"""
System tray indicator for Claude Code usage overlay.

Displays usage data via:
- System tray icon with color-coded gauge (green/yellow/orange/red)
- Panel label showing compact status (e.g., "45%|67%")
- Dropdown menu with detailed usage info and reset times

Note: Hover tooltips don't work on GNOME Shell due to AppIndicator limitations.
See KNOWN_ISSUES.md for details.
"""
import gi

gi.require_version('AyatanaAppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
from gi.repository import AyatanaAppIndicator3 as AppIndicator3, Gtk, GLib
import sys

from src.icon_generator import generate_gauge_icon
from src.utils import format_time_until
from src.config import get_access_token, UserConfig, get_config_path
from src.api import fetch_with_retry, APIError, AuthenticationError
from src.notifier import UsageNotifier
from src.autostart import create_autostart_entry, is_autostart_enabled, remove_autostart_entry


class TrayIndicator:
    """System tray indicator for Claude Code usage."""

    APPINDICATOR_ID = 'claude-usage-overlay'

    def __init__(self):
        """Initialize the tray indicator."""
        self.usage_data = None
        self.indicator = None
        self.menu = None
        self.timer_id = None

        # Load configuration
        self.config = UserConfig.load()

        # Initialize notifier with both threshold lists
        self.notifier = UsageNotifier(
            session_thresholds=self.config.session_thresholds,
            weekly_thresholds=self.config.weekly_thresholds
        )

        self._setup_indicator()
        self._update_usage()

        # Start periodic updates with config interval
        self._start_update_timer()

    def _setup_indicator(self):
        """Set up the AppIndicator with initial icon and menu."""
        # Create initial icon at 0% fill with green color (both 0%)
        initial_icon = generate_gauge_icon(0, 0)

        # Create AppIndicator
        self.indicator = AppIndicator3.Indicator.new(
            self.APPINDICATOR_ID,
            initial_icon,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Build initial menu with loading message
        menu = Gtk.Menu()
        loading_item = Gtk.MenuItem(label="Loading...")
        loading_item.set_sensitive(False)
        menu.append(loading_item)
        menu.show_all()

        self.menu = menu
        self.indicator.set_menu(menu)

    def _update_usage(self) -> bool:
        """Fetch usage data and refresh display.

        Returns:
            bool: GLib.SOURCE_CONTINUE to keep timer running
        """
        try:
            token = get_access_token()
            self.usage_data = fetch_with_retry(token)
            self._refresh_display()

        except AuthenticationError as e:
            error_msg = f"Authentication failed: {e}"
            print(error_msg, file=sys.stderr)
            self.indicator.set_title(error_msg)

        except (APIError, ValueError, FileNotFoundError) as e:
            error_msg = f"Error: {e}"
            print(error_msg, file=sys.stderr)
            self.indicator.set_title(error_msg)

        # Return GLib.SOURCE_CONTINUE to keep timer running
        return GLib.SOURCE_CONTINUE

    def _start_update_timer(self):
        """Start or restart periodic update timer with config interval."""
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)
        self.timer_id = GLib.timeout_add_seconds(
            self.config.polling_interval,
            self._update_usage
        )

    def _refresh_display(self):
        """Update icon, tooltip, and menu based on current usage data."""
        if self.usage_data is None:
            return

        session_percent = self.usage_data.session_percent
        weekly_percent = self.usage_data.weekly_percent

        # Arc fill shows session usage only (5-hour window)
        # Color shows worst-case urgency (max of session and weekly)
        worst_case_percent = max(session_percent, weekly_percent)

        # Generate icon with separate percentage (arc fill) and color
        icon_path = generate_gauge_icon(session_percent, worst_case_percent)
        self.indicator.set_icon_full(icon_path, 'Claude usage gauge')

        # Update accessibility label (for screen readers, not displayed as tooltip on GNOME)
        tooltip = f"Session: {session_percent:.0f}% | Weekly: {weekly_percent:.0f}%"
        self.indicator.set_title(tooltip)

        # Display compact status in panel (next to icon)
        # Note: AppIndicator on GNOME Shell doesn't show hover tooltips (known limitation).
        # This label appears as text in the panel for quick visual reference.
        compact_label = f"{session_percent:.0f}%|{weekly_percent:.0f}%"
        self.indicator.set_label(compact_label, "100%|100%")  # guide string for sizing

        # Rebuild menu with current data
        self._build_menu()

        # Pass pause flag to notifier before check_and_notify
        self.notifier.pause_notifications = self.config.pause_notifications

        # Check thresholds and show notifications if needed
        # Convert datetime to timestamp for notifier
        session_reset_ts = (self.usage_data.session_resets_at.timestamp()
                            if self.usage_data.session_resets_at else 0)
        weekly_reset_ts = (self.usage_data.weekly_resets_at.timestamp()
                           if self.usage_data.weekly_resets_at else 0)

        self.notifier.check_and_notify(
            session_percent,
            weekly_percent,
            session_reset_ts,
            weekly_reset_ts
        )

    def _build_menu(self) -> Gtk.Menu:
        """Build the dropdown menu with usage info and actions.

        Returns:
            Gtk.Menu: The constructed menu
        """
        menu = Gtk.Menu()

        # Add usage line (non-clickable)
        session_percent = self.usage_data.session_percent
        weekly_percent = self.usage_data.weekly_percent
        usage_text = f"Session: {session_percent:.0f}%  |  Weekly: {weekly_percent:.0f}%"
        usage_item = Gtk.MenuItem(label=usage_text)
        usage_item.set_sensitive(False)
        menu.append(usage_item)

        # Add reset time line (non-clickable)
        # Use session_resets_at (5-hour is more relevant for active users)
        reset_time_str = format_time_until(self.usage_data.session_resets_at)
        reset_item = Gtk.MenuItem(label=f"Resets in {reset_time_str}")
        reset_item.set_sensitive(False)
        menu.append(reset_item)

        # Add separator
        menu.append(Gtk.SeparatorMenuItem())

        # Add Refresh item
        # Note: AppIndicator menus don't support GTK accelerators (no window to attach AccelGroup)
        # Show the shortcut hint in the label instead
        refresh_item = Gtk.MenuItem(label="Refresh")
        refresh_item.connect('activate', self._on_refresh_clicked)
        menu.append(refresh_item)

        # Add Settings submenu
        settings_item = Gtk.MenuItem(label="Settings")
        settings_submenu = Gtk.Menu()

        # Pause Notifications checkbox
        pause_item = Gtk.CheckMenuItem(label="Pause Notifications")
        pause_item.set_active(self.config.pause_notifications)
        pause_item.connect('activate', self._on_pause_toggled)
        settings_submenu.append(pause_item)

        # Autostart on Login checkbox
        autostart_item = Gtk.CheckMenuItem(label="Autostart on Login")
        autostart_item.set_active(is_autostart_enabled())
        autostart_item.connect('activate', self._on_autostart_toggled)
        settings_submenu.append(autostart_item)

        # Separator
        settings_submenu.append(Gtk.SeparatorMenuItem())

        # Edit Config File item
        edit_config_item = Gtk.MenuItem(label="Edit Config File...")
        edit_config_item.connect('activate', self._on_edit_config_clicked)
        settings_submenu.append(edit_config_item)

        settings_item.set_submenu(settings_submenu)
        menu.append(settings_item)

        # Add separator
        menu.append(Gtk.SeparatorMenuItem())

        # Add Quit item
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect('activate', self._on_quit_clicked)
        menu.append(quit_item)

        # Show all menu items
        menu.show_all()

        # Update instance menu and indicator
        self.menu = menu
        self.indicator.set_menu(menu)

        return menu

    def _on_refresh_clicked(self, widget):
        """Handle Refresh menu item click.

        Uses GLib.idle_add to defer the update until after the menu closes,
        avoiding GTK crashes from rebuilding the menu during event handling.
        """
        GLib.idle_add(self._update_usage)

    def _on_pause_toggled(self, widget):
        """Handle Pause Notifications toggle."""
        self.config.pause_notifications = widget.get_active()
        self.config.save()
        self.notifier.pause_notifications = self.config.pause_notifications

    def _on_autostart_toggled(self, widget):
        """Handle Autostart toggle."""
        if widget.get_active():
            create_autostart_entry(True)
        else:
            remove_autostart_entry()
        self.config.autostart_enabled = widget.get_active()
        self.config.save()

    def _on_edit_config_clicked(self, widget):
        """Open config file in default editor."""
        import subprocess
        config_path = get_config_path()
        # Ensure file exists with defaults
        if not config_path.exists():
            self.config.save()
        subprocess.Popen(["/usr/bin/xdg-open", str(config_path)])

    def _on_quit_clicked(self, widget):
        """Handle Quit menu item click."""
        Gtk.main_quit()

    def run(self):
        """Start the GTK main loop."""
        Gtk.main()

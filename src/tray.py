"""
System tray indicator for Claude Code usage overlay.

Displays usage data via system tray icon, menu, and tooltip.
"""
import gi

gi.require_version('AyatanaAppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
from gi.repository import AyatanaAppIndicator3 as AppIndicator3, Gtk, GLib
import sys

from src.icon_generator import generate_gauge_icon
from src.utils import format_time_until
from src.config import get_access_token
from src.api import fetch_with_retry, APIError, AuthenticationError


class TrayIndicator:
    """System tray indicator for Claude Code usage."""

    APPINDICATOR_ID = 'claude-usage-overlay'

    def __init__(self):
        """Initialize the tray indicator."""
        self.usage_data = None
        self.indicator = None
        self.menu = None

        self._setup_indicator()
        self._update_usage()

        # Start periodic updates every 5 minutes
        GLib.timeout_add_seconds(300, self._update_usage)

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

        # Update tooltip with both metrics
        tooltip = f"Session: {session_percent:.0f}% | Weekly: {weekly_percent:.0f}%"
        self.indicator.set_title(tooltip)

        # Rebuild menu with current data
        self._build_menu()

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
        refresh_item = Gtk.MenuItem(label="Refresh")
        refresh_item.connect('activate', self._on_refresh_clicked)
        menu.append(refresh_item)

        # Add Settings item (placeholder for Phase 4)
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.set_sensitive(False)
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
        """Handle Refresh menu item click."""
        self._update_usage()

    def _on_quit_clicked(self, widget):
        """Handle Quit menu item click."""
        Gtk.main_quit()

    def run(self):
        """Start the GTK main loop."""
        Gtk.main()

"""
System tray indicator for Claude Code usage overlay.

Cross-platform: uses pystray for Windows, macOS, and Linux.

Displays usage data via:
- System tray icon with color-coded gauge (green/yellow/red)
- Tooltip showing compact status (e.g., "Session: 45% | Weekly: 67%")
- Dropdown menu with detailed usage info and reset times

Note: Panel labels (text next to icon) are not supported by pystray.
Tooltip is used instead for quick status display.
"""
import sys
import threading
import webbrowser
from typing import Optional

import pystray

from src.icon_generator import generate_gauge_icon
from src.utils import format_time_until
from src.config import get_access_token, UserConfig, get_config_path
from src.api import fetch_with_retry, APIError, AuthenticationError, UsageData
from src.notifier import UsageNotifier
from src.autostart import create_autostart_entry, is_autostart_enabled, remove_autostart_entry


class TrayIndicator:
    """System tray indicator for Claude Code usage."""

    def __init__(self):
        """Initialize the tray indicator."""
        self.usage_data: Optional[UsageData] = None
        self.icon: Optional[pystray.Icon] = None
        self._stop_event = threading.Event()
        self._update_thread: Optional[threading.Thread] = None

        # Load configuration
        self.config = UserConfig.load()

        # Initialize notifier with both threshold lists
        self.notifier = UsageNotifier(
            session_thresholds=self.config.session_thresholds,
            weekly_thresholds=self.config.weekly_thresholds
        )

        self._setup_indicator()

    def _setup_indicator(self):
        """Set up the pystray icon with initial state."""
        # Create initial icon at 0% fill with green color
        initial_icon = generate_gauge_icon(0, 0)

        # Create pystray Icon
        self.icon = pystray.Icon(
            name="claude-usage-overlay",
            icon=initial_icon,
            title="Claude Usage: Loading...",
            menu=self._build_menu()
        )

    def _build_menu(self) -> pystray.Menu:
        """Build the dropdown menu with usage info and actions.

        Returns:
            pystray.Menu: The constructed menu
        """
        # Usage line (shows current percentages or loading state)
        if self.usage_data is not None:
            session_percent = self.usage_data.session_percent
            weekly_percent = self.usage_data.weekly_percent
            usage_text = f"Session: {session_percent:.0f}%  |  Weekly: {weekly_percent:.0f}%"
            reset_time_str = format_time_until(self.usage_data.session_resets_at)
            reset_text = f"Resets in {reset_time_str}"
        else:
            usage_text = "Loading..."
            reset_text = ""

        menu_items = [
            pystray.MenuItem(usage_text, None, enabled=False),
        ]

        if reset_text:
            menu_items.append(pystray.MenuItem(reset_text, None, enabled=False))

        menu_items.extend([
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Refresh", self._on_refresh_clicked),
            pystray.MenuItem(
                "Settings",
                pystray.Menu(
                    pystray.MenuItem(
                        "Pause Notifications",
                        self._on_pause_toggled,
                        checked=lambda item: self.config.pause_notifications
                    ),
                    pystray.MenuItem(
                        "Autostart on Login",
                        self._on_autostart_toggled,
                        checked=lambda item: is_autostart_enabled()
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Edit Config File...", self._on_edit_config_clicked),
                )
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit_clicked),
        ])

        return pystray.Menu(*menu_items)

    def _update_usage(self):
        """Fetch usage data and refresh display."""
        try:
            token = get_access_token()
            self.usage_data = fetch_with_retry(token)
            self._refresh_display()

        except AuthenticationError as e:
            error_msg = f"Authentication failed: {e}"
            print(error_msg, file=sys.stderr)
            if self.icon:
                self.icon.title = error_msg

        except (APIError, ValueError, FileNotFoundError) as e:
            error_msg = f"Error: {e}"
            print(error_msg, file=sys.stderr)
            if self.icon:
                self.icon.title = error_msg

    def _refresh_display(self):
        """Update icon, tooltip, and menu based on current usage data."""
        if self.usage_data is None or self.icon is None:
            return

        session_percent = self.usage_data.session_percent
        weekly_percent = self.usage_data.weekly_percent

        # Arc fill shows session usage only (5-hour window)
        # Color shows worst-case urgency (max of session and weekly)
        worst_case_percent = max(session_percent, weekly_percent)

        # Generate new icon image
        new_icon = generate_gauge_icon(session_percent, worst_case_percent)
        self.icon.icon = new_icon

        # Update tooltip (shown on hover)
        tooltip = f"Session: {session_percent:.0f}% | Weekly: {weekly_percent:.0f}%"
        self.icon.title = tooltip

        # Rebuild menu with current data
        self.icon.menu = self._build_menu()

        # Pass pause flag to notifier before check_and_notify
        self.notifier.pause_notifications = self.config.pause_notifications

        # Check thresholds and show notifications if needed
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

    def _update_loop(self):
        """Background thread that periodically updates usage data."""
        # Initial update
        self._update_usage()

        # Periodic updates
        while not self._stop_event.wait(timeout=self.config.polling_interval):
            self._update_usage()

    def _on_refresh_clicked(self, icon=None, item=None):
        """Handle Refresh menu item click."""
        # Run update in background thread to avoid blocking UI
        threading.Thread(target=self._update_usage, daemon=True).start()

    def _on_pause_toggled(self, icon=None, item=None):
        """Handle Pause Notifications toggle."""
        self.config.pause_notifications = not self.config.pause_notifications
        self.config.save()
        self.notifier.pause_notifications = self.config.pause_notifications

    def _on_autostart_toggled(self, icon=None, item=None):
        """Handle Autostart toggle."""
        if is_autostart_enabled():
            remove_autostart_entry()
            self.config.autostart_enabled = False
        else:
            create_autostart_entry(True)
            self.config.autostart_enabled = True
        self.config.save()

    def _on_edit_config_clicked(self, icon=None, item=None):
        """Open config file in default editor/viewer."""
        config_path = get_config_path()
        # Ensure file exists with defaults
        if not config_path.exists():
            self.config.save()

        # Use webbrowser for cross-platform file opening
        # This works on Windows, macOS, and Linux
        webbrowser.open(str(config_path))

    def _on_quit_clicked(self, icon=None, item=None):
        """Handle Quit menu item click."""
        self._stop_event.set()
        if self.icon:
            self.icon.stop()

    def run(self):
        """Start the tray indicator."""
        # Start background update thread
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()

        # Run pystray main loop (blocks until icon.stop() is called)
        self.icon.run()

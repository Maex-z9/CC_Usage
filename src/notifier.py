"""Desktop notification manager for usage threshold alerts."""

import subprocess
import time

import gi

gi.require_version('Notify', '0.7')
from gi.repository import Notify


class UsageNotifier:
    """Manages threshold-based usage notifications.

    Displays popup notifications when session or weekly usage crosses
    thresholds (50%, 75%, 90%) with escalating urgency and advice.
    Tracks alerted thresholds to prevent notification spam.
    """

    THRESHOLDS = [50, 75, 90]

    def __init__(self, app_name="Claude Code Usage Monitor"):
        """Initialize the notifier.

        Args:
            app_name: Name shown in notification server
        """
        # Initialize libnotify once
        Notify.init(app_name)

        # Track alerted thresholds: {(metric, threshold): True}
        # metric = 'session' or 'weekly'
        # threshold = 50, 75, or 90
        self.alerted = {}

        # Grace period flag - skip first poll to avoid startup spam
        self.first_poll = True

        # Cache server capabilities
        self._actions_supported = None

    def check_and_notify(self, session_pct, weekly_pct, session_reset, weekly_reset):
        """Check thresholds and show notifications if needed.

        Main entry point called by TrayIndicator after each usage update.

        Args:
            session_pct: Session usage percentage (0-100)
            weekly_pct: Weekly usage percentage (0-100)
            session_reset: Unix timestamp when session resets
            weekly_reset: Unix timestamp when weekly resets
        """
        # Skip first poll (grace period)
        if self.first_poll:
            self.first_poll = False
            return

        # Find highest threshold crossed for each metric
        session_threshold = self._highest_crossed(session_pct, self.THRESHOLDS)
        weekly_threshold = self._highest_crossed(weekly_pct, self.THRESHOLDS)

        # Determine if we should alert
        session_needs_alert = (
            session_threshold and
            ('session', session_threshold) not in self.alerted
        )
        weekly_needs_alert = (
            weekly_threshold and
            ('weekly', weekly_threshold) not in self.alerted
        )

        # Handle combined case first (both need alerts)
        if session_needs_alert and weekly_needs_alert:
            if session_threshold == weekly_threshold:
                # Same threshold - use that urgency
                self._show_combined_notification(
                    session_threshold, session_pct, weekly_pct,
                    session_reset, weekly_reset
                )
            else:
                # Different thresholds - use highest urgency
                max_threshold = max(session_threshold, weekly_threshold)
                self._show_combined_notification(
                    max_threshold, session_pct, weekly_pct,
                    session_reset, weekly_reset
                )
            # Mark both as alerted
            self.alerted[('session', session_threshold)] = True
            self.alerted[('weekly', weekly_threshold)] = True

        # Individual alerts
        elif session_needs_alert:
            self._show_notification(
                'session', session_pct, session_threshold, session_reset
            )
            self.alerted[('session', session_threshold)] = True

        elif weekly_needs_alert:
            self._show_notification(
                'weekly', weekly_pct, weekly_threshold, weekly_reset
            )
            self.alerted[('weekly', weekly_threshold)] = True

    def _highest_crossed(self, percentage, thresholds):
        """Return highest threshold crossed, or None.

        Args:
            percentage: Current usage percentage (0-100)
            thresholds: List of threshold values to check

        Returns:
            int: Highest crossed threshold, or None if no thresholds crossed
        """
        crossed = [t for t in thresholds if percentage >= t]
        return max(crossed) if crossed else None

    def _show_notification(self, metric, percentage, threshold, reset_time):
        """Show notification for single metric threshold.

        Args:
            metric: 'session' or 'weekly'
            percentage: Current usage percentage (0-100)
            threshold: Threshold that was crossed (50, 75, or 90)
            reset_time: Unix timestamp when metric resets
        """
        # Map threshold to urgency and advice
        urgency_map = {
            50: (Notify.Urgency.LOW, "Heads up"),
            75: (Notify.Urgency.NORMAL, "Consider saving your work"),
            90: (Notify.Urgency.CRITICAL, "Save your work now")
        }

        urgency, advice = urgency_map[threshold]

        # Format title
        metric_name = "Session Usage" if metric == 'session' else "Weekly Usage"
        title = f"{metric_name}: {percentage:.0f}%"

        # Format body with reset time
        reset_str = self._format_reset_time(reset_time)
        body = f"{advice}\n\nResets in {reset_str}"

        # Create notification
        notification = Notify.Notification.new(
            title,
            body,
            "dialog-information"
        )

        # Set urgency level
        notification.set_urgency(urgency)

        # Add action button if server supports it
        if self._server_supports_actions():
            notification.add_action(
                "open-claude",
                "Open Claude Code",
                self._on_open_claude,
                None
            )

        # Show notification
        notification.show()

    def _show_combined_notification(self, threshold, session_pct, weekly_pct,
                                    session_reset, weekly_reset):
        """Show combined notification for both metrics.

        Args:
            threshold: Threshold to use for urgency (highest of both)
            session_pct: Session usage percentage (0-100)
            weekly_pct: Weekly usage percentage (0-100)
            session_reset: Unix timestamp when session resets
            weekly_reset: Unix timestamp when weekly resets
        """
        # Map threshold to urgency and advice
        urgency_map = {
            50: (Notify.Urgency.LOW, "Heads up"),
            75: (Notify.Urgency.NORMAL, "Consider saving your work"),
            90: (Notify.Urgency.CRITICAL, "Save your work now")
        }

        urgency, advice = urgency_map[threshold]

        # Format title (show threshold, not individual percentages)
        title = f"Session & Weekly Usage: {threshold}%"

        # Format body with both reset times
        session_reset_str = self._format_reset_time(session_reset)
        weekly_reset_str = self._format_reset_time(weekly_reset)
        body = (f"{advice}\n\n"
                f"Session resets in {session_reset_str}\n"
                f"Weekly resets in {weekly_reset_str}")

        # Create notification
        notification = Notify.Notification.new(
            title,
            body,
            "dialog-information"
        )

        # Set urgency level
        notification.set_urgency(urgency)

        # Add action button if server supports it
        if self._server_supports_actions():
            notification.add_action(
                "open-claude",
                "Open Claude Code",
                self._on_open_claude,
                None
            )

        # Show notification
        notification.show()

    def _format_reset_time(self, reset_timestamp):
        """Format Unix timestamp to human-readable time until reset.

        Args:
            reset_timestamp: Unix timestamp (seconds since epoch)

        Returns:
            str: Human-readable time string (e.g., "2h", "3d", "45m")
        """
        now = time.time()
        seconds = int(reset_timestamp - now)

        if seconds <= 0:
            return "shortly"

        # Convert to hours and days using divmod
        hours, remainder = divmod(seconds, 3600)
        days, hours = divmod(hours, 24)

        if days > 0:
            return f"{days}d"
        elif hours > 0:
            return f"{hours}h"
        else:
            minutes = remainder // 60
            return f"{minutes}m" if minutes > 0 else "shortly"

    def _server_supports_actions(self):
        """Check if notification server supports action buttons.

        Returns:
            bool: True if server supports actions, False otherwise
        """
        if self._actions_supported is None:
            caps = Notify.get_server_caps()
            self._actions_supported = caps and 'actions' in caps
        return self._actions_supported

    def _on_open_claude(self, notification, action, user_data):
        """Callback when 'Open Claude Code' button is clicked.

        Args:
            notification: The notification that triggered the action
            action: Action identifier string
            user_data: User data passed to add_action (unused)
        """
        # Close the notification
        notification.close()

        # Open Claude Code in browser
        subprocess.Popen(["/usr/bin/xdg-open", "https://claude.ai"])

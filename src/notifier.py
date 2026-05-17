"""Desktop notification manager for usage threshold alerts.

Cross-platform: uses desktop-notifier for Windows, macOS, and Linux.
"""

import asyncio
import sys
import time
import webbrowser
from typing import Optional

from desktop_notifier import DesktopNotifier, Urgency, Button


class UsageNotifier:
    """Manages threshold-based usage notifications.

    Displays popup notifications when session or weekly usage crosses
    thresholds (50%, 75%, 90%) with escalating urgency and advice.
    Tracks alerted thresholds to prevent notification spam.
    """

    def __init__(self, app_name="Claude Code Usage Monitor",
                 session_thresholds=None, weekly_thresholds=None):
        """Initialize the notifier.

        Args:
            app_name: Name shown in notification server
            session_thresholds: List of threshold percentages for session (default [50, 75, 90])
            weekly_thresholds: List of threshold percentages for weekly (default to session_thresholds)
        """
        self.app_name = app_name
        self.notifier = None
        self._notifier_init_attempted = False

        # Configure thresholds
        self.session_thresholds = session_thresholds if session_thresholds is not None else [50, 75, 90]
        self.weekly_thresholds = weekly_thresholds if weekly_thresholds is not None else self.session_thresholds

        # Track alerted thresholds: {(metric, threshold): True}
        # metric = 'session' or 'weekly'
        # threshold = 50, 75, or 90
        self.alerted = {}

        # Grace period flag - skip first poll to avoid startup spam
        self.first_poll = True

        # Pause notifications mode
        self.pause_notifications = False

        # Event loop for async operations
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for async operations."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create new one
                self._loop = asyncio.new_event_loop()
        return self._loop

    def _run_async(self, coro):
        """Run async coroutine synchronously."""
        loop = self._get_event_loop()
        try:
            # Try to run in existing loop
            if loop.is_running():
                # Schedule in running loop (won't block)
                asyncio.ensure_future(coro, loop=loop)
            else:
                loop.run_until_complete(coro)
        except RuntimeError:
            # Fallback: create new loop
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(coro)
            finally:
                new_loop.close()

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

        # Respect pause mode
        if self.pause_notifications:
            return

        # Find highest threshold crossed for each metric
        session_threshold = self._highest_crossed(session_pct, self.session_thresholds)
        weekly_threshold = self._highest_crossed(weekly_pct, self.weekly_thresholds)

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

    def _get_urgency(self, threshold: int) -> Urgency:
        """Map threshold to desktop-notifier Urgency level.

        Args:
            threshold: Threshold percentage (50, 75, or 90)

        Returns:
            Urgency enum value
        """
        if threshold >= 90:
            return Urgency.Critical
        elif threshold >= 75:
            return Urgency.Normal
        else:
            return Urgency.Low

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
            50: "Heads up",
            75: "Consider saving your work",
            90: "Save your work now"
        }

        advice = urgency_map[threshold]
        urgency = self._get_urgency(threshold)

        # Format title
        metric_name = "Session Usage" if metric == 'session' else "Weekly Usage"
        title = f"{metric_name}: {percentage:.0f}%"

        # Format body with reset time
        reset_str = self._format_reset_time(reset_time)
        body = f"{advice}\n\nResets in {reset_str}"

        # Show notification asynchronously
        self._run_async(self._send_notification(title, body, urgency))

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
            50: "Heads up",
            75: "Consider saving your work",
            90: "Save your work now"
        }

        advice = urgency_map[threshold]
        urgency = self._get_urgency(threshold)

        # Format title (show threshold, not individual percentages)
        title = f"Session & Weekly Usage: {threshold}%"

        # Format body with both reset times
        session_reset_str = self._format_reset_time(session_reset)
        weekly_reset_str = self._format_reset_time(weekly_reset)
        body = (f"{advice}\n\n"
                f"Session resets in {session_reset_str}\n"
                f"Weekly resets in {weekly_reset_str}")

        # Show notification asynchronously
        self._run_async(self._send_notification(title, body, urgency))

    async def _send_notification(self, title: str, body: str, urgency: Urgency):
        """Send notification via desktop-notifier.

        Args:
            title: Notification title
            body: Notification body text
            urgency: Urgency level
        """
        if not self._notifier_init_attempted:
            self._notifier_init_attempted = True
            try:
                self.notifier = DesktopNotifier(
                    app_name=self.app_name,
                    notification_limit=10
                )
            except Exception as e:
                print(f"Warning: Failed to initialize desktop notifications: {e}", file=sys.stderr)
                self.notifier = None

        if self.notifier is None:
            return

        try:
            await self.notifier.send(
                title=title,
                message=body,
                urgency=urgency,
                buttons=[
                    Button(
                        title="Open Claude",
                        on_pressed=lambda: webbrowser.open("https://claude.ai")
                    )
                ]
            )
        except Exception as e:
            # Log but don't crash on notification failure
            print(f"Notification error: {e}", file=sys.stderr)

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

    def set_thresholds(self, session_thresholds, weekly_thresholds=None):
        """Update threshold configuration.

        Args:
            session_thresholds: List of session threshold percentages
            weekly_thresholds: List of weekly threshold percentages (defaults to session)
        """
        self.session_thresholds = session_thresholds
        self.weekly_thresholds = weekly_thresholds if weekly_thresholds is not None else session_thresholds

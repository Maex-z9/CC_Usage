# Phase 3: Alerts - Research

**Researched:** 2026-02-04
**Domain:** Desktop notifications with libnotify/PyGObject
**Confidence:** HIGH

## Summary

Desktop notifications in Python GTK applications are implemented using libnotify through PyGObject (gi.repository.Notify). The library provides a simple API: initialize once with `Notify.init()`, create notifications with `Notify.Notification.new()`, configure urgency/actions, and display with `show()`.

The standard approach is to track alerted thresholds in application state (using a dictionary or set) to prevent notification spam, set urgency levels (LOW=0, NORMAL=1, CRITICAL=2) to control visual prominence and timeout behavior, and optionally add action buttons if the notification server supports them (verify with `Notify.get_server_caps()`).

Critical notifications often bypass timeout settings and require explicit dismissal. Action button support varies by notification server - GNOME Shell supports them, but some servers like notify-osd do not. Always check server capabilities before adding actions to avoid compatibility issues.

**Primary recommendation:** Use libnotify with PyGObject, track alerted state in a dictionary keyed by (metric, threshold), format reset times with divmod() for hours/days, and check server capabilities before adding action buttons.

## Standard Stack

The established libraries/tools for desktop notifications in Python GTK applications:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| libnotify | 0.7+ | Desktop notifications via D-Bus | Official GNOME notification API, freedesktop.org standard |
| PyGObject (gi.repository.Notify) | 3.0+ | Python bindings for libnotify | Official Python bindings for GNOME libraries |
| GLib | 2.0+ | Main loop and timer integration | Required for GTK applications, provides thread-safe callbacks |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| humanize | 4.0+ | Format timedelta to readable strings | Optional - only if complex time formatting needed beyond hours/days |
| subprocess | stdlib | Open URLs with xdg-open | For "Open Claude Code" action button |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| libnotify (gi.repository.Notify) | notify2 | notify2 is older pynotify-compatible library, less maintained, doesn't support modern PyGObject patterns |
| libnotify | desktop-notifier, notify-py | Cross-platform but adds dependencies, no urgency control, limited action support |
| Manual time formatting (divmod) | humanize library | Humanize adds dependency for simple use case, manual approach has zero deps |

**Installation:**
```bash
# System packages (required)
sudo apt install libnotify-dev gir1.2-notify-0.7

# Python packages (if using humanize)
pip install humanize
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── notifier.py          # Notification logic and state tracking
├── indicator.py         # Tray indicator with polling
└── main.py              # Application entry point
```

### Pattern 1: Notification State Tracking

**What:** Track which thresholds have been alerted for each metric to prevent re-notification spam.

**When to use:** Always - essential for any threshold-based notification system.

**Example:**
```python
# Source: Best practices from research synthesis
class UsageNotifier:
    def __init__(self):
        # Initialize libnotify once at startup
        Notify.init("Claude Code Usage Monitor")

        # Track alerted thresholds: {(metric, threshold): True}
        # metric = 'session' or 'weekly'
        # threshold = 50, 75, or 90
        self.alerted = {}

        # Grace period: skip alerts for first poll
        self.first_poll = True

    def check_and_notify(self, session_pct, weekly_pct, session_reset, weekly_reset):
        """Check thresholds and show notifications if needed."""
        if self.first_poll:
            self.first_poll = False
            return

        thresholds = [50, 75, 90]

        # Find highest threshold crossed for each metric
        session_threshold = self._highest_crossed(session_pct, thresholds)
        weekly_threshold = self._highest_crossed(weekly_pct, thresholds)

        # Determine if we should alert
        session_needs_alert = (session_threshold and
                              ('session', session_threshold) not in self.alerted)
        weekly_needs_alert = (weekly_threshold and
                             ('weekly', weekly_threshold) not in self.alerted)

        if session_needs_alert and weekly_needs_alert and session_threshold == weekly_threshold:
            # Combined alert - same threshold
            self._show_combined_notification(session_threshold, session_reset, weekly_reset)
            self.alerted[('session', session_threshold)] = True
            self.alerted[('weekly', weekly_threshold)] = True
        elif session_needs_alert and weekly_needs_alert:
            # Combined alert - different thresholds
            max_threshold = max(session_threshold, weekly_threshold)
            self._show_combined_notification(max_threshold, session_reset, weekly_reset)
            self.alerted[('session', session_threshold)] = True
            self.alerted[('weekly', weekly_threshold)] = True
        elif session_needs_alert:
            self._show_notification('session', session_pct, session_threshold, session_reset)
            self.alerted[('session', session_threshold)] = True
        elif weekly_needs_alert:
            self._show_notification('weekly', weekly_pct, weekly_threshold, weekly_reset)
            self.alerted[('weekly', weekly_threshold)] = True

    def _highest_crossed(self, percentage, thresholds):
        """Return highest threshold crossed, or None."""
        crossed = [t for t in thresholds if percentage >= t]
        return max(crossed) if crossed else None
```

### Pattern 2: Urgency-Based Notification Creation

**What:** Map threshold levels to libnotify urgency levels with appropriate messaging.

**When to use:** For any multi-level alert system where severity matters.

**Example:**
```python
# Source: Synthesized from libnotify documentation and UX best practices
def _show_notification(self, metric, percentage, threshold, reset_time):
    """Show notification for single metric threshold."""
    # Map threshold to urgency and message
    urgency_map = {
        50: (Notify.Urgency.LOW, "Heads up"),
        75: (Notify.Urgency.NORMAL, "Consider saving your work"),
        90: (Notify.Urgency.CRITICAL, "Save your work now")
    }

    urgency, advice = urgency_map[threshold]

    # Format title
    metric_name = "Session Usage" if metric == 'session' else "Weekly Usage"
    title = f"{metric_name}: {percentage}%"

    # Format body with reset time
    reset_str = self._format_reset_time(reset_time)
    body = f"{advice}\n\nResets in {reset_str}"

    # Create notification
    notification = Notify.Notification.new(
        title,
        body,
        "dialog-information"  # or custom icon path
    )

    # Set urgency level
    notification.set_urgency(urgency)

    # Add action button if supported
    if self._server_supports_actions():
        notification.add_action(
            "open-claude",
            "Open Claude Code",
            self._on_open_claude,
            None
        )

    # Show notification
    notification.show()
```

### Pattern 3: Server Capability Detection

**What:** Check notification server capabilities before adding actions to avoid unsupported features.

**When to use:** Before adding action buttons to notifications.

**Example:**
```python
# Source: https://github.com/phuhl/notify-send.py, libnotify documentation
def _server_supports_actions(self):
    """Check if notification server supports action buttons."""
    caps = Notify.get_server_caps()
    return caps and 'actions' in caps
```

### Pattern 4: Time Formatting Without Dependencies

**What:** Format seconds to human-readable "Xh" or "Xd" format using divmod.

**When to use:** For simple time formatting without adding humanize dependency.

**Example:**
```python
# Source: https://www.geeksforgeeks.org/python/python-program-to-convert-seconds-into-hours-minutes-and-seconds/
def _format_reset_time(self, reset_timestamp):
    """Format Unix timestamp to human-readable time until reset."""
    now = time.time()
    seconds = int(reset_timestamp - now)

    if seconds < 0:
        return "shortly"

    # Convert to hours and days
    hours, remainder = divmod(seconds, 3600)
    days, hours = divmod(hours, 24)

    if days > 0:
        return f"{days}d"
    elif hours > 0:
        return f"{hours}h"
    else:
        minutes = remainder // 60
        return f"{minutes}m" if minutes > 0 else "shortly"
```

### Pattern 5: Action Button Callback

**What:** Handle notification action button clicks to open external application.

**When to use:** When adding interactive buttons to notifications.

**Example:**
```python
# Source: https://lazka.github.io/pgi-docs/Notify-0.7/classes/Notification.html
def _on_open_claude(self, notification, action, user_data):
    """Callback when 'Open Claude Code' button is clicked."""
    # Close the notification
    notification.close()

    # Open Claude Code (example - adjust URL/command as needed)
    import subprocess
    subprocess.Popen(["xdg-open", "https://claude.ai"])
```

### Anti-Patterns to Avoid

- **Re-alerting same threshold:** Never clear alerted state during app runtime - only reset on restart. Clearing leads to notification spam.
- **Alerting on first poll:** Always skip first check after startup - the user just launched the app and knows the current state.
- **Ignoring server capabilities:** Adding action buttons without checking server support causes silent failures on some systems.
- **Setting EXPIRES_NEVER without CRITICAL urgency:** Timeout settings are often ignored by notification servers; use CRITICAL urgency for persistence.
- **Threading GTK calls from callbacks:** Notification callbacks run in main loop - never spawn threads that call GTK/libnotify directly. Use GLib.idle_add() if needed.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Desktop notifications | Custom D-Bus interface | libnotify via gi.repository.Notify | D-Bus notification spec is complex, server capability detection is tricky, libnotify handles it all |
| Time formatting | String manipulation | divmod() for simple cases, humanize library for complex | Edge cases (plural forms, negative times, timezones) are harder than they look |
| Opening URLs | os.system() | subprocess.Popen(["/usr/bin/xdg-open", url]) | Security (shell injection), cross-desktop compatibility |
| Threshold tracking | List comparisons on every check | Dictionary of alerted state | O(1) lookups vs O(n), prevents logic errors |

**Key insight:** Desktop notifications are a standardized D-Bus interface with many edge cases around server capabilities, threading, and timeout behavior. libnotify abstracts all of this correctly.

## Common Pitfalls

### Pitfall 1: Notification Action Buttons Not Appearing

**What goes wrong:** Action buttons added to notifications don't appear on user's system.

**Why it happens:** Not all notification servers support action buttons. Notably, notify-osd (used in some Ubuntu configurations) does not support actions at all. GNOME Shell supports them, but they must be explicitly checked.

**How to avoid:**
```python
def _server_supports_actions(self):
    caps = Notify.get_server_caps()
    return caps and 'actions' in caps

# Always check before adding actions
if self._server_supports_actions():
    notification.add_action("id", "Label", callback, None)
```

**Warning signs:** Users report "I never see the Open button" - different notification servers on different systems.

### Pitfall 2: Notification Spam on App Restart

**What goes wrong:** User restarts app, immediately sees notifications for thresholds they already know about.

**Why it happens:** Not implementing grace period - checking thresholds before first API fetch completes, or immediately on first poll.

**How to avoid:**
```python
def __init__(self):
    self.first_poll = True

def check_and_notify(self, ...):
    if self.first_poll:
        self.first_poll = False
        return  # Skip notifications on first check
```

**Warning signs:** User feedback "app is too noisy on startup", notifications appearing immediately when app launches.

### Pitfall 3: Threading Violations with Notification Callbacks

**What goes wrong:** Crashes or "X11: Fatal IO error" when notification action button is clicked.

**Why it happens:** Notification callbacks are invoked in the GLib main loop context. If the callback spawns a thread that calls GTK/libnotify methods, it violates GTK's single-thread requirement.

**How to avoid:** Keep callbacks simple and synchronous. If you need to do work, use GLib.idle_add():
```python
def _on_open_claude(self, notification, action, user_data):
    notification.close()  # Safe - called from main loop
    subprocess.Popen([...])  # Safe - spawns external process

    # If you need to update GTK widgets:
    # GLib.idle_add(self._update_ui)
```

**Warning signs:** Crashes on notification interaction, errors mentioning "not called from main thread".

### Pitfall 4: Incorrect Combined Notification Logic

**What goes wrong:** Two separate notifications shown when both metrics hit same threshold, or combined notification not using highest urgency when thresholds differ.

**Why it happens:** Not checking if both metrics crossed thresholds in same poll cycle before creating notifications.

**How to avoid:**
```python
# Detect both metrics needing alerts BEFORE creating any notifications
session_needs_alert = (session_threshold and ...)
weekly_needs_alert = (weekly_threshold and ...)

# Handle combined case first
if session_needs_alert and weekly_needs_alert:
    if session_threshold == weekly_threshold:
        # Same threshold - use that urgency
        self._show_combined_notification(session_threshold, ...)
    else:
        # Different thresholds - use highest urgency
        max_threshold = max(session_threshold, weekly_threshold)
        self._show_combined_notification(max_threshold, ...)
    # Mark BOTH as alerted
    self.alerted[('session', session_threshold)] = True
    self.alerted[('weekly', weekly_threshold)] = True
elif session_needs_alert:
    # Only session
    ...
```

**Warning signs:** User reports "I got two notifications at once for 75%", urgency level doesn't match highest threshold in combined alerts.

### Pitfall 5: Timeout/Persistence Expectations

**What goes wrong:** Expecting CRITICAL notifications to persist or EXPIRES_NEVER to work, but notifications still auto-dismiss.

**Why it happens:** Timeout settings are recommendations, not requirements. Many notification servers (especially GNOME Shell) ignore timeout settings entirely and use their own policies.

**How to avoid:**
- Don't rely on timeout behavior for critical functionality
- Use urgency levels for visual prominence, not persistence
- Document that notifications follow system defaults
```python
# Set urgency for visual cues, not persistence
notification.set_urgency(Notify.Urgency.CRITICAL)
# Don't expect this to work on all systems:
# notification.set_timeout(Notify.EXPIRES_NEVER)
```

**Warning signs:** User reports "critical notifications disappear too quickly" - this is server-dependent, not a bug.

## Code Examples

Verified patterns from official sources:

### Complete Notification Manager Class

```python
# Source: Synthesized from libnotify documentation and best practices
from gi.repository import Notify, GLib
import subprocess
import time

class UsageNotifier:
    """Manages threshold-based usage notifications."""

    def __init__(self, app_name="Claude Code Usage Monitor"):
        # Initialize libnotify
        Notify.init(app_name)

        # Track alerted thresholds
        self.alerted = {}  # {(metric, threshold): True}

        # Grace period flag
        self.first_poll = True

        # Cache server capabilities
        self._actions_supported = None

    def check_and_notify(self, session_pct, weekly_pct,
                         session_reset, weekly_reset):
        """Check thresholds and show notifications if needed.

        Args:
            session_pct: Session usage percentage (0-100)
            weekly_pct: Weekly usage percentage (0-100)
            session_reset: Unix timestamp when session resets
            weekly_reset: Unix timestamp when weekly resets
        """
        if self.first_poll:
            self.first_poll = False
            return

        thresholds = [50, 75, 90]

        # Find highest crossed threshold for each metric
        session_threshold = self._highest_crossed(session_pct, thresholds)
        weekly_threshold = self._highest_crossed(weekly_pct, thresholds)

        # Check if we need to alert
        session_needs_alert = (
            session_threshold and
            ('session', session_threshold) not in self.alerted
        )
        weekly_needs_alert = (
            weekly_threshold and
            ('weekly', weekly_threshold) not in self.alerted
        )

        # Handle combined alerts
        if session_needs_alert and weekly_needs_alert:
            if session_threshold == weekly_threshold:
                # Same threshold
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
            self.alerted[('session', session_threshold)] = True
            self.alerted[('weekly', weekly_threshold)] = True
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
        """Return highest threshold crossed, or None."""
        crossed = [t for t in thresholds if percentage >= t]
        return max(crossed) if crossed else None

    def _show_notification(self, metric, percentage, threshold, reset_time):
        """Show notification for single metric threshold."""
        urgency_map = {
            50: (Notify.Urgency.LOW, "Heads up"),
            75: (Notify.Urgency.NORMAL, "Consider saving your work"),
            90: (Notify.Urgency.CRITICAL, "Save your work now")
        }

        urgency, advice = urgency_map[threshold]

        # Format strings
        metric_name = "Session Usage" if metric == 'session' else "Weekly Usage"
        title = f"{metric_name}: {percentage}%"
        reset_str = self._format_reset_time(reset_time)
        body = f"{advice}\n\nResets in {reset_str}"

        # Create and configure notification
        notification = Notify.Notification.new(title, body, "dialog-information")
        notification.set_urgency(urgency)

        # Add action button if supported
        if self._server_supports_actions():
            notification.add_action(
                "open-claude",
                "Open Claude Code",
                self._on_open_claude,
                None
            )

        notification.show()

    def _show_combined_notification(self, threshold, session_pct, weekly_pct,
                                    session_reset, weekly_reset):
        """Show combined notification for both metrics."""
        urgency_map = {
            50: (Notify.Urgency.LOW, "Heads up"),
            75: (Notify.Urgency.NORMAL, "Consider saving your work"),
            90: (Notify.Urgency.CRITICAL, "Save your work now")
        }

        urgency, advice = urgency_map[threshold]

        # Format strings
        title = f"Session & Weekly Usage: {threshold}%"
        session_reset_str = self._format_reset_time(session_reset)
        weekly_reset_str = self._format_reset_time(weekly_reset)
        body = (f"{advice}\n\n"
                f"Session resets in {session_reset_str}\n"
                f"Weekly resets in {weekly_reset_str}")

        # Create and configure notification
        notification = Notify.Notification.new(title, body, "dialog-information")
        notification.set_urgency(urgency)

        if self._server_supports_actions():
            notification.add_action(
                "open-claude",
                "Open Claude Code",
                self._on_open_claude,
                None
            )

        notification.show()

    def _format_reset_time(self, reset_timestamp):
        """Format Unix timestamp to human-readable time until reset."""
        now = time.time()
        seconds = int(reset_timestamp - now)

        if seconds < 0:
            return "shortly"

        # Convert to hours and days
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
        """Check if notification server supports action buttons."""
        if self._actions_supported is None:
            caps = Notify.get_server_caps()
            self._actions_supported = caps and 'actions' in caps
        return self._actions_supported

    def _on_open_claude(self, notification, action, user_data):
        """Callback when 'Open Claude Code' button is clicked."""
        notification.close()
        subprocess.Popen(["/usr/bin/xdg-open", "https://claude.ai"])
```

### Basic Notification Example

```python
# Source: https://github.com/mk-fg/notification-thing, libnotify docs
from gi.repository import Notify

# Initialize once at app startup
Notify.init("My App")

# Create notification
notification = Notify.Notification.new(
    "Summary Text",           # Title
    "Body text goes here",    # Body
    "dialog-information"      # Icon name or path
)

# Set urgency level (optional)
notification.set_urgency(Notify.Urgency.NORMAL)

# Show on screen
notification.show()
```

### Checking Server Capabilities

```python
# Source: https://github.com/phuhl/notify-send.py
from gi.repository import Notify

Notify.init("Test App")

# Get list of server capabilities
caps = Notify.get_server_caps()
print(f"Server capabilities: {caps}")

# Check for specific capability
if 'actions' in caps:
    print("Server supports action buttons")
else:
    print("Server does not support action buttons")

# Common capabilities:
# - 'actions': Action button support
# - 'body': Notification body text
# - 'body-markup': Pango markup in body
# - 'icon-static': Static icon display
# - 'persistence': Notifications persist across session
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pynotify module | gi.repository.Notify (PyGObject) | ~2012 (GTK 3 transition) | Old pynotify incompatible with GTK 3+, must use PyGObject bindings |
| set_icon_from_pixbuf() | set_image_from_pixbuf() | libnotify 0.5 (2010) | Method renamed, functionality identical |
| notify2 library | gi.repository.Notify | 2015+ | notify2 was compatibility shim, now unnecessary and unmaintained |
| Threading notifications | GLib main loop integration | Always required | Notifications must be on main thread, use GLib.idle_add() for safety |

**Deprecated/outdated:**
- **pynotify module**: Replaced by gi.repository.Notify in PyGObject 3.0+. Old tutorials using `import pynotify` are obsolete.
- **set_icon_from_pixbuf()**: Deprecated since libnotify 0.5, use set_image_from_pixbuf() instead.
- **notify2 library**: Compatibility layer for old pynotify code, no longer needed with PyGObject.

## Open Questions

Things that couldn't be fully resolved:

1. **Custom icon path for notifications**
   - What we know: Can pass icon name or path to Notify.Notification.new(), deprecated set_image_from_pixbuf() suggests custom icons possible
   - What's unclear: Best practice for custom app icon vs system icons, whether icon theme names are preferred
   - Recommendation: Start with system icon name like "dialog-information", test custom icon path if branding needed

2. **Exact wording for advice messages**
   - What we know: User wants escalating tone from "heads up" to "save work now"
   - What's unclear: Exact phrasing that feels helpful not alarming
   - Recommendation: Start with suggested wording, gather user feedback, iterate
   - Example options:
     - 50%: "Heads up" / "You're halfway there" / "Approaching limits"
     - 75%: "Consider saving your work" / "Getting close to limits" / "May want to wrap up"
     - 90%: "Save your work now" / "Nearly at limit" / "Close to session end"

3. **Reset alerts menu item necessity**
   - What we know: Alerts clear on app restart, tracked in-memory only
   - What's unclear: Will users want to manually reset alert tracking mid-session?
   - Recommendation: Skip menu item in Phase 3 (YAGNI), add if users request it

## Sources

### Primary (HIGH confidence)
- [Notify.Notification API Reference - lazka.github.io](https://lazka.github.io/pgi-docs/Notify-0.7/classes/Notification.html) - Complete API documentation
- [Notify.Urgency Documentation - valadoc.org](https://valadoc.org/libnotify/Notify.Urgency.html) - Urgency level definitions
- [libnotify Official Repository](https://github.com/GNOME/libnotify) - Source code and examples
- [Python GTK+ 3 Tutorial](https://python-gtk-3-tutorial.readthedocs.io/en/latest/) - GTK patterns and best practices
- [PyGObject Multi-Threading Guide](https://pygobject.readthedocs.io/en/latest/guide/threading.html) - Thread safety requirements
- [GLib Main Event Loop Documentation](https://docs.gtk.org/glib/main-loop.html) - Callback execution context

### Secondary (MEDIUM confidence)
- [Desktop Notifications in Linux with Python - DevDungeon](https://www.devdungeon.com/content/desktop-notifications-linux-python) - Comprehensive examples (connection refused during fetch, found via search)
- [Python libnotify add_action examples - ProgramCreek](https://www.programcreek.com/python/example/92191/gi.repository.Notify.init) - Community examples
- [Desktop notifications - ArchWiki](https://wiki.archlinux.org/title/Desktop_notifications) - Server capabilities and limitations (fetch failed, verified via search)
- [Python time conversion examples - GeeksforGeeks](https://www.geeksforgeeks.org/python/python-program-to-convert-seconds-into-hours-minutes-and-seconds/) - divmod() time formatting
- [Python humanize library - PyPI](https://pypi.org/project/humanize/) - Alternative time formatting approach

### Tertiary (LOW confidence)
- [A Comprehensive Guide to Notification Design - Toptal](https://www.toptal.com/designers/ux/notification-design) - UX best practices (general, not Linux-specific)
- [GNOME Notification Human Interface Guidelines](https://developer.gnome.org/hig/patterns/feedback/notifications.html) - Design guidance (search result, not deeply verified)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - libnotify is the official GNOME notification API, well-documented, verified in multiple sources
- Architecture: HIGH - Patterns synthesized from official API docs, verified examples, and established GTK best practices
- Pitfalls: MEDIUM to HIGH - Server capability issues confirmed in official docs, threading requirements from PyGObject docs, other pitfalls based on common patterns and logical inference

**Research date:** 2026-02-04
**Valid until:** ~2026-05-04 (90 days) - libnotify is mature and stable, API unlikely to change

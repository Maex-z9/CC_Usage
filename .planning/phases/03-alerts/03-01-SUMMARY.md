---
phase: 03-alerts
plan: 01
subsystem: notifications
tags: [libnotify, PyGObject, desktop-notifications, GTK3, threshold-alerts]

# Dependency graph
requires:
  - phase: 02-system-tray-display
    provides: TrayIndicator with periodic usage updates and GLib integration
provides:
  - UsageNotifier class with threshold tracking and popup notifications
  - Threshold-based alerts at 50%, 75%, 90% with escalating urgency
  - Combined notifications when both metrics cross thresholds
  - Action button support for opening Claude Code
  - Grace period preventing startup notification spam
affects: [04-configuration-polish]

# Tech tracking
tech-stack:
  added: [gi.repository.Notify]
  patterns: [threshold state tracking with dictionaries, grace period first-poll pattern, server capability detection caching]

key-files:
  created: [src/notifier.py]
  modified: [src/tray.py]

key-decisions:
  - "Use libnotify via PyGObject for GNOME-native notifications"
  - "Track alerted thresholds separately for session vs weekly metrics"
  - "Skip first poll (grace period) to prevent startup notification spam"
  - "Check server capabilities once and cache result for action button support"
  - "Use divmod for time formatting without external dependencies"

patterns-established:
  - "Threshold tracking pattern: dictionary keyed by (metric, threshold) tuples"
  - "Grace period pattern: first_poll boolean flag set in __init__, cleared on first check"
  - "Combined notification logic: check both metrics, handle same/different thresholds"
  - "Server capability caching: check once, store in instance variable"

# Metrics
duration: 2min
completed: 2026-02-04
---

# Phase 3 Plan 1: Alerts Summary

**Desktop popup notifications at 50%, 75%, 90% thresholds with escalating urgency, combined alerts, and action buttons**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-04T16:08:45Z
- **Completed:** 2026-02-04T16:10:44Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Threshold-based notifications with escalating urgency (LOW → NORMAL → CRITICAL)
- Combined notifications when both session and weekly cross thresholds simultaneously
- Grace period preventing notification spam on app startup
- Action button support with server capability detection
- Integrated into TrayIndicator refresh cycle

## Task Commits

Each task was committed atomically:

1. **Task 1: Create UsageNotifier class** - `11e2383` (feat)
2. **Task 2: Integrate notifier with TrayIndicator** - `d977f04` (feat)

## Files Created/Modified
- `src/notifier.py` - UsageNotifier class with threshold tracking, notification display, and server capability detection
- `src/tray.py` - Integrated notifier instantiation and check_and_notify() call in refresh cycle

## Decisions Made

1. **Use libnotify via PyGObject** - GNOME-native notification system, well-documented, supports urgency levels and action buttons
2. **Track thresholds separately by metric** - Dictionary keyed by (metric, threshold) allows independent tracking of session vs weekly alerts
3. **Grace period implementation** - Skip first poll with `first_poll` boolean flag to prevent startup notification spam
4. **Cache server capabilities** - Check `Notify.get_server_caps()` once and store result to avoid repeated lookups
5. **Manual time formatting with divmod** - No external dependencies, simple "Xh" or "Xd" format sufficient for reset times
6. **Combined notification for same-poll crossings** - Single notification when both metrics cross thresholds reduces notification spam

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation was straightforward following RESEARCH.md patterns.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 4 (Configuration & Polish):**
- Notification system fully functional with default thresholds (50%, 75%, 90%)
- Threshold customization can be added via configuration UI
- "Reset alerts" menu item can be added if users request mid-session alert reset
- Custom notification icon path can be configured for branding

**No blockers:** All core notification functionality complete and tested.

---
*Phase: 03-alerts*
*Completed: 2026-02-04*

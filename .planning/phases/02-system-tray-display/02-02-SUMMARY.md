---
phase: 02-system-tray-display
plan: 02
subsystem: ui
tags: [gtk, ayatana-appindicator, system-tray, python, gobject]

# Dependency graph
requires:
  - phase: 01-data-source
    provides: API fetch, credentials, UsageData model
  - phase: 02-01
    provides: Icon generation and time formatting utilities
provides:
  - TrayIndicator class managing system tray with AppIndicator3
  - Main entry point for application execution
  - System tray with dynamic icon, dropdown menu, and tooltip
  - Periodic usage updates every 5 minutes
affects: [02-03-menu-display, 03-alerts]

# Tech tracking
tech-stack:
  added: [AyatanaAppIndicator3, Gtk3, GLib]
  patterns: [AppIndicator for GNOME system tray, GLib timers for periodic updates, GTK menu construction]

key-files:
  created:
    - src/tray.py
    - src/main.py
    - system-requirements.txt
  modified:
    - src/tray.py (Ayatana fix)
    - system-requirements.txt (Ayatana fix)

key-decisions:
  - "Use AyatanaAppIndicator3 (modern fork) instead of legacy Ubuntu AppIndicator3"
  - "Periodic updates every 5 minutes via GLib.timeout_add_seconds()"
  - "Session percentage controls gauge arc fill, max(session, weekly) controls color"
  - "Show session reset time in menu (5-hour window more relevant for active users)"

patterns-established:
  - "TrayIndicator class encapsulates all system tray logic"
  - "GLib.SOURCE_CONTINUE pattern for keeping timers alive"
  - "Error handling prints to stderr and updates tooltip with error message"
  - "Menu rebuilt on each update to reflect current data"

# Metrics
duration: 12min
completed: 2026-02-04
---

# Phase 2 Plan 2: Tray Indicator Summary

**System tray indicator with dynamic gauge icon, dropdown menu, and tooltip using AyatanaAppIndicator3 for GNOME**

## Performance

- **Duration:** 12 minutes
- **Started:** 2026-02-04T13:49:44Z (c4f73d2)
- **Completed:** 2026-02-04T13:56:11Z (16174ed)
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- TrayIndicator class with AppIndicator3 integration
- Dynamic icon display using session percentage for gauge fill and max(session, weekly) for color
- Dropdown menu showing both session and weekly percentages with reset countdown
- Main entry point with clean error handling
- Compatibility fix for modern GNOME using Ayatana fork

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TrayIndicator class** - `c4f73d2` (feat)
2. **Task 2: Create main entry point** - `0266ed6` (feat)
3. **Task 3: Document system dependencies** - `85c84a5` (chore)
4. **Task 3: Verify system tray appears** - `16174ed` (fix - Ayatana compatibility)

## Files Created/Modified
- `src/tray.py` - TrayIndicator class managing AppIndicator3, menu, tooltip, and periodic updates
- `src/main.py` - Application entry point with error handling and keyboard interrupt support
- `system-requirements.txt` - Documented system packages for GNOME/GTK integration

## Decisions Made

**Use AyatanaAppIndicator3 instead of legacy AppIndicator3**
- Rationale: Modern GNOME systems use Ayatana fork, legacy Ubuntu AppIndicator3 is deprecated
- Implementation: Changed imports to `AyatanaAppIndicator3`, aliased as `AppIndicator3` to keep code unchanged
- Benefit: Works on modern Ubuntu/GNOME systems without requiring legacy packages

**Periodic updates every 5 minutes**
- Rationale: Balance between freshness and API rate limits
- Implementation: `GLib.timeout_add_seconds(300, self._update_usage)`
- Benefit: User always sees recent data without excessive API calls

**Session percentage for arc fill, max(session, weekly) for color**
- Rationale: Session is immediate concern, color warns about worst-case urgency
- Implementation: `generate_gauge_icon(session_percent, max(session_percent, weekly_percent))`
- Benefit: User sees both metrics at a glance without confusion

**Show session reset time in menu**
- Rationale: 5-hour window resets faster and is more relevant for active Claude Code users
- Implementation: Display `format_time_until(usage_data.session_resets_at)` in menu
- Benefit: User knows when their session window resets

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switch to AyatanaAppIndicator3**
- **Found during:** Task 3 (Verify system tray appears)
- **Issue:** Legacy AppIndicator3 not available on modern GNOME (user installed gir1.2-ayatanaappindicator3-0.1)
- **Fix:** Changed imports to use AyatanaAppIndicator3, aliased as AppIndicator3
- **Files modified:** src/tray.py, system-requirements.txt
- **Verification:** Import test passed, app ran successfully for 3 seconds
- **Committed in:** 16174ed (fix commit after checkpoint resolution)

**2. [Rule 2 - Missing Critical] Added system-requirements.txt**
- **Found during:** Task 3 (Verify system tray appears)
- **Issue:** No documentation of required system packages for GTK/AppIndicator
- **Fix:** Created system-requirements.txt with all GObject Introspection packages
- **Files modified:** system-requirements.txt (created)
- **Verification:** All packages documented with install commands
- **Committed in:** 85c84a5 (chore commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both fixes essential for compatibility with modern GNOME systems. No scope creep.

## Issues Encountered

**AppIndicator3 package not available**
- Issue: User's GNOME system uses Ayatana fork, not legacy Ubuntu AppIndicator3
- Detection: Import error when attempting to load AppIndicator3
- Resolution: Paused at checkpoint, user installed gir1.2-ayatanaappindicator3-0.1, updated code to use Ayatana
- Outcome: App now compatible with modern GNOME environments

## Authentication Gates

None - API authentication handled by Phase 1 credentials.

## User Setup Required

None - system packages and Python dependencies documented in system-requirements.txt and requirements.txt. Users will install dependencies before first run.

## Next Phase Readiness

**Ready for Phase 2 Plan 3 (Tooltip and Menu Display)**
- TrayIndicator class provides foundation for menu enhancements
- Tooltip and menu already functional with basic usage display
- Icon generation integrated and working
- Periodic updates established

**Ready for Phase 3 (Alerts)**
- Usage data structure in place for threshold detection
- TrayIndicator class can be extended with notification support
- Color thresholds already established (green/yellow/red)

**No blockers**
- System tray working on modern GNOME
- All Phase 1 integrations functional
- Menu and tooltip displaying correctly

---
*Phase: 02-system-tray-display*
*Completed: 2026-02-04*

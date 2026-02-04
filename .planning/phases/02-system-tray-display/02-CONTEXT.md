# Phase 2: System Tray & Display - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Show current usage status via system tray icon and menu. User can see at a glance (icon color), hover for quick numbers (tooltip), or click for full details (menu). This phase makes the data from Phase 1 visible. Alerts/notifications are Phase 3. Configuration is Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Icon appearance
- Circular gauge shape (like a pie chart or progress ring)
- Gauge shows session (5-hour) usage only
- Monochrome icon with colored fill portion (GNOME-native feel)
- Gray outline, colored fill represents usage level

### Menu layout
- Session and weekly usage displayed side by side (compact row format)
- Menu actions: Refresh, Settings (placeholder for Phase 4), Quit
- Reset time shown as relative ("Resets in 2h 15m")
- Percentages as whole numbers only (no decimals)

### Tooltip content
- Brief summary format: "Session: 36% | Weekly: 77%"
- No app name in tooltip — just the data
- No reset times in tooltip (keep it brief)

### Color thresholds
- Same thresholds for both session and weekly metrics
- Color based on the higher of session/weekly (worst-case at a glance)

### Claude's Discretion
- Whether to show percentage text inside/near the icon (based on what looks good)
- Whether to highlight the higher metric in tooltip (if it adds value)
- Error state handling in tooltip (error message vs stale data)
- Exact threshold values for yellow and red (sensible defaults)

</decisions>

<specifics>
## Specific Ideas

- Icon should feel native to GNOME — monochrome with color fill matches system tray conventions
- Side-by-side layout keeps the menu compact — user wants quick info, not a dashboard

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-system-tray-display*
*Context gathered: 2026-02-04*

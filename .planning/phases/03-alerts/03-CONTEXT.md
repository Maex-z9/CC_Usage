# Phase 3: Alerts - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Popup notifications when usage hits thresholds (50%, 75%, 90%). Users receive timely alerts with escalating urgency. Configuration of custom thresholds belongs to Phase 4 — this phase uses the defaults.

</domain>

<decisions>
## Implementation Decisions

### Notification Content
- **Title:** Metric name + percentage (e.g., "Session Usage: 75%" or "Weekly Usage: 90%")
- **Body:** Advice message + time until reset
- **Escalating urgency in advice:**
  - 50%: "Heads up" tone
  - 75%: "Consider saving your work"
  - 90%: "Save your work now"
- **Icon:** Use the app's gauge icon (same as tray)

### Combined Alerts
- When both session AND weekly cross thresholds in the same poll → single combined notification
- **Combined title:** "Session & Weekly Usage: 75%" (both metrics named)
- **Combined body:** Show both reset times ("Session resets in 2h, Weekly resets in 3d")
- **Same urgency** as individual alerts at that threshold (no bump for combined)
- **Different thresholds at same poll:** If session hits 75% and weekly hits 90%, single combined alert using highest urgency (90% critical)

### Threshold Tracking
- **Track separately** for session vs weekly (each metric has its own alerted state)
- **Never re-alert same threshold** within app session (app restart clears tracking)
- **Grace period on startup:** Wait one poll interval before alerting (avoid spam on restart)

### Claude's Discretion
- Whether to add a "Reset alerts" menu item (manual way to re-enable alerts)
- Exact wording of advice messages within the tone guidance
- libnotify implementation details

</decisions>

<specifics>
## Specific Ideas

- Notifications should feel like a helpful reminder, not an alarm
- The escalation from "heads up" to "save work now" should feel natural
- Don't nag — once alerted at a threshold, stay quiet until next threshold or restart

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-alerts*
*Context gathered: 2026-02-04*

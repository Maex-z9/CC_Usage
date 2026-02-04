# Requirements: Claude Code Usage Overlay

**Defined:** 2026-02-04
**Core Value:** Never be surprised by hitting Claude Code usage limits — always know where you stand and get timely reminders to save your work.

## v1 Requirements

### System Tray

- [x] **TRAY-01**: System tray icon visible in GNOME panel
- [x] **TRAY-02**: Click icon to see menu with current usage details
- [x] **TRAY-03**: Hover tooltip shows quick usage summary (panel label workaround for GNOME)
- [x] **TRAY-04**: Color-coded icon (green/yellow/red based on highest usage level)
- [ ] **TRAY-05**: Auto-start on login via .desktop file

### Usage Display

- [x] **DISP-01**: Show session % (five_hour utilization)
- [x] **DISP-02**: Show weekly % (seven_day utilization)
- [x] **DISP-03**: Show time remaining until reset ("Resets in 2h 15m")

### Alerts

- [x] **ALRT-01**: Popup notification at configured thresholds (default 50/75/90%)
- [x] **ALRT-02**: Combined popup when both metrics hit same threshold
- [x] **ALRT-03**: Different thresholds configurable per metric (session vs weekly)
- [x] **ALRT-04**: Notification urgency: low at 50%, normal at 75%, critical at 90%
- [x] **ALRT-05**: "Open Claude Code" action button in notification

### Configuration

- [ ] **CONF-01**: Configurable thresholds per metric
- [ ] **CONF-02**: Configurable polling interval (default 60s)
- [ ] **CONF-03**: Keyboard shortcut to force refresh / show popup
- [ ] **CONF-04**: Pause notifications mode (presentation mode)

### Data Source

- [x] **DATA-01**: Read OAuth token from ~/.claude/.credentials.json
- [x] **DATA-02**: Poll Anthropic usage API periodically
- [x] **DATA-03**: Handle API errors gracefully with retry

## v2 Requirements

### Token Management

- **TOKN-01**: Automatic token refresh when expired
- **TOKN-02**: Prompt user to re-authenticate if refresh fails

### Advanced Features

- **ADVN-01**: Usage history graph (last 7 days)
- **ADVN-02**: Predict when limit will be hit based on current rate
- **ADVN-03**: Multiple account support

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile/other platforms | Linux/GNOME only per user request |
| Automatic actions (pause, block) | Reminder only, user dismissed |
| Sound alerts | User preferred visual notifications |
| Web dashboard | Desktop app only |
| Email/SMS notifications | Desktop notifications sufficient |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| TRAY-01 | Phase 2 | Complete |
| TRAY-02 | Phase 2 | Complete |
| TRAY-03 | Phase 2 | Complete |
| TRAY-04 | Phase 2 | Complete |
| DISP-01 | Phase 2 | Complete |
| DISP-02 | Phase 2 | Complete |
| DISP-03 | Phase 2 | Complete |
| ALRT-01 | Phase 3 | Complete |
| ALRT-02 | Phase 3 | Complete |
| ALRT-03 | Phase 3 | Complete |
| ALRT-04 | Phase 3 | Complete |
| ALRT-05 | Phase 3 | Complete |
| CONF-01 | Phase 4 | Pending |
| CONF-02 | Phase 4 | Pending |
| CONF-03 | Phase 4 | Pending |
| CONF-04 | Phase 4 | Pending |
| TRAY-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-02-04 after Phase 3 completion*

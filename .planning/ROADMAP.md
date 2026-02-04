# Roadmap: Claude Code Usage Overlay

## Overview

This roadmap delivers a Linux/GNOME system tray application that monitors Claude Code token usage and provides timely alerts at usage thresholds. We build in four phases: first proving we can fetch usage data from the API, then showing it to the user via system tray, adding the core alert functionality, and finally polishing with configuration and auto-start capabilities.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Data Source** - Prove we can fetch usage data
- [ ] **Phase 2: System Tray & Display** - Show usage to user
- [ ] **Phase 3: Alerts** - Deliver core value with notifications
- [ ] **Phase 4: Configuration & Polish** - Customization and auto-start

## Phase Details

### Phase 1: Data Source
**Goal**: Application can fetch and parse Claude Code usage data from Anthropic API
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. Application reads OAuth token from ~/.claude/.credentials.json
  2. Application successfully fetches usage data from Anthropic API
  3. Application parses five_hour and seven_day utilization percentages
  4. Application handles API errors gracefully with retry logic
**Plans**: 1 plan

Plans:
- [x] 01-01-PLAN.md — Create data source layer (config + API client with retry)

### Phase 2: System Tray & Display
**Goal**: User can see current usage status via system tray icon and menu
**Depends on**: Phase 1
**Requirements**: TRAY-01, TRAY-02, TRAY-03, TRAY-04, DISP-01, DISP-02, DISP-03
**Success Criteria** (what must be TRUE):
  1. System tray icon appears in GNOME panel
  2. User can click icon to see menu with session and weekly usage percentages
  3. Hover tooltip shows quick usage summary
  4. Icon color reflects highest usage level (green/yellow/red)
  5. Menu displays time remaining until reset
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Create icon generator and time formatting utilities
- [ ] 02-02-PLAN.md — Create TrayIndicator class and main entry point
- [ ] 02-03-PLAN.md — Visual verification checkpoint

### Phase 3: Alerts
**Goal**: User receives timely popup notifications when usage hits thresholds
**Depends on**: Phase 2
**Requirements**: ALRT-01, ALRT-02, ALRT-03, ALRT-04, ALRT-05
**Success Criteria** (what must be TRUE):
  1. User receives popup notification when session or weekly usage hits configured threshold
  2. Notification shows which metric triggered alert and current percentage
  3. When both metrics hit same threshold simultaneously, single combined popup appears
  4. Notification urgency matches severity (low at 50%, normal at 75%, critical at 90%)
  5. User can click "Open Claude Code" button in notification
  6. Application tracks alerted thresholds to prevent repeat notifications
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 4: Configuration & Polish
**Goal**: User can customize behavior and application auto-starts on login
**Depends on**: Phase 3
**Requirements**: CONF-01, CONF-02, CONF-03, CONF-04, TRAY-05
**Success Criteria** (what must be TRUE):
  1. User can configure thresholds per metric (session vs weekly)
  2. User can configure polling interval
  3. User can trigger force refresh via keyboard shortcut
  4. User can enable pause notifications mode
  5. Application auto-starts on login via .desktop file
**Plans**: TBD

Plans:
- [ ] TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Source | 1/1 | Complete | 2026-02-04 |
| 2. System Tray & Display | 0/3 | Not started | - |
| 3. Alerts | 0/TBD | Not started | - |
| 4. Configuration & Polish | 0/TBD | Not started | - |

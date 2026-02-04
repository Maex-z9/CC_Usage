# Claude Code Usage Overlay

## What This Is

A Linux/GNOME system tray application that monitors Claude Code token usage (both session and weekly) and displays popup alerts at 50%, 75%, and 90% thresholds. It serves as a gentle reminder to save work, push to GitHub, or take a break before hitting usage limits.

## Core Value

Never be surprised by hitting Claude Code usage limits — always know where you stand and get timely reminders to save your work.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] System tray icon showing current usage status
- [ ] Click tray icon to see session % and weekly % details
- [ ] Popup alert at 50% threshold (session and/or weekly)
- [ ] Popup alert at 75% threshold (session and/or weekly)
- [ ] Popup alert at 90% threshold (session and/or weekly)
- [ ] Combined popup when both metrics hit same threshold simultaneously
- [ ] Dismissible popups (click to dismiss, continue working)
- [ ] Discover and use the API that Claude Code uses for usage data
- [ ] Periodic polling to check usage (configurable interval)

### Out of Scope

- Mobile/other platforms — Linux/GNOME only
- Usage history/graphs — just current status
- Automatic actions (pause work, block usage) — reminder only
- Multiple account support — single user

## Context

- User runs Claude Code CLI daily for development work
- `/status` command shows usage with session % and weekly %
- Session usage resets daily at 11:59am (Europe/Berlin timezone)
- Weekly usage resets weekly (harder limit — locked out at 100%)
- Claude Code stores config in `~/.claude/` — may contain usage cache
- Need to reverse-engineer or discover the API endpoint Claude Code calls

## Constraints

- **Platform**: Linux with GNOME desktop — uses AppIndicator for tray, libnotify for popups
- **Data source**: Must discover Claude Code's usage API — not documented publicly
- **Permissions**: Needs access to whatever auth Claude Code uses (likely in ~/.claude/)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| System tray over floating widget | Less intrusive, GNOME-native | — Pending |
| Discover API over parsing CLI | More reliable, real-time data | — Pending |
| Combined popups for matching thresholds | Less notification spam | — Pending |

---
*Last updated: 2026-02-04 after initialization*

# Architecture Research: Claude Code Usage Overlay

## Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Usage Overlay                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Config     │    │   API        │    │   Alert      │  │
│  │   Manager    │    │   Poller     │    │   Tracker    │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │   App Core      │                      │
│                    │   (Main Loop)   │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│         ┌───────────────────┼───────────────────┐           │
│         │                   │                   │           │
│  ┌──────▼───────┐    ┌──────▼───────┐    ┌──────▼───────┐  │
│  │   Tray       │    │   Menu       │    │   Notifier   │  │
│  │   Manager    │    │   Handler    │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Config Manager
**Responsibility:** Load/save configuration, credentials

**Files:**
- Reads: `~/.claude/.credentials.json` (OAuth token)
- Reads/Writes: `~/.config/claude-usage-overlay/config.json` (settings)

**Data:**
```python
@dataclass
class Config:
    poll_interval: int = 60  # seconds
    thresholds: list[int] = [50, 75, 90]
    show_session: bool = True
    show_weekly: bool = True
```

### 2. API Poller
**Responsibility:** Fetch usage data from Anthropic API

**Endpoint:** `GET https://api.anthropic.com/api/oauth/usage`

**Input:** OAuth access token
**Output:**
```python
@dataclass
class UsageData:
    session_percent: float  # five_hour.utilization
    session_resets_at: datetime
    weekly_percent: float   # seven_day.utilization
    weekly_resets_at: datetime
```

**Error handling:**
- Network errors → retry with exponential backoff
- 401 Unauthorized → attempt token refresh or notify user
- 429 Rate limited → back off, increase poll interval

### 3. Alert Tracker
**Responsibility:** Track which thresholds have been alerted, avoid duplicates

**State:**
```python
@dataclass
class AlertState:
    session_alerted: set[int]  # e.g., {50, 75}
    weekly_alerted: set[int]
    last_session_percent: float
    last_weekly_percent: float
```

**Logic:**
- If usage crosses threshold AND not already alerted → trigger alert
- If usage drops below threshold → remove from alerted set (can re-alert)
- If usage resets (detects resets_at change) → clear all alerted

### 4. Tray Manager
**Responsibility:** Manage system tray icon and status

**Uses:** `AppIndicator3`

**States:**
- Normal (green/default icon)
- Warning (yellow) - >50%
- Critical (red) - >90%
- Error (gray) - API failed

### 5. Menu Handler
**Responsibility:** Build and update tray menu

**Menu structure:**
```
┌──────────────────────────┐
│ Session: 36% (resets 12pm)│
│ Weekly:  77% (resets Wed) │
├──────────────────────────┤
│ Refresh                   │
│ Settings...               │
├──────────────────────────┤
│ Quit                      │
└──────────────────────────┘
```

### 6. Notifier
**Responsibility:** Show desktop notifications

**Uses:** `gi.repository.Notify`

**Notification types:**
- Single metric alert: "Session usage at 75%"
- Combined alert: "Usage at 50% (Session & Weekly)"

## Data Flow

```
1. Startup
   Config Manager → loads credentials
   Config Manager → loads settings
   API Poller → initial fetch
   Tray Manager → creates icon with initial state
   Alert Tracker → initializes (no alerts yet)

2. Poll Cycle (every N seconds)
   Timer triggers
   API Poller → fetches usage
   Alert Tracker → checks thresholds
   If threshold crossed → Notifier shows popup
   Tray Manager → updates icon color
   Menu Handler → updates menu text

3. User clicks tray
   Menu Handler → shows current state

4. User dismisses notification
   (no action needed, libnotify handles)
```

## Build Order (Phases)

| Phase | Components | Deliverable |
|-------|------------|-------------|
| 1 | Config Manager, API Poller | Can fetch and print usage |
| 2 | Tray Manager, Menu Handler | Tray icon with usage display |
| 3 | Alert Tracker, Notifier | Threshold alerts working |
| 4 | Polish | Error handling, auto-start, config UI |

## File Structure

```
claude-usage-overlay/
├── src/
│   ├── __init__.py
│   ├── main.py           # Entry point, GTK main loop
│   ├── config.py         # Config Manager
│   ├── api.py            # API Poller
│   ├── alerts.py         # Alert Tracker
│   ├── tray.py           # Tray Manager + Menu Handler
│   └── notifier.py       # Notifier
├── resources/
│   └── icons/
│       ├── normal.svg
│       ├── warning.svg
│       └── critical.svg
├── setup.py
└── README.md
```

## Threading Model

GTK requires all UI operations on the main thread. Use `GLib.timeout_add_seconds()` for periodic polling - this integrates with GTK's main loop and runs callbacks on the main thread.

```python
def start_polling(interval_seconds):
    GLib.timeout_add_seconds(interval_seconds, poll_and_update)

def poll_and_update():
    usage = api.fetch_usage()
    update_ui(usage)
    return True  # Continue polling
```

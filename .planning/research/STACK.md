# Stack Research: Claude Code Usage Overlay

## Recommended Stack

### Language: Python 3.11+
**Confidence: High**

**Rationale:**
- Best GTK/GObject Introspection bindings via PyGObject
- Native libnotify support
- Simple HTTP requests with `requests` library
- Fast development iteration
- Pre-installed on most Linux distros

**Alternatives considered:**
- Go: Good for CLI tools but GTK bindings are less mature
- Rust: Excellent but overkill for this scope
- Node.js: Electron would be too heavy for a tray app

### GUI Framework: GTK 3 with AppIndicator3
**Confidence: High**

**Components:**
- `gi.repository.Gtk` - GTK bindings
- `gi.repository.AppIndicator3` - System tray integration
- `gi.repository.Notify` - Desktop notifications (libnotify)

**Installation (Debian/Ubuntu):**
```bash
sudo apt install python3-gi gir1.2-appindicator3-0.1 libnotify-bin
pip install PyGObject requests
```

**GNOME-specific note:** GNOME Shell removed legacy system tray in 3.26. Users need the "AppIndicator and KStatusNotifierItem Support" extension installed. This is common and most GNOME users have it.

### HTTP Client: requests
**Confidence: High**

Simple, reliable HTTP client for API calls.

```bash
pip install requests
```

### Configuration: JSON file
**Confidence: High**

Store in `~/.config/claude-usage-overlay/config.json`:
- Polling interval
- Alert thresholds
- Dismissed alerts tracking

## Dependencies Summary

| Package | Purpose | Version |
|---------|---------|---------|
| python3 | Runtime | 3.11+ |
| PyGObject | GTK bindings | 3.46+ |
| gir1.2-appindicator3-0.1 | Tray icon | 0.1 |
| libnotify | Notifications | 0.8+ |
| requests | HTTP client | 2.31+ |

## What NOT to Use

| Technology | Reason |
|------------|--------|
| Electron | Too heavy for a simple tray app |
| Qt/PyQt | GTK is more native on GNOME |
| Tkinter | No system tray support |
| pynotify | Deprecated, use GObject Introspection |
| Gtk.StatusIcon | Deprecated in GTK 3.14 |

## API Discovery

**Endpoint:** `https://api.anthropic.com/api/oauth/usage`

**Authentication:** OAuth Bearer token from `~/.claude/.credentials.json`

**Response structure:**
```json
{
  "five_hour": {
    "utilization": 36.0,
    "resets_at": "2026-02-04T10:59:59+00:00"
  },
  "seven_day": {
    "utilization": 77.0,
    "resets_at": "2026-02-05T10:59:59+00:00"
  }
}
```

**Required headers:**
```
Authorization: Bearer <access_token>
Accept: application/json
anthropic-beta: oauth-2025-04-20
```

## Sources

- [AppIndicator Tutorial](http://candidtim.github.io/appindicator/2014/09/13/ubuntu-appindicator-step-by-step.html)
- [Custom System Tray Indicator](https://fosspost.org/custom-system-tray-icon-indicator-linux)
- [Claude Code Usage API](https://codelynx.dev/posts/claude-code-usage-limits-statusline)
- [Desktop Notifications in Python](https://www.devdungeon.com/content/desktop-notifications-linux-python)

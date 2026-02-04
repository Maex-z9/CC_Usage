# Research Summary: Claude Code Usage Overlay

## Key Findings

### Stack
**Python 3 + GTK 3 + AppIndicator3 + libnotify**

- Python with PyGObject for GTK bindings
- AppIndicator3 for GNOME system tray (requires extension on modern GNOME)
- libnotify via GObject Introspection for desktop notifications
- Simple `requests` library for API calls

### API Discovery
**Endpoint found:** `https://api.anthropic.com/api/oauth/usage`

- Uses OAuth Bearer token from `~/.claude/.credentials.json`
- Returns `five_hour` (session) and `seven_day` (weekly) utilization percentages
- Also returns `resets_at` timestamps for each limit

### Table Stakes Features
1. System tray icon with click-to-view usage
2. Popup alerts at 50%, 75%, 90% thresholds
3. Show both session and weekly percentages
4. Dismissible notifications

### Watch Out For
1. **GNOME tray support** - Requires AppIndicator extension (document this)
2. **Token expiration** - OAuth tokens expire, need refresh handling
3. **Notification spam** - Must track alerted thresholds to avoid repeating
4. **GTK thread safety** - Use GLib.timeout_add_seconds() for polling

## Architecture

```
Config → API Poller → Alert Tracker → Notifier
              ↓
        Tray Manager → Menu
```

**Build order:**
1. API + Config (prove we can fetch data)
2. Tray + Menu (show it to user)
3. Alerts + Notifications (the core value)
4. Polish (error handling, auto-start)

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.11+ | Best GTK bindings, fast development |
| GUI | GTK 3 + AppIndicator3 | Native GNOME experience |
| Notifications | libnotify (Notify) | Standard, integrates with GNOME |
| HTTP | requests | Simple, reliable |
| Config storage | JSON in ~/.config | Standard Linux convention |
| Polling | GLib.timeout_add_seconds | Thread-safe, integrates with GTK loop |

## Dependencies

```bash
# System packages (Debian/Ubuntu)
sudo apt install python3-gi gir1.2-appindicator3-0.1 libnotify-bin

# Python packages
pip install PyGObject requests
```

## Risk Summary

| Risk | Mitigation |
|------|------------|
| No tray icon on GNOME | Document extension requirement |
| Token expires | Implement refresh or prompt user |
| API changes | Defensive parsing, graceful degradation |

## Next Steps

1. Define requirements based on research
2. Create roadmap with 4 phases
3. Start with Phase 1: API + Config (prove concept)

# Features Research: Claude Code Usage Overlay

## Feature Categories

### Table Stakes (Must Have)

| Feature | Complexity | Notes |
|---------|------------|-------|
| System tray icon | Low | Basic AppIndicator with icon |
| Show current usage on click | Low | Menu or tooltip with session % and weekly % |
| Popup at 50% threshold | Low | libnotify notification |
| Popup at 75% threshold | Low | libnotify notification |
| Popup at 90% threshold | Low | libnotify notification |
| Dismissible popups | Low | Click to dismiss, built into libnotify |
| Periodic polling | Low | Timer-based API calls |
| Read credentials from ~/.claude | Low | JSON parsing |

### Differentiators (Nice to Have)

| Feature | Complexity | Notes |
|---------|------------|-------|
| Combined alerts (same threshold) | Low | Track both metrics, single popup when coincide |
| Configurable thresholds | Medium | Config file, default 50/75/90 |
| Configurable polling interval | Low | Config file, default 60s |
| Color-coded tray icon | Medium | Green/yellow/red based on usage level |
| Time until reset display | Low | Parse resets_at from API |
| Minimize to tray on startup | Low | Auto-start minimized option |
| Auto-start on login | Medium | .desktop file in autostart |

### Anti-Features (Don't Build)

| Feature | Reason |
|---------|--------|
| Usage history/graphs | Scope creep - user said just current status |
| Multiple account support | Single user app |
| Automatic actions (pause, block) | User wants reminder only |
| Web dashboard | Desktop app only |
| Sound alerts | User didn't ask, can be annoying |
| Email/SMS notifications | Desktop notifications sufficient |
| API key management | Use existing Claude credentials |
| Custom notification styling | Use system defaults |

## Feature Dependencies

```
Read credentials
    └── Poll API
        ├── Update tray icon/menu
        └── Check thresholds
            └── Show notifications
                └── Combined alerts logic
```

## User Flow

1. App starts → reads credentials from `~/.claude/.credentials.json`
2. Polls API immediately → updates tray icon
3. Every N seconds → poll API
4. If threshold crossed → show popup (combined if both metrics hit same threshold)
5. User clicks tray → sees current session % and weekly %
6. User dismisses popup → continue working
7. Track dismissed thresholds to avoid repeat alerts until usage drops or resets

## Edge Cases

| Case | Behavior |
|------|----------|
| No credentials found | Show error notification, tray icon indicates error state |
| API request fails | Retry with backoff, show error state after 3 failures |
| Token expired | Credentials include refreshToken - could auto-refresh or prompt |
| Usage drops below threshold | Reset alert tracking (can alert again if crosses) |
| Usage resets (daily/weekly) | Reset all alert tracking |

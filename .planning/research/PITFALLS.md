# Pitfalls Research: Claude Code Usage Overlay

## Critical Pitfalls

### 1. GNOME System Tray Removal
**Risk: High**

GNOME Shell removed legacy system tray support in version 3.26. Without the AppIndicator extension, users won't see the tray icon at all.

**Warning signs:**
- App runs but no tray icon visible
- No errors in console (fails silently)

**Prevention:**
- Document requirement for "AppIndicator and KStatusNotifierItem Support" extension
- On startup, detect GNOME and check if extension is active
- Show notification explaining the issue if tray icon fails to appear

**Phase:** Phase 2 (Tray implementation)

---

### 2. OAuth Token Expiration
**Risk: Medium**

The access token in `~/.claude/.credentials.json` has an `expiresAt` timestamp. After expiration, API calls will fail with 401.

**Warning signs:**
- API returns 401 Unauthorized
- Token expiration timestamp passed

**Prevention:**
- Check `expiresAt` before each API call
- Implement token refresh using `refreshToken`
- If refresh fails, notify user to re-authenticate via Claude Code

**Refresh endpoint:** (needs investigation - may need to run `claude` CLI to refresh)

**Phase:** Phase 1 (API implementation)

---

### 3. Credentials File Location Assumption
**Risk: Low**

Assuming `~/.claude/.credentials.json` exists and has the expected structure. Path could vary or user might not be authenticated.

**Warning signs:**
- FileNotFoundError on startup
- KeyError when parsing JSON

**Prevention:**
- Graceful error handling on startup
- Clear error message: "Claude Code not authenticated. Run `claude` first."
- Check for required fields in JSON

**Phase:** Phase 1 (Config implementation)

---

### 4. API Rate Limiting the Monitor
**Risk: Low**

Polling too frequently could itself trigger rate limits or add unnecessary API load.

**Warning signs:**
- 429 responses from API
- Increased API costs (if using API key instead of OAuth)

**Prevention:**
- Default poll interval of 60 seconds (reasonable)
- Exponential backoff on errors
- Make interval configurable

**Phase:** Phase 1 (API implementation)

---

### 5. GTK Thread Safety
**Risk: Medium**

GTK is not thread-safe. Making API calls in a background thread and updating UI directly will cause crashes or undefined behavior.

**Warning signs:**
- Random crashes
- UI freezes
- "Gtk-CRITICAL" warnings in console

**Prevention:**
- Use `GLib.timeout_add_seconds()` for polling (runs on main thread)
- If using threads, use `GLib.idle_add()` to schedule UI updates on main thread
- Keep API calls synchronous and fast (just a simple GET)

**Phase:** Phase 2 (Tray implementation)

---

### 6. Notification Spam
**Risk: Medium**

Without proper tracking, the app could spam notifications every poll cycle once usage exceeds a threshold.

**Warning signs:**
- Continuous notifications every 60 seconds
- User disables/uninstalls app

**Prevention:**
- Track which thresholds have been alerted
- Only alert once per threshold crossing
- Reset tracking when usage drops below threshold or resets

**Phase:** Phase 3 (Alert implementation)

---

### 7. API Response Structure Changes
**Risk: Low**

The usage API is undocumented. Anthropic could change the response structure without notice.

**Warning signs:**
- KeyError when parsing response
- Missing expected fields

**Prevention:**
- Defensive parsing with try/except
- Log unexpected response structures
- Fail gracefully (show "Unknown" in UI)

**Phase:** Phase 1 (API implementation)

---

### 8. Hardcoded Headers/User-Agent
**Risk: Low**

The API may require specific headers (like `anthropic-beta`). These could change.

**Warning signs:**
- 400 Bad Request
- API returns unexpected errors

**Prevention:**
- Keep headers configurable or easy to update
- Log full request/response on errors for debugging

**Phase:** Phase 1 (API implementation)

---

## Minor Pitfalls

### 9. Icon Visibility on Different Themes
**Risk: Low**

Icon colors that work on dark themes may be invisible on light themes.

**Prevention:**
- Use symbolic icons that adapt to theme
- Or provide both light and dark variants

**Phase:** Phase 2 (Tray implementation)

---

### 10. Config File Permissions
**Risk: Low**

Config file in `~/.config/` could have wrong permissions if created incorrectly.

**Prevention:**
- Use standard config library (e.g., `appdirs`)
- Set appropriate permissions (600 for files with tokens)

**Phase:** Phase 4 (Polish)

---

## Summary Table

| Pitfall | Risk | Phase | Prevention |
|---------|------|-------|------------|
| GNOME tray removal | High | 2 | Document extension requirement, detect on startup |
| Token expiration | Medium | 1 | Implement refresh or prompt re-auth |
| Credentials missing | Low | 1 | Graceful error, clear message |
| API rate limiting | Low | 1 | 60s default interval, backoff |
| GTK thread safety | Medium | 2 | Use GLib.timeout_add_seconds() |
| Notification spam | Medium | 3 | Track alerted thresholds |
| API changes | Low | 1 | Defensive parsing |
| Hardcoded headers | Low | 1 | Keep configurable |
| Icon visibility | Low | 2 | Use symbolic icons |
| Config permissions | Low | 4 | Use standard paths, set permissions |

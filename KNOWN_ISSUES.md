# Known Issues and Limitations

## 1. Hover Tooltip Not Displayed (GNOME Shell)

**Issue:** When hovering over the tray icon, no tooltip appears.

**Root Cause:** This is a **known limitation** of AppIndicator on GNOME Shell. The AppIndicator/StatusNotifierItem specification does not support hover tooltips in GNOME Shell's implementation, unlike the legacy StatusIcon system.

**Affected Environments:**
- GNOME Shell with "AppIndicator and KStatusNotifierItem Support" extension
- Most Ubuntu and Fedora default desktop configurations

**Workaround:**
The application displays usage information in two alternative ways:
1. **Panel Label**: Compact status appears as text next to the icon (e.g., "45%|67%")
2. **Menu**: Click the icon to see full details including:
   - Session usage percentage (5-hour window)
   - Weekly usage percentage (7-day window)
   - Time until reset

**Technical Details:**
- `set_title()` is called for accessibility (screen readers) but doesn't display as tooltip on GNOME
- `set_label()` displays text in the panel, which works on GNOME Shell
- The menu provides the most detailed information

**Status:** Cannot be fixed - architectural limitation of GNOME Shell's AppIndicator implementation.

---

## 2. Tray Icon Not Visible Without Extension

**Issue:** The tray icon doesn't appear at all.

**Root Cause:** GNOME Shell removed legacy system tray support in version 3.26. AppIndicators require a GNOME Shell extension.

**Solution:** Install the "AppIndicator and KStatusNotifierItem Support" extension:
```bash
# Via GNOME Extensions website (recommended)
# Visit: https://extensions.gnome.org/extension/615/appindicator-support/

# Or via package manager (Ubuntu)
sudo apt install gnome-shell-extension-appindicator
```

**Verification:** After installing, you may need to log out and back in, or restart GNOME Shell (Alt+F2, type "r", press Enter).

---

## Future Improvements

Potential enhancements that could address these limitations:

1. **Alternative Display Modes**: Add option to use native GNOME notifications or a desktop widget
2. **Expanded Panel Label**: Make label format configurable (show session only, weekly only, or both)
3. **Desktop Environment Detection**: Automatically adapt display strategy based on DE

---

## Reporting Issues

If you encounter issues not listed here, please report them with:
- Your Linux distribution and version
- GNOME Shell version (`gnome-shell --version`)
- Whether AppIndicator extension is installed and active
- Console output when running `python3 main.py`

# Phase 2: System Tray & Display - Research

**Researched:** 2026-02-04
**Domain:** GTK3 AppIndicator3 system tray with Cairo-drawn dynamic icons
**Confidence:** HIGH

## Summary

Phase 2 implements a GNOME system tray application using PyGObject with AppIndicator3 for the tray icon and GTK3 for the menu. The icon will be dynamically generated using Cairo to draw a circular gauge showing session usage percentage. AppIndicator3 requires the "AppIndicator and KStatusNotifierItem Support" GNOME extension to display tray icons, as GNOME Shell removed legacy tray support in version 3.26.

The technical approach involves generating PNG icons in memory using Cairo's ImageSurface, saving them to temporary files (AppIndicator3 requires file paths, not in-memory buffers), and using GLib.timeout_add_seconds for periodic updates in a thread-safe manner. The menu displays usage percentages with GTK3 MenuItems, and tooltips show brief summaries.

**Primary recommendation:** Use AppIndicator3.Indicator with Cairo-generated icons saved to /tmp, GTK3.Menu for display, and GLib.timeout_add_seconds for periodic polling. Generate new icon files for each color state change.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyGObject | 3.46+ | GTK/GLib bindings for Python | Official Python bindings for GTK3, mature and well-documented |
| AppIndicator3 | 0.1 | System tray integration | Standard for GNOME/Ubuntu system tray apps, KStatusNotifierItem protocol |
| Cairo | via PyGObject | 2D vector graphics for icon rendering | Industry standard 2D graphics library, integrated with GTK |
| GLib | via PyGObject | Main loop, timers, threading primitives | Core event loop for all GTK applications |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| humanize | 4.0+ | Relative time formatting | Format "Resets in 2h 15m" strings from datetime |
| io.BytesIO | stdlib | In-memory file buffer | Intermediate step for Cairo PNG generation |
| tempfile | stdlib | Temporary file creation | Store generated icon PNGs for AppIndicator3 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AppIndicator3 | Gtk.StatusIcon | StatusIcon deprecated in GTK 3.14, not recommended |
| Cairo rendering | Pre-made SVG icons | Cairo allows dynamic percentage-based gauge, SVG would need 100+ files |
| GLib.timeout_add_seconds | threading.Timer | GLib is thread-safe with GTK main loop, threading.Timer is not |

**Installation:**
```bash
# System packages (Debian/Ubuntu)
sudo apt install python3-gi gir1.2-appindicator3-0.1 libnotify-bin

# Python packages
pip install humanize
```

**Note:** GNOME users must install "AppIndicator and KStatusNotifierItem Support" extension from extensions.gnome.org/extension/615/

## Architecture Patterns

### Recommended Project Structure
```
src/
├── __init__.py
├── config.py          # (Phase 1 - already exists)
├── api.py             # (Phase 1 - already exists)
├── tray.py            # TrayIndicator class - manages AppIndicator3
├── icon_generator.py  # IconGenerator class - Cairo rendering
└── utils.py           # Time formatting helpers (humanize wrapper)
```

### Pattern 1: AppIndicator3 with Dynamic Icons
**What:** Create indicator, generate icon files dynamically, update via set_icon_full()
**When to use:** Need to show changing visual state in tray icon

**Example:**
```python
# Based on official tutorials and documentation
import gi
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
from gi.repository import AppIndicator3, Gtk

# Create indicator with initial icon
indicator = AppIndicator3.Indicator.new(
    'claude-usage-overlay',
    '/tmp/claude-usage-icon.png',  # Absolute path to icon file
    AppIndicator3.IndicatorCategory.APPLICATION_STATUS
)

# Set status to ACTIVE (required for display)
indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

# Create and attach menu (required for display)
menu = Gtk.Menu()
# ... add menu items ...
menu.show_all()  # MUST call show_all() before set_menu()
indicator.set_menu(menu)

# Update icon dynamically
indicator.set_icon_full('/tmp/claude-usage-icon-updated.png', 'Usage icon')

# Set tooltip
indicator.set_title('Session: 36% | Weekly: 77%')  # Acts as tooltip
```

### Pattern 2: Cairo Circular Gauge Generation
**What:** Draw circular progress ring showing percentage fill
**When to use:** Creating gauge-style visualizations

**Example:**
```python
# Based on Cairo documentation and community examples
import cairo
import math

def generate_gauge_icon(percentage, size=22):
    """Generate circular gauge icon with Cairo."""
    # Create surface
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surface)

    # Setup
    center_x = center_y = size / 2
    radius = (size - 4) / 2  # Leave 2px margin

    # Clear background (transparent)
    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.paint()

    # Draw gray outline circle
    ctx.set_source_rgb(0.5, 0.5, 0.5)  # Cairo uses 0-1, not 0-255
    ctx.set_line_width(2)
    ctx.arc(center_x, center_y, radius, 0, 2 * math.pi)
    ctx.stroke()

    # Draw colored fill arc (percentage)
    # Cairo arcs use radians, starting from 3 o'clock, clockwise
    # Start at -90 degrees (12 o'clock) = -math.pi/2 radians
    start_angle = -math.pi / 2
    end_angle = start_angle + (2 * math.pi * percentage / 100)

    color = get_color_for_percentage(percentage)
    ctx.set_source_rgb(*color)
    ctx.set_line_width(2)
    ctx.arc(center_x, center_y, radius, start_angle, end_angle)
    ctx.stroke()

    # Save to file (AppIndicator3 requires file path)
    icon_path = '/tmp/claude-usage-icon.png'
    surface.write_to_png(icon_path)
    return icon_path
```

### Pattern 3: GTK3 Menu Construction
**What:** Build menu with items, separators, and callbacks
**When to use:** Creating AppIndicator3 dropdown menus

**Example:**
```python
# Based on GTK3 documentation and tutorials
from gi.repository import Gtk

def create_menu(usage_data):
    """Create menu showing usage details."""
    menu = Gtk.Menu()

    # Usage display (non-clickable label)
    usage_item = Gtk.MenuItem.new_with_label(
        f"Session: {usage_data.session_percent:.0f}%  |  Weekly: {usage_data.weekly_percent:.0f}%"
    )
    usage_item.set_sensitive(False)  # Make it non-clickable
    menu.append(usage_item)

    # Reset time display
    reset_time = format_time_until(usage_data.session_resets_at)
    reset_item = Gtk.MenuItem.new_with_label(f"Resets in {reset_time}")
    reset_item.set_sensitive(False)
    menu.append(reset_item)

    # Separator
    menu.append(Gtk.SeparatorMenuItem())

    # Refresh action
    refresh_item = Gtk.MenuItem.new_with_label('Refresh')
    refresh_item.connect('activate', on_refresh_clicked)
    menu.append(refresh_item)

    # Settings placeholder
    settings_item = Gtk.MenuItem.new_with_label('Settings')
    settings_item.set_sensitive(False)  # Disabled until Phase 4
    menu.append(settings_item)

    # Separator
    menu.append(Gtk.SeparatorMenuItem())

    # Quit
    quit_item = Gtk.MenuItem.new_with_label('Quit')
    quit_item.connect('activate', Gtk.main_quit)
    menu.append(quit_item)

    menu.show_all()  # CRITICAL: Must call before set_menu()
    return menu
```

### Pattern 4: Thread-Safe Periodic Updates
**What:** Update UI from timer callback without threading issues
**When to use:** Polling API and updating GTK widgets periodically

**Example:**
```python
# Based on PyGObject threading documentation
from gi.repository import GLib

def update_usage(indicator):
    """Update usage data and refresh UI. Called by GLib timer."""
    try:
        # Fetch new data (already exists from Phase 1)
        from src.config import get_access_token
        from src.api import fetch_with_retry

        token = get_access_token()
        usage = fetch_with_retry(token)

        # Update icon
        icon_path = generate_gauge_icon(usage.session_percent)
        indicator.set_icon_full(icon_path, 'Usage icon')

        # Update tooltip
        tooltip = f"Session: {usage.session_percent:.0f}% | Weekly: {usage.weekly_percent:.0f}%"
        indicator.set_title(tooltip)

        # Rebuild menu
        menu = create_menu(usage)
        indicator.set_menu(menu)

    except Exception as e:
        print(f"Update failed: {e}", file=sys.stderr)

    return GLib.SOURCE_CONTINUE  # Keep timer running

# Start periodic updates (every 5 minutes = 300 seconds)
GLib.timeout_add_seconds(300, update_usage, indicator)

# Start GTK main loop
Gtk.main()
```

### Anti-Patterns to Avoid
- **Creating indicator without menu:** AppIndicator will not display unless set_status(ACTIVE) AND set_menu() are both called
- **Forgetting menu.show_all():** Menu items won't appear unless show_all() is called before set_menu()
- **Using relative icon paths:** AppIndicator3 requires absolute paths for custom icons
- **Using set_icon() instead of set_icon_full():** set_icon() is deprecated, use set_icon_full(icon_path, description)
- **Updating UI from threads:** Use GLib.idle_add() or GLib.timeout_add_seconds() for thread-safe updates, never call GTK methods directly from threads
- **RGB colors as 0-255:** Cairo expects 0.0-1.0, must divide by 255

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative time formatting | Manual timedelta string formatting | humanize.naturaldelta() or humanize.naturaltime() | Handles edge cases (singular/plural, different time units), localization support |
| Thread-safe GTK updates | threading.Timer + manual locking | GLib.timeout_add_seconds() | GTK main loop integration, automatic thread safety, guaranteed execution on main thread |
| Temporary file management | Manual /tmp path generation | tempfile.NamedTemporaryFile() | Automatic cleanup, secure random naming, proper permissions, cross-platform |
| Radians conversion | Manual math.pi multiplication | math.radians() and math.degrees() | Standard library functions, clearer intent, less error-prone |

**Key insight:** GTK/GLib ecosystem has mature solutions for all common GUI patterns. Using GLib primitives ensures proper integration with the main loop and prevents threading bugs.

## Common Pitfalls

### Pitfall 1: AppIndicator Not Appearing
**What goes wrong:** Indicator created but nothing shows in system tray
**Why it happens:**
- GNOME extension not installed
- Missing set_status(ACTIVE) call
- Missing set_menu() call
- Menu doesn't have show_all() called

**How to avoid:**
1. Check extension installed: `gnome-extensions list | grep appindicator`
2. Always call both `set_status(ACTIVE)` and `set_menu(menu)` after creating indicator
3. Always call `menu.show_all()` before `set_menu()`

**Warning signs:** No error messages, app runs but tray is empty

### Pitfall 2: Icon Not Updating
**What goes wrong:** Icon changes not visible in tray
**Why it happens:**
- Using same filename (system caches icon by path)
- Icon path not absolute
- set_icon() called instead of set_icon_full()

**How to avoid:**
- Use unique filenames for each state OR overwrite file and use set_icon_theme_path() to bust cache
- Always use absolute paths: `os.path.abspath(icon_path)`
- Use set_icon_full() with description parameter

**Warning signs:** Icon never changes even though code runs

### Pitfall 3: Menu Items Not Visible
**What goes wrong:** Menu items added but don't appear when clicking icon
**Why it happens:** Forgot to call show_all() on menu or individual items

**How to avoid:**
- ALWAYS call `menu.show_all()` after adding all items and before `set_menu()`
- For dynamically added items, call `item.show()` or rebuild and show_all()

**Warning signs:** Empty menu or missing menu items

### Pitfall 4: GTK Thread Safety Violations
**What goes wrong:** Random crashes, "GTK accessed from non-main thread" errors
**Why it happens:** Calling GTK methods from background threads

**How to avoid:**
- Never call GTK/AppIndicator methods from threads
- Use GLib.idle_add() to schedule UI updates from callbacks
- Use GLib.timeout_add_seconds() for periodic updates

**Warning signs:** Intermittent crashes, warnings about thread safety

### Pitfall 5: Cairo Angle Confusion
**What goes wrong:** Arc drawn in wrong position or direction
**Why it happens:**
- Cairo uses radians, not degrees
- Cairo starts at 3 o'clock (0 radians), not 12 o'clock
- Positive angles go clockwise in default coordinate system

**How to avoid:**
- Use math.radians() to convert degrees
- Start angle at -math.pi/2 for 12 o'clock position
- Remember: 0° = 3 o'clock, 90° = 6 o'clock, 180° = 9 o'clock, 270° = 12 o'clock

**Warning signs:** Gauge appears rotated 90° from expected

## Code Examples

Verified patterns from official sources:

### Complete AppIndicator3 Setup
```python
# Source: http://candidtim.github.io/appindicator/2014/09/13/ubuntu-appindicator-step-by-step.html
import gi
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
from gi.repository import AppIndicator3, Gtk

APPINDICATOR_ID = 'claude-usage-overlay'

def main():
    # Create indicator
    indicator = AppIndicator3.Indicator.new(
        APPINDICATOR_ID,
        '/path/to/icon.png',  # Must be absolute path
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    # Create menu
    menu = Gtk.Menu()
    item = Gtk.MenuItem.new_with_label('Example Item')
    item.connect('activate', on_item_clicked)
    menu.append(item)
    menu.show_all()

    # Attach menu
    indicator.set_menu(menu)

    # Set tooltip (uses set_title)
    indicator.set_title('Tooltip text here')

    # Start main loop
    Gtk.main()

if __name__ == "__main__":
    main()
```

### Cairo Color Conversion Helper
```python
# Source: Cairo color format documentation
def rgb_to_cairo(r, g, b):
    """Convert RGB 0-255 to Cairo 0.0-1.0 format.

    Args:
        r, g, b: Color values in 0-255 range

    Returns:
        tuple: (r, g, b) in 0.0-1.0 range
    """
    return (r / 255.0, g / 255.0, b / 255.0)

# Usage
GREEN = rgb_to_cairo(0, 191, 255)  # Cyan
ctx.set_source_rgb(*GREEN)
```

### Humanize Time Formatting
```python
# Source: https://python-humanize.readthedocs.io/en/latest/time/
from datetime import datetime, timezone
import humanize

def format_time_until(reset_time):
    """Format time until reset in human-readable format.

    Args:
        reset_time: datetime object (timezone-aware)

    Returns:
        str: e.g., "2 hours, 15 minutes"
    """
    if reset_time is None:
        return "Unknown"

    now = datetime.now(timezone.utc)
    delta = reset_time - now

    # naturaldelta returns "2 hours" or "15 minutes" without "in" prefix
    return humanize.naturaldelta(delta)
```

### GLib Timer with Return Values
```python
# Source: https://docs.gtk.org/glib/func.timeout_add_seconds.html
from gi.repository import GLib

def periodic_callback():
    """Called every N seconds by GLib timer."""
    print("Callback executed")

    # Return GLib.SOURCE_CONTINUE to keep timer running
    # Return GLib.SOURCE_REMOVE to stop timer
    return GLib.SOURCE_CONTINUE

# Add timer (every 60 seconds)
timer_id = GLib.timeout_add_seconds(60, periodic_callback)

# To manually remove timer later:
# GLib.source_remove(timer_id)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Gtk.StatusIcon | AppIndicator3 | GTK 3.14 (2014) | StatusIcon deprecated, AppIndicator is standard for system tray |
| Direct threading.Thread | GLib.timeout_add_seconds() | Always in GTK | Proper main loop integration, thread safety |
| set_icon() | set_icon_full() | AppIndicator3 0.1 | set_icon() deprecated, must provide icon description |
| SVG icon files | Cairo dynamic rendering | N/A - use case specific | Dynamic icons need runtime generation |

**Deprecated/outdated:**
- **Gtk.StatusIcon**: Deprecated in GTK 3.14, not recommended. Use AppIndicator3 instead.
- **AppIndicator3.Indicator.set_icon()**: Deprecated. Use set_icon_full(icon_name, icon_desc) instead.
- **pynotify**: Old notification library. Use gi.repository.Notify (GObject Introspection) instead.

## Open Questions

Things that couldn't be fully resolved:

1. **Icon size standardization**
   - What we know: AppIndicator icons typically 16px-22px depending on GNOME theme
   - What's unclear: Exact pixel size preference varies by system/theme/extension version
   - Recommendation: Generate 22px icons (standard from Unity days), test on target system, make configurable in Phase 4

2. **Icon caching behavior**
   - What we know: AppIndicator may cache icons by filename
   - What's unclear: Exact caching mechanism varies by implementation
   - Recommendation: Use unique filenames per state OR use set_icon_theme_path() after updating file

3. **Tooltip vs Title behavior**
   - What we know: set_title() shows on hover in some implementations
   - What's unclear: Not all AppIndicator implementations support tooltips consistently
   - Recommendation: Use set_title() for tooltip text, test on target GNOME version

4. **Menu item sensitivity for labels**
   - What we know: set_sensitive(False) makes items non-clickable
   - What's unclear: Visual styling (grayed out vs normal) may vary by theme
   - Recommendation: Test appearance, may need custom styling in Phase 4

## Sources

### Primary (HIGH confidence)
- [AppIndicator3 step-by-step tutorial](http://candidtim.github.io/appindicator/2014/09/13/ubuntu-appindicator-step-by-step.html) - Complete working example
- [GLib.timeout_add_seconds documentation](https://docs.gtk.org/glib/func.timeout_add_seconds.html) - Official API docs
- [Cairo arc documentation](https://www.cairographics.org/samples/arc/) - Official Cairo samples
- [GTK3 SeparatorMenuItem](https://docs.gtk.org/gtk3/class.SeparatorMenuItem.html) - Official GTK docs
- [Pycairo surfaces documentation](https://pycairo.readthedocs.io/en/latest/reference/surfaces.html) - Official Pycairo docs
- [Humanize time documentation](https://python-humanize.readthedocs.io/en/latest/time/) - Official package docs

### Secondary (MEDIUM confidence)
- [AppIndicator3 custom icons blog](https://zderadicka.eu/appindicator3-how-to-use-custom-icons/) - Verified approach for icon paths
- [Python GTK3 tutorial: Menus](https://python-gtk-3-tutorial.readthedocs.io/en/latest/menus.html) - Menu construction patterns
- [PyGObject threading guide](https://pygobject.readthedocs.io/en/latest/guide/threading.html) - Thread safety best practices
- [Drawing with Cairo in PyGTK](https://zetcode.com/gui/pygtk/drawing/) - Cairo drawing examples

### Tertiary (LOW confidence - verify in testing)
- [AppIndicator icon size discussions](https://github.com/ubuntu/gnome-shell-extension-appindicator/issues/112) - Community debate on sizing
- [GNOME extension page](https://extensions.gnome.org/extension/615/appindicator-support/) - Extension requirement

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyGObject/AppIndicator3/Cairo are industry standard, well-documented
- Architecture: HIGH - Patterns verified from official tutorials and documentation
- Pitfalls: HIGH - Common issues documented in forums, GitHub issues, and tutorials

**Research date:** 2026-02-04
**Valid until:** ~30 days (stable stack, but GNOME extension compatibility may change)

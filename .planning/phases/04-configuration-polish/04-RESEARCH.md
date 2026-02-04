# Phase 4: Configuration & Polish - Research

**Researched:** 2026-02-04
**Domain:** Python desktop application configuration management and Linux desktop integration
**Confidence:** HIGH

## Summary

Phase 4 adds user-configurable settings and desktop integration to the Claude Code usage monitor. Research focused on configuration file formats, XDG standards, keyboard shortcut handling, and Linux autostart mechanisms for Python GTK applications.

**Configuration Storage:** For this application, JSON with Python dataclasses provides the optimal balance. GSettings requires schema installation to system directories (overkill for single-user utility), while Pydantic adds external dependency. Standard library JSON with dataclass validation provides type safety without complexity.

**XDG Compliance:** User configuration belongs in `~/.config/claude-usage-overlay/config.json` per XDG Base Directory spec. This location is standard, portable across distros, and user-specific (no root/sudo required).

**Autostart:** XDG autostart via `.desktop` file in `~/.config/autostart/` is the universal mechanism supported by GNOME, KDE, XFCE, and others. No daemon registration or systemd unit needed.

**Keyboard Shortcuts:** GTK menu accelerators (Ctrl+R, etc.) work within the application menu. True global hotkeys require external library (keybinder-3.0) which is unmaintained since 2017. For system tray app, menu-based shortcuts are sufficient and conflict-free.

**Primary recommendation:** Use JSON configuration with Python dataclasses for validation, store in XDG_CONFIG_HOME, implement file watching for live reload, provide menu-based shortcuts instead of global hotkeys.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| json (stdlib) | 3.11+ | Configuration serialization | Built-in, simple, human-readable |
| dataclasses (stdlib) | 3.11+ | Configuration validation | Type safety without external deps |
| pathlib (stdlib) | 3.11+ | File path handling | XDG-compliant path construction |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| GLib.timeout_add | via PyGObject | Dynamic polling interval | Recreate timer when config changes |
| watchdog | 3.0+ (optional) | File watching for config reload | Auto-reload on external edits |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON + dataclass | GSettings + dconf | GSettings requires schema installation, system-wide setup. Overkill for single-user utility. Better for multi-app integration. |
| JSON + dataclass | Pydantic BaseSettings | Pydantic adds external dependency for minimal gain. BaseSettings designed for env vars, not simple JSON files. |
| JSON | TOML | TOML better for complex hierarchies. This app has flat config. JSON more familiar, stdlib only. |
| Menu accelerators | keybinder-3.0 global hotkeys | Global hotkeys work when app unfocused, but keybinder unmaintained since 2017, X11-only, adds complexity. Menu shortcuts sufficient. |

**Installation:**
```bash
# No additional dependencies needed - uses stdlib only
# Optional file watching:
pip install watchdog
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── config.py           # Existing: OAuth credentials + NEW: UserConfig dataclass
├── tray.py             # Modified: Load config, wire up keyboard shortcuts
├── notifier.py         # Modified: Respect pause_notifications flag
└── main.py             # Entry point (unchanged)

~/.config/claude-usage-overlay/
└── config.json         # User configuration file

~/.config/autostart/
└── claude-usage-overlay.desktop  # XDG autostart entry
```

### Pattern 1: Dataclass-Based Configuration with Validation

**What:** Define configuration schema as Python dataclass with defaults, load from JSON, validate on load.

**When to use:** Simple configuration (< 20 fields), flat or shallow hierarchy, no need for system-wide settings.

**Example:**
```python
# Source: Python stdlib docs + dataclasses best practices
from dataclasses import dataclass, asdict
from pathlib import Path
import json

@dataclass
class UserConfig:
    """User-configurable settings."""
    # Thresholds per metric (percentages)
    session_thresholds: list[int] = None
    weekly_thresholds: list[int] = None

    # Polling interval (seconds)
    polling_interval: int = 300  # 5 minutes default

    # Pause notifications mode
    pause_notifications: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Set defaults if None
        if self.session_thresholds is None:
            self.session_thresholds = [50, 75, 90]
        if self.weekly_thresholds is None:
            self.weekly_thresholds = [50, 75, 90]

        # Validate thresholds
        for threshold in self.session_thresholds + self.weekly_thresholds:
            if not 0 <= threshold <= 100:
                raise ValueError(f"Threshold must be 0-100, got {threshold}")

        # Validate polling interval (min 30s, max 1 hour)
        if not 30 <= self.polling_interval <= 3600:
            raise ValueError(f"Polling interval must be 30-3600s, got {self.polling_interval}")

    @classmethod
    def load(cls, config_path: Path) -> 'UserConfig':
        """Load configuration from JSON file."""
        if not config_path.exists():
            # Return defaults if no config file
            return cls()

        with open(config_path, 'r') as f:
            data = json.load(f)

        return cls(**data)

    def save(self, config_path: Path):
        """Save configuration to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
```

### Pattern 2: XDG Base Directory Compliance

**What:** Store config in `~/.config/<app-name>/`, cache in `~/.cache/<app-name>/`, respect XDG_CONFIG_HOME env var.

**When to use:** All Linux desktop applications.

**Example:**
```python
# Source: https://wiki.archlinux.org/title/XDG_Base_Directory
import os
from pathlib import Path

def get_config_dir() -> Path:
    """Get XDG-compliant config directory."""
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config_home:
        base = Path(xdg_config_home)
    else:
        base = Path.home() / '.config'

    app_config_dir = base / 'claude-usage-overlay'
    app_config_dir.mkdir(parents=True, exist_ok=True)
    return app_config_dir

def get_config_path() -> Path:
    """Get path to user configuration file."""
    return get_config_dir() / 'config.json'
```

### Pattern 3: Dynamic Timer Interval Update

**What:** Replace GLib timeout when polling interval changes (can't modify existing timeout).

**When to use:** User-configurable timer intervals in GTK apps.

**Example:**
```python
# Source: https://docs.gtk.org/glib/func.timeout_add_seconds.html
from gi.repository import GLib

class TrayIndicator:
    def __init__(self):
        self.timer_id = None
        self.polling_interval = 300
        self._start_timer()

    def _start_timer(self):
        """Start or restart the update timer."""
        # Remove old timer if exists
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)

        # Add new timer with current interval
        self.timer_id = GLib.timeout_add_seconds(
            self.polling_interval,
            self._update_usage
        )

    def update_polling_interval(self, new_interval: int):
        """Change polling interval and restart timer."""
        self.polling_interval = new_interval
        self._start_timer()
```

### Pattern 4: XDG Autostart Desktop Entry

**What:** Create `.desktop` file in `~/.config/autostart/` for login autostart.

**When to use:** Applications that should start automatically on user login.

**Example:**
```desktop
# Source: https://specifications.freedesktop.org/autostart/latest/
[Desktop Entry]
Type=Application
Name=Claude Code Usage Monitor
Comment=Monitor Claude Code token usage in system tray
Exec=/usr/bin/python3 /path/to/overlay-CC-usage/src/main.py
Icon=dialog-information
Terminal=false
Categories=Utility;Monitor;
StartupNotify=false
X-GNOME-Autostart-enabled=true
```

### Pattern 5: GTK Menu Accelerators (Keyboard Shortcuts)

**What:** Add keyboard shortcuts to menu items using Gtk.AccelGroup and MenuItem.add_accelerator().

**When to use:** In-app shortcuts (active when app has focus or menu is open).

**Example:**
```python
# Source: https://python-gtk-3-tutorial.readthedocs.io/en/latest/menus.html
from gi.repository import Gtk, Gdk

def build_menu(self):
    """Build menu with keyboard shortcuts."""
    menu = Gtk.Menu()

    # Create accelerator group
    accel_group = Gtk.AccelGroup()

    # Add Refresh item with Ctrl+R shortcut
    refresh_item = Gtk.MenuItem(label="Refresh")
    refresh_item.connect('activate', self._on_refresh_clicked)
    refresh_item.add_accelerator(
        "activate",
        accel_group,
        Gdk.KEY_r,                    # 'r' key
        Gdk.ModifierType.CONTROL_MASK, # Ctrl modifier
        Gtk.AccelFlags.VISIBLE
    )
    menu.append(refresh_item)

    # Note: AccelGroup must be kept alive and added to window
    # For system tray, accelerators work when menu is active
    self.accel_group = accel_group

    menu.show_all()
    return menu
```

### Anti-Patterns to Avoid

- **Hardcoding config paths:** Always use XDG_CONFIG_HOME with fallback to `~/.config`, never hardcode `/home/username/`.
- **Mutating default lists in dataclass:** Use `None` as default and set in `__post_init__`, never `field(default_factory=list)` as class attribute without factory.
- **Validating in setter only:** Validate in `__post_init__` so invalid JSON files are caught on load, not just on manual edits.
- **Global hotkeys without fallback:** keybinder-3.0 is unmaintained and X11-only. Wayland doesn't support global hotkeys without compositor cooperation. Menu accelerators are portable.
- **Modifying timer in-place:** GLib timeouts can't be modified. Always remove old and add new.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Configuration validation | Manual type checks | dataclass with `__post_init__` | Automatic type checking, IDE support, less code |
| Config file location | `~/.my-app-config` | XDG Base Directory spec | Standard across all Linux apps, respects user overrides |
| Desktop autostart | systemd user unit | XDG autostart .desktop file | Simpler, desktop-agnostic, no daemon registration |
| Global keyboard shortcuts | Custom X11 binding | keybinder-3.0 OR menu accelerators | X11 complexity, security implications. Menu accelerators work everywhere. |
| File watching for config reload | Polling with mtime check | watchdog library (optional) | Handles edge cases (atomic writes, renames), efficient |
| JSON schema validation | if/else chains | dataclass validation | Type hints work, fewer bugs, self-documenting |

**Key insight:** Linux desktop has mature standards (XDG, freedesktop.org specs). Using these standards means your app works correctly on Fedora, Ubuntu, Arch, with GNOME, KDE, XFCE. Custom solutions break on some combination.

## Common Pitfalls

### Pitfall 1: Ignoring XDG_CONFIG_HOME Environment Variable

**What goes wrong:** Hardcoding `~/.config` breaks for users who set `XDG_CONFIG_HOME` to custom location (e.g., NixOS, some corporate setups).

**Why it happens:** Developers test with default setup where `~/.config` works.

**How to avoid:** Always check `os.environ.get('XDG_CONFIG_HOME')` first, use `~/.config` as fallback only.

**Warning signs:** Bug reports from NixOS or advanced users saying "config not found."

### Pitfall 2: TryExec Path Issues in .desktop File

**What goes wrong:** Autostart .desktop file with wrong `TryExec` path silently fails to start (no error message).

**Why it happens:** Installed Python script path differs from development path. User installs to venv or system path but .desktop has hardcoded dev path.

**How to avoid:** Use absolute path in `Exec=` that matches actual installation. For development, use `python3 -m src.main` from project directory. For production, install with setuptools and use installed script path.

**Warning signs:** App doesn't autostart but manually running works fine.

### Pitfall 3: Mutable Default Arguments in Dataclass

**What goes wrong:** Using `field(default_factory=list)` incorrectly or `list[int] = [50, 75, 90]` as class attribute causes shared mutable state between instances.

**Why it happens:** Python's mutable default trap - same list object shared across instances.

**How to avoid:** Use `None` as default, set actual list in `__post_init__`:
```python
session_thresholds: list[int] = None

def __post_init__(self):
    if self.session_thresholds is None:
        self.session_thresholds = [50, 75, 90]
```

**Warning signs:** Modifying config in one instance affects another, or default values "stick" between loads.

### Pitfall 4: Not Validating Configuration Early

**What goes wrong:** Invalid config loaded, app crashes later during usage (e.g., threshold 150% causes notification logic to fail).

**Why it happens:** Validation deferred to usage site instead of load time.

**How to avoid:** Validate everything in `__post_init__` immediately after loading JSON. Fail fast with clear error message.

**Warning signs:** Crashes deep in application logic with confusing errors like "percentage > 100."

### Pitfall 5: Timer Keeps Old Interval After Config Change

**What goes wrong:** User changes polling interval to 60s, but app keeps polling every 300s. Config saved but not applied.

**Why it happens:** GLib timeout can't be modified in-place. Must remove old timer and add new one.

**How to avoid:** Always call `GLib.source_remove(old_timer_id)` before creating new timer with new interval.

**Warning signs:** Config file shows new value, but behavior unchanged until restart.

### Pitfall 6: Leaking Sensitive Data in Error Messages

**What goes wrong:** Validation error shows entire config including OAuth tokens if they were stored in user config.

**Why it happens:** Generic error messages include repr(config) for debugging.

**How to avoid:** Never store OAuth tokens in user config (already separate in `~/.claude/.credentials.json`). For error messages, show only the invalid field: `f"Invalid threshold: {threshold}"` not `f"Invalid config: {config}"`.

**Warning signs:** OAuth tokens appear in terminal output or log files.

### Pitfall 7: Desktop File Doesn't Match Installed Path

**What goes wrong:** Created autostart .desktop but `Exec=` path wrong, app doesn't start on login. No error shown.

**Why it happens:** Developed with `python3 /home/dev/project/main.py`, but installed to `/usr/local/bin/claude-usage-monitor`. Desktop file still has old path.

**How to avoid:**
- Development: Use absolute path to project OR install with `pip install -e .` and use installed command
- Production: Generate .desktop file during install with correct path
- Use `TryExec=` to fail gracefully if path wrong

**Warning signs:** Manual launch works, autostart silently fails. Check `journalctl --user` for systemd-xdg-autostart-generator errors.

## Code Examples

Verified patterns from official sources:

### Configuration Loading with Validation

```python
# Source: Python dataclasses stdlib + XDG spec
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os

def get_config_path() -> Path:
    """Get XDG-compliant config file path."""
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    base = Path(xdg_config_home) if xdg_config_home else Path.home() / '.config'
    config_dir = base / 'claude-usage-overlay'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'config.json'

@dataclass
class UserConfig:
    """User-configurable settings for Claude Code usage monitor."""
    session_thresholds: list[int] = None
    weekly_thresholds: list[int] = None
    polling_interval: int = 300  # seconds
    pause_notifications: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Set defaults for mutable fields
        if self.session_thresholds is None:
            self.session_thresholds = [50, 75, 90]
        if self.weekly_thresholds is None:
            self.weekly_thresholds = [50, 75, 90]

        # Validate thresholds (0-100%)
        all_thresholds = self.session_thresholds + self.weekly_thresholds
        for threshold in all_thresholds:
            if not isinstance(threshold, int) or not 0 <= threshold <= 100:
                raise ValueError(
                    f"Threshold must be integer 0-100, got {threshold}"
                )

        # Validate polling interval (30s to 1 hour)
        if not isinstance(self.polling_interval, int):
            raise ValueError(
                f"polling_interval must be integer, got {type(self.polling_interval)}"
            )
        if not 30 <= self.polling_interval <= 3600:
            raise ValueError(
                f"polling_interval must be 30-3600 seconds, got {self.polling_interval}"
            )

        # Validate pause_notifications is bool
        if not isinstance(self.pause_notifications, bool):
            raise ValueError(
                f"pause_notifications must be boolean, got {type(self.pause_notifications)}"
            )

    @classmethod
    def load(cls) -> 'UserConfig':
        """Load configuration from XDG config file.

        Returns:
            UserConfig instance with loaded settings or defaults
        """
        config_path = get_config_path()

        if not config_path.exists():
            # No config file - return defaults
            return cls()

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)

            return cls(**data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except TypeError as e:
            raise ValueError(f"Invalid config structure: {e}")

    def save(self):
        """Save configuration to XDG config file."""
        config_path = get_config_path()

        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
```

### XDG Autostart Desktop File Creation

```python
# Source: https://specifications.freedesktop.org/autostart/latest/
import os
from pathlib import Path

def get_autostart_path() -> Path:
    """Get XDG autostart directory path."""
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    base = Path(xdg_config_home) if xdg_config_home else Path.home() / '.config'
    autostart_dir = base / 'autostart'
    autostart_dir.mkdir(parents=True, exist_ok=True)
    return autostart_dir

def create_autostart_entry(enable: bool = True):
    """Create or update XDG autostart desktop entry.

    Args:
        enable: If True, create/enable autostart. If False, disable via Hidden=true.
    """
    autostart_path = get_autostart_path() / 'claude-usage-overlay.desktop'

    # Get absolute path to main.py
    # For installed package, use: exec_path = shutil.which('claude-usage-monitor')
    # For development:
    project_root = Path(__file__).parent.parent.absolute()
    exec_path = f"/usr/bin/python3 {project_root}/src/main.py"

    desktop_entry = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=Claude Code Usage Monitor
Comment=System tray monitor for Claude Code token usage
Exec={exec_path}
Icon=dialog-information
Terminal=false
Categories=Utility;Monitor;
StartupNotify=false
X-GNOME-Autostart-enabled=true
Hidden={'false' if enable else 'true'}
"""

    with open(autostart_path, 'w') as f:
        f.write(desktop_entry)

    # Make executable (some DEs check this)
    autostart_path.chmod(0o755)

def is_autostart_enabled() -> bool:
    """Check if autostart is currently enabled."""
    autostart_path = get_autostart_path() / 'claude-usage-overlay.desktop'

    if not autostart_path.exists():
        return False

    # Parse desktop file to check Hidden key
    with open(autostart_path, 'r') as f:
        content = f.read()

    # Simple parsing - look for Hidden=true
    for line in content.splitlines():
        if line.strip().startswith('Hidden='):
            value = line.split('=', 1)[1].strip().lower()
            return value != 'true'

    # No Hidden key means enabled
    return True
```

### Menu with Keyboard Shortcuts

```python
# Source: https://python-gtk-3-tutorial.readthedocs.io/en/latest/menus.html
from gi.repository import Gtk, Gdk

def _build_menu(self) -> Gtk.Menu:
    """Build menu with keyboard shortcuts."""
    menu = Gtk.Menu()

    # Create accelerator group for shortcuts
    # Note: For system tray, shortcuts only work when menu is open
    accel_group = Gtk.AccelGroup()

    # Usage info (non-clickable)
    usage_item = Gtk.MenuItem(label="Session: 45%  |  Weekly: 67%")
    usage_item.set_sensitive(False)
    menu.append(usage_item)

    menu.append(Gtk.SeparatorMenuItem())

    # Refresh with Ctrl+R shortcut
    refresh_item = Gtk.MenuItem(label="Refresh")
    refresh_item.connect('activate', self._on_refresh_clicked)
    refresh_item.add_accelerator(
        "activate",
        accel_group,
        Gdk.KEY_r,
        Gdk.ModifierType.CONTROL_MASK,
        Gtk.AccelFlags.VISIBLE
    )
    menu.append(refresh_item)

    # Settings with Ctrl+S shortcut
    settings_item = Gtk.MenuItem(label="Settings")
    settings_item.connect('activate', self._on_settings_clicked)
    settings_item.add_accelerator(
        "activate",
        accel_group,
        Gdk.KEY_s,
        Gdk.ModifierType.CONTROL_MASK,
        Gtk.AccelFlags.VISIBLE
    )
    menu.append(settings_item)

    menu.append(Gtk.SeparatorMenuItem())

    # Quit with Ctrl+Q shortcut
    quit_item = Gtk.MenuItem(label="Quit")
    quit_item.connect('activate', self._on_quit_clicked)
    quit_item.add_accelerator(
        "activate",
        accel_group,
        Gdk.KEY_q,
        Gdk.ModifierType.CONTROL_MASK,
        Gtk.AccelFlags.VISIBLE
    )
    menu.append(quit_item)

    menu.show_all()

    # Keep reference to accel_group so it's not garbage collected
    self.accel_group = accel_group

    return menu
```

### Dynamic Timer Interval Update

```python
# Source: https://docs.gtk.org/glib/func.timeout_add_seconds.html
from gi.repository import GLib

class TrayIndicator:
    def __init__(self):
        self.config = UserConfig.load()
        self.timer_id = None
        self._start_update_timer()

    def _start_update_timer(self):
        """Start or restart the periodic update timer."""
        # Remove existing timer if any
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

        # Create new timer with current config interval
        self.timer_id = GLib.timeout_add_seconds(
            self.config.polling_interval,
            self._update_usage
        )

    def reload_config(self):
        """Reload configuration and apply changes."""
        old_interval = self.config.polling_interval

        # Reload config from file
        self.config = UserConfig.load()

        # If interval changed, restart timer
        if self.config.polling_interval != old_interval:
            self._start_update_timer()

        # If pause_notifications changed, inform notifier
        self.notifier.pause_notifications = self.config.pause_notifications
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom config in `~/.app-name-rc` | XDG Base Directory (`~/.config/app-name/`) | ~2010, standardized 2015+ | Consistent location, respects user overrides |
| INI files with configparser | JSON/TOML with type validation | 2015+ | Type safety, better tooling, easier nesting |
| Manual validation in getters | Dataclass with `__post_init__` | Python 3.7+ (2018) | Fail-fast, less boilerplate, IDE support |
| keybinder for global hotkeys | Menu accelerators OR compositor protocols | 2017+ (Wayland) | keybinder unmaintained, X11-only. Wayland needs different approach. |
| GConf/GSettings for all apps | GSettings for system apps, JSON for user tools | ~2013+ | GSettings overkill for single-user utilities |

**Deprecated/outdated:**
- **GConf:** Replaced by GSettings/dconf in GNOME 3 (2011). Don't use for new applications.
- **keybinder-3.0:** Last release 2017, X11-only, doesn't support Wayland. For global hotkeys on Wayland, need compositor-specific protocols (GNOME Shell extensions, KWin scripts).
- **StatusIcon:** Gtk.StatusIcon deprecated in GTK 3.14+ (2014), removed in GTK 4. Use AppIndicator3 (already done in this project).
- **~/.app-namerc files:** Non-standard. Use XDG Base Directory spec instead.

## Open Questions

1. **Should settings be editable via GUI dialog or file-only?**
   - What we know: File editing works, but users may expect GUI. GNOME apps typically have Preferences dialog.
   - What's unclear: User preference for this specific tool. Power users may prefer file editing.
   - Recommendation: Start with file-only (simpler), add GUI dialog in future if users request it. Document config file location in menu item ("Settings: ~/.config/...")

2. **How to handle invalid config on load?**
   - What we know: Validation in `__post_init__` raises ValueError. Could crash app on startup if config corrupted.
   - What's unclear: Best UX - show error dialog, fall back to defaults silently, or restore from backup?
   - Recommendation: Try load, catch ValueError, show notification with error message, fall back to defaults, save corrected config. Log original to `~/.config/claude-usage-overlay/config.json.error` for debugging.

3. **Should pause_notifications persist across restarts?**
   - What we know: It's saved in config.json, so yes by default.
   - What's unclear: Is "pause" intended as temporary (presentation mode) or permanent (disable forever)?
   - Recommendation: Persist across restarts (current behavior). Add menu toggle "Pause Notifications" that updates config and saves. User can unpause when needed.

## Sources

### Primary (HIGH confidence)
- [XDG Base Directory Specification - ArchWiki](https://wiki.archlinux.org/title/XDG_Base_Directory) - Configuration directory standards
- [Desktop Application Autostart Specification - freedesktop.org](https://specifications.freedesktop.org/autostart/latest/) - Autostart .desktop file format
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html) - Stdlib dataclass API
- [GLib.timeout_add_seconds documentation](https://docs.gtk.org/glib/func.timeout_add_seconds.html) - Timer management
- [Python GTK+ 3 Tutorial - Menus](https://python-gtk-3-tutorial.readthedocs.io/en/latest/menus.html) - Menu accelerators

### Secondary (MEDIUM confidence)
- [Using GSettings with Python/PyGObject - Micah Carrick](https://www.micahcarrick.com/gsettings-python-gnome-3.html) - GSettings vs JSON tradeoffs (verified with official GSettings docs)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Alternative approach (verified but not using)
- [dataclasses-json PyPI](https://pypi.org/project/dataclasses-json/) - JSON serialization library (verified but stdlib sufficient)

### Tertiary (LOW confidence, marked for validation)
- keybinder-3.0 maintenance status - GitHub shows last release 2017, but this could be stable-not-abandoned. Check if X11-Wayland distinction matters for target users.
- Configuration reload approaches - watchdog library vs manual file monitoring. Performance implications unknown for this simple use case.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib, well-documented XDG specs, established GTK patterns
- Architecture: HIGH - Patterns verified in official docs and production apps
- Pitfalls: HIGH - Common issues documented in ArchWiki, Stack Overflow, official troubleshooting guides

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - stable domain, Python 3.11+ and GTK 3 mature)

"""Autostart management for Claude Usage Overlay."""

import os
import shutil
from configparser import ConfigParser
from pathlib import Path


def get_autostart_path() -> Path:
    """Get XDG-compliant autostart directory path.

    Returns:
        Path: Path to autostart directory
    """
    config_home = os.environ.get('XDG_CONFIG_HOME')
    if config_home:
        base = Path(config_home)
    else:
        base = Path.home() / '.config'

    autostart_dir = base / 'autostart'
    autostart_dir.mkdir(parents=True, exist_ok=True)

    return autostart_dir


def get_desktop_file_path() -> Path:
    """Get path to the .desktop file.

    Returns:
        Path: Path to claude-usage-overlay.desktop
    """
    return get_autostart_path() / 'claude-usage-overlay.desktop'


def _get_exec_command() -> str:
    """Determine the best Exec command for the .desktop file.

    Returns:
        Command string for Exec= line, preferring installed entry point
    """
    # Prefer the installed 'claude-usage' command if available
    claude_usage_path = shutil.which("claude-usage")
    if claude_usage_path:
        return claude_usage_path

    # Fallback to running module directly with python
    project_root = Path(__file__).parent.parent.absolute()
    main_py = project_root / "src" / "main.py"
    if main_py.exists():
        # Use sys.executable equivalent for current python
        return f"python3 -m src.main"

    # Last resort: assume it's installed as module
    return "python3 -m src.main"


def create_autostart_entry(enable: bool = True):
    """Create or update autostart .desktop file.

    Args:
        enable: If True, enable autostart. If False, disable (set Hidden=true).
    """
    desktop_file = get_desktop_file_path()

    # Get best exec command (prefer installed entry point)
    exec_cmd = _get_exec_command()

    # Desktop entry content
    hidden_value = "false" if enable else "true"
    content = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=Claude Code Usage Monitor
Comment=System tray monitor for Claude Code token usage
Exec={exec_cmd}
Icon=dialog-information
Terminal=false
Categories=Utility;Monitor;
StartupNotify=false
X-GNOME-Autostart-enabled=true
Hidden={hidden_value}
"""

    # Write .desktop file with secure permissions (rw-r--r--)
    # .desktop files don't need execute bit - they're parsed by desktop environment
    desktop_file.write_text(content)
    desktop_file.chmod(0o644)


def remove_autostart_entry():
    """Remove autostart .desktop file."""
    desktop_file = get_desktop_file_path()
    if desktop_file.exists():
        desktop_file.unlink()


def is_autostart_enabled() -> bool:
    """Check if autostart is enabled.

    Returns:
        bool: True if autostart is enabled (file exists and Hidden!=true)
    """
    desktop_file = get_desktop_file_path()

    if not desktop_file.exists():
        return False

    # Use configparser for proper INI parsing
    parser = ConfigParser(interpolation=None)
    try:
        parser.read(desktop_file)
        # Desktop files use 'Desktop Entry' section
        # Hidden=true means disabled; absent or false means enabled
        hidden = parser.get('Desktop Entry', 'Hidden', fallback='false')
        return hidden.lower() != 'true'
    except Exception:
        # If parsing fails, assume enabled if file exists
        return True

"""Autostart management for Claude Usage Overlay.

Cross-platform: supports Linux (.desktop), Windows (Registry), and macOS (LaunchAgent).
"""

import os
import shutil
import sys
from configparser import ConfigParser
from pathlib import Path

# Detect platform
IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')


# --- Linux .desktop file support ---

def _get_linux_autostart_path() -> Path:
    """Get XDG-compliant autostart directory path for Linux.

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


def _get_linux_desktop_file_path() -> Path:
    """Get path to the Linux .desktop file.

    Returns:
        Path: Path to claude-usage-overlay.desktop
    """
    return _get_linux_autostart_path() / 'claude-usage-overlay.desktop'


def _get_exec_command() -> str:
    """Determine the best Exec command for autostart.

    Returns:
        Command string, preferring installed entry point.
        On Windows, paths are quoted to handle spaces.
    """
    # Prefer the installed 'claude-usage' command if available
    claude_usage_path = shutil.which("claude-usage")
    if claude_usage_path:
        # Quote path on Windows in case of spaces
        if IS_WINDOWS and ' ' in claude_usage_path:
            return f'"{claude_usage_path}"'
        return claude_usage_path

    # For PyInstaller frozen executable
    if getattr(sys, 'frozen', False):
        if IS_WINDOWS and ' ' in sys.executable:
            return f'"{sys.executable}"'
        return sys.executable

    # Fallback to running module directly with python
    if IS_WINDOWS:
        # Quote Python path on Windows (often in "Program Files")
        return f'"{sys.executable}" -m src.main'
    return f"{sys.executable} -m src.main"


def _create_linux_autostart(enable: bool = True):
    """Create or update autostart .desktop file on Linux.

    Args:
        enable: If True, enable autostart. If False, disable (set Hidden=true).
    """
    desktop_file = _get_linux_desktop_file_path()
    exec_cmd = _get_exec_command()

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

    desktop_file.write_text(content)
    desktop_file.chmod(0o644)


def _remove_linux_autostart():
    """Remove autostart .desktop file on Linux."""
    desktop_file = _get_linux_desktop_file_path()
    if desktop_file.exists():
        desktop_file.unlink()


def _is_linux_autostart_enabled() -> bool:
    """Check if autostart is enabled on Linux.

    Returns:
        bool: True if autostart is enabled (file exists and Hidden!=true)
    """
    desktop_file = _get_linux_desktop_file_path()

    if not desktop_file.exists():
        return False

    parser = ConfigParser(interpolation=None)
    try:
        parser.read(desktop_file)
        hidden = parser.get('Desktop Entry', 'Hidden', fallback='false')
        return hidden.lower() != 'true'
    except Exception:
        return True


# --- Windows Registry support ---

WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_APP_NAME = "ClaudeUsageOverlay"


def _create_windows_autostart(enable: bool = True):
    """Create or remove autostart Registry entry on Windows.

    Args:
        enable: If True, enable autostart. If False, remove entry.
    """
    if not IS_WINDOWS:
        return

    import winreg

    exec_cmd = _get_exec_command()

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            WINDOWS_RUN_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            if enable:
                winreg.SetValueEx(key, WINDOWS_APP_NAME, 0, winreg.REG_SZ, exec_cmd)
            else:
                try:
                    winreg.DeleteValue(key, WINDOWS_APP_NAME)
                except FileNotFoundError:
                    pass  # Already removed
        finally:
            winreg.CloseKey(key)
    except OSError as e:
        print(f"Failed to modify Windows autostart: {e}", file=sys.stderr)


def _remove_windows_autostart():
    """Remove autostart Registry entry on Windows."""
    _create_windows_autostart(enable=False)


def _is_windows_autostart_enabled() -> bool:
    """Check if autostart is enabled on Windows.

    Returns:
        bool: True if Registry entry exists
    """
    if not IS_WINDOWS:
        return False

    import winreg

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            WINDOWS_RUN_KEY,
            0,
            winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, WINDOWS_APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


# --- macOS LaunchAgent support ---

def _get_macos_launch_agent_path() -> Path:
    """Get path to macOS LaunchAgent plist file.

    Returns:
        Path: Path to com.claude-usage.overlay.plist
    """
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    return launch_agents_dir / "com.claude-usage.overlay.plist"


def _create_macos_autostart(enable: bool = True):
    """Create or update LaunchAgent plist on macOS.

    Args:
        enable: If True, enable autostart. If False, remove plist.
    """
    if not IS_MACOS:
        return

    plist_path = _get_macos_launch_agent_path()

    if not enable:
        if plist_path.exists():
            plist_path.unlink()
        return

    exec_cmd = _get_exec_command()

    # For module execution, split into program and arguments
    if " -m " in exec_cmd:
        parts = exec_cmd.split()
        program = parts[0]
        args = parts[1:]
        args_xml = "\n".join(f"        <string>{arg}</string>" for arg in args)
        program_args = f"""    <key>ProgramArguments</key>
    <array>
        <string>{program}</string>
{args_xml}
    </array>"""
    else:
        program_args = f"""    <key>ProgramArguments</key>
    <array>
        <string>{exec_cmd}</string>
    </array>"""

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude-usage.overlay</string>
{program_args}
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""

    plist_path.write_text(plist_content)


def _remove_macos_autostart():
    """Remove LaunchAgent plist on macOS."""
    _create_macos_autostart(enable=False)


def _is_macos_autostart_enabled() -> bool:
    """Check if autostart is enabled on macOS.

    Returns:
        bool: True if LaunchAgent plist exists
    """
    if not IS_MACOS:
        return False

    return _get_macos_launch_agent_path().exists()


# --- Cross-platform public API ---

def get_autostart_path() -> Path:
    """Get platform-specific autostart path.

    Returns:
        Path: Path to autostart configuration location
    """
    if IS_WINDOWS:
        # Return a conceptual path for documentation purposes
        return Path("HKCU") / WINDOWS_RUN_KEY / WINDOWS_APP_NAME
    elif IS_MACOS:
        return _get_macos_launch_agent_path()
    else:
        return _get_linux_autostart_path()


def get_desktop_file_path() -> Path:
    """Get path to the autostart configuration file.

    Returns:
        Path: Platform-specific autostart file path
    """
    if IS_WINDOWS:
        return Path("HKCU") / WINDOWS_RUN_KEY / WINDOWS_APP_NAME
    elif IS_MACOS:
        return _get_macos_launch_agent_path()
    else:
        return _get_linux_desktop_file_path()


def create_autostart_entry(enable: bool = True):
    """Create or update autostart entry for current platform.

    Args:
        enable: If True, enable autostart. If False, disable.
    """
    if IS_WINDOWS:
        _create_windows_autostart(enable)
    elif IS_MACOS:
        _create_macos_autostart(enable)
    else:
        _create_linux_autostart(enable)


def remove_autostart_entry():
    """Remove autostart entry for current platform."""
    if IS_WINDOWS:
        _remove_windows_autostart()
    elif IS_MACOS:
        _remove_macos_autostart()
    else:
        _remove_linux_autostart()


def is_autostart_enabled() -> bool:
    """Check if autostart is enabled for current platform.

    Returns:
        bool: True if autostart is enabled
    """
    if IS_WINDOWS:
        return _is_windows_autostart_enabled()
    elif IS_MACOS:
        return _is_macos_autostart_enabled()
    else:
        return _is_linux_autostart_enabled()

# Claude Code Usage Overlay

A Linux/GNOME system tray application that monitors your Claude Code token usage and alerts you before hitting limits.

[![PyPI version](https://img.shields.io/pypi/v/claude-code-usage.svg)](https://pypi.org/project/claude-code-usage/)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux%2FGNOME-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **System tray icon** with color-coded gauge (green/yellow/red based on usage)
- **Panel label** showing session and weekly usage percentages
- **Popup notifications** at configurable thresholds (default: 50%, 75%, 90%)
- **Configurable settings** via JSON file or Settings menu
- **Auto-start on login** via XDG autostart

## Screenshots

The tray icon shows your current usage with:
- Arc fill = session usage (5-hour window)
- Color = worst-case urgency (max of session/weekly)
- Panel label = "45%|67%" format

## Requirements

- Linux with GNOME Shell (or compatible desktop with AppIndicator support)
- Python 3.11+
- [Claude Code CLI](https://claude.ai/code) installed and authenticated
- AppIndicator extension for GNOME Shell

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7

# Fedora
sudo dnf install python3-gobject python3-cairo libayatana-appindicator-gtk3 libnotify

# Arch
sudo pacman -S python-gobject python-cairo libayatana-appindicator libnotify
```

### GNOME Shell Extension

Install the [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/) extension for GNOME Shell to see system tray icons.

## Installation

### From PyPI (recommended)

1. Install system dependencies (see [System Dependencies](#system-dependencies) above)

2. Install with pipx (recommended):
   ```bash
   pipx install claude-code-usage --system-site-packages
   ```

   The `--system-site-packages` flag is required to access system GTK libraries.

3. Run: `claude-usage`

### From Source

```bash
git clone https://github.com/Maex-z9/CC_Usage.git
cd CC_Usage
./install.sh
```

This installs system dependencies and the app automatically.

### Prerequisites

Make sure you have Claude Code CLI installed and authenticated:
```bash
claude
# Follow the authentication flow
```

## Usage

Run the application:

```bash
claude-usage
```

Or if running from source:
```bash
python3 -m src.main
```

### Menu Options

Click the tray icon to access:
- Current usage percentages and reset time
- **Refresh** - Force update usage data
- **Settings** submenu:
  - Pause Notifications - Temporarily disable alerts
  - Autostart on Login - Enable/disable auto-start
  - Edit Config File - Open config in text editor
- **Quit** - Exit the application

### Configuration

Config file location: `~/.config/claude-usage-overlay/config.json`

```json
{
  "session_thresholds": [50, 75, 90],
  "weekly_thresholds": [50, 75, 90],
  "polling_interval": 300,
  "pause_notifications": false,
  "autostart_enabled": false
}
```

| Setting | Description | Default |
|---------|-------------|---------|
| `session_thresholds` | Alert thresholds for 5-hour session usage | `[50, 75, 90]` |
| `weekly_thresholds` | Alert thresholds for 7-day weekly usage | `[50, 75, 90]` |
| `polling_interval` | Seconds between API checks (30-3600) | `300` (5 min) |
| `pause_notifications` | Disable popup alerts | `false` |
| `autostart_enabled` | Start on login | `false` |

## How It Works

1. Reads your OAuth token from `~/.claude/.credentials.json` (created by Claude Code CLI)
2. Polls the Anthropic usage API every 5 minutes (configurable)
3. Displays usage in the system tray with color-coded urgency
4. Shows desktop notifications when thresholds are crossed

## Privacy & Security

- **No API keys stored in the repo** - Uses Claude Code's existing credentials
- **Credentials stay local** - Reads from `~/.claude/.credentials.json`
- **Config stays local** - Stored in `~/.config/claude-usage-overlay/`
- **No data sent anywhere** - Only communicates with Anthropic's API

## Known Issues

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for details on:
- GNOME Shell tooltip limitations (using panel label instead)
- AppIndicator menu accelerator limitations

## Contributing

Contributions welcome! Please open an issue or PR.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

Built with [Claude Code](https://claude.ai/code) using the [GSD workflow](https://github.com/get-shit-done/gsd).

#!/usr/bin/env python3
"""Claude Code Usage Overlay - System tray application."""

import argparse
import sys
from pathlib import Path


def main():
    """Start the Claude Code Usage Overlay application."""
    parser = argparse.ArgumentParser(
        description="Claude Code Usage Overlay - system tray monitor"
    )
    parser.add_argument(
        "--config",
        metavar="DIR",
        help=(
            "Path to Claude config directory containing .credentials.json "
            "(overrides the CLAUDE_CONFIG_DIR environment variable and the default ~/.claude)"
        ),
    )
    args = parser.parse_args()
    claude_config_dir = Path(args.config) if args.config else None

    try:
        from src.tray import TrayIndicator

        indicator = TrayIndicator(claude_config_dir=claude_config_dir)
        indicator.run()

    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

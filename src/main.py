#!/usr/bin/env python3
"""Claude Code Usage Overlay - System tray application."""

import sys


def main():
    """Start the Claude Code Usage Overlay application."""
    try:
        from src.tray import TrayIndicator

        indicator = TrayIndicator()
        indicator.run()

    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/bin/bash
# Install script for Claude Code Usage Overlay
set -e

echo "=== Claude Code Usage Overlay Installer ==="
echo

# Detect package manager
if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    echo "Detected: Debian/Ubuntu"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    echo "Detected: Fedora/RHEL"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    echo "Detected: Arch Linux"
else
    echo "Error: Could not detect package manager (apt/dnf/pacman)"
    echo "Please install system dependencies manually. See README.md"
    exit 1
fi

echo

# Install system dependencies
echo "Installing system dependencies..."
case $PKG_MANAGER in
    apt)
        sudo apt update
        sudo apt install -y python3-gi python3-gi-cairo gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7 python3-pip
        ;;
    dnf)
        sudo dnf install -y python3-gobject python3-cairo libayatana-appindicator-gtk3 libnotify python3-pip
        ;;
    pacman)
        sudo pacman -S --noconfirm python-gobject python-cairo libayatana-appindicator libnotify python-pip
        ;;
esac

echo

# Install Python package
echo "Installing Python package..."
pip install --user .

echo
echo "=== Installation complete! ==="
echo
echo "Run with:  claude-usage"
echo
echo "Note: Make sure you have:"
echo "  1. Claude Code CLI installed and authenticated (run 'claude' first)"
echo "  2. AppIndicator extension for GNOME Shell (if using GNOME)"
echo

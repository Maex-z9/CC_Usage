"""
Icon generation utilities for Claude Code usage overlay.

Generates circular gauge icons using Cairo for system tray display.
"""
import cairo
import math
import os
import tempfile
from pathlib import Path
from typing import Tuple

# Secure temp directory for icons (created once, reused)
_icon_temp_dir: str | None = None


def _get_secure_icon_dir() -> str:
    """Get or create a secure temporary directory for icon files.

    Returns:
        Path to secure temp directory with restricted permissions (0o700)
    """
    global _icon_temp_dir
    if _icon_temp_dir is None or not Path(_icon_temp_dir).exists():
        # Create secure temp directory owned by current user only
        _icon_temp_dir = tempfile.mkdtemp(prefix="claude-usage-icons-")
        os.chmod(_icon_temp_dir, 0o700)
    return _icon_temp_dir


def get_color_for_percentage(percentage: float) -> Tuple[float, float, float]:
    """
    Return RGB color tuple based on usage percentage.

    Args:
        percentage: Usage percentage (0-100)

    Returns:
        RGB tuple in Cairo format (0.0-1.0 range)
        - Green for < 50%
        - Yellow for 50-75%
        - Red for >= 75%
    """
    if percentage < 50:
        return (0.2, 0.8, 0.2)  # Green
    elif percentage < 75:
        return (0.9, 0.7, 0.0)  # Yellow
    else:
        return (0.9, 0.2, 0.2)  # Red


def generate_gauge_icon(percentage: float, color_percentage: float, size: int = 22) -> str:
    """
    Generate a circular gauge icon showing usage percentage.

    Args:
        percentage: Usage level to display as arc fill (0-100)
        color_percentage: Percentage used to determine color (0-100)
        size: Icon size in pixels (default: 22)

    Returns:
        Absolute path to generated PNG file in /tmp

    Notes:
        - percentage controls the arc fill amount (how full the gauge is)
        - color_percentage controls the color (via get_color_for_percentage)
        - This separation allows showing session usage while coloring by worst-case urgency
    """
    # Get color based on color_percentage parameter
    fill_color = get_color_for_percentage(color_percentage)

    # Determine color name for filename (to bust icon cache)
    if color_percentage < 50:
        color_name = "green"
    elif color_percentage < 75:
        color_name = "yellow"
    else:
        color_name = "red"

    # Create Cairo surface with transparent background
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surface)

    # Clear background (transparent)
    ctx.set_source_rgba(0, 0, 0, 0)
    ctx.paint()

    # Calculate center and radius (leave 2px margin)
    center = size / 2
    radius = (size / 2) - 2

    # Draw gray outline (full circle)
    ctx.set_source_rgb(0.5, 0.5, 0.5)
    ctx.set_line_width(2)
    ctx.arc(center, center, radius, 0, 2 * math.pi)
    ctx.stroke()

    # Draw colored fill arc (based on percentage)
    if percentage > 0:
        ctx.set_source_rgb(*fill_color)
        ctx.set_line_width(2)
        # Start at 12 o'clock (-pi/2), go clockwise by percentage amount
        end_angle = -math.pi / 2 + (2 * math.pi * percentage / 100)
        ctx.arc(center, center, radius, -math.pi / 2, end_angle)
        ctx.stroke()

    # Save to secure temp directory with unique filename (bust GTK icon cache)
    icon_dir = _get_secure_icon_dir()
    icon_path = os.path.join(icon_dir, f"gauge-{int(percentage)}-{color_name}.png")
    surface.write_to_png(icon_path)

    return os.path.abspath(icon_path)

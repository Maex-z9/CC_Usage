"""
Icon generation utilities for Claude Code usage overlay.

Generates circular gauge icons using Pillow for system tray display.
Cross-platform: works on Windows, macOS, and Linux.
"""
from typing import Tuple

from PIL import Image, ImageDraw


def get_color_for_percentage(percentage: float) -> Tuple[int, int, int, int]:
    """
    Return RGBA color tuple based on usage percentage.

    Args:
        percentage: Usage percentage (0-100)

    Returns:
        RGBA tuple in Pillow format (0-255 range)
        - Green for < 50%
        - Yellow for 50-75%
        - Red for >= 75%
    """
    if percentage < 50:
        return (51, 204, 51, 255)  # Green
    elif percentage < 75:
        return (230, 179, 0, 255)  # Yellow
    else:
        return (230, 51, 51, 255)  # Red


def generate_gauge_icon(percentage: float, color_percentage: float, size: int = 22) -> Image.Image:
    """
    Generate a circular gauge icon showing usage percentage.

    Args:
        percentage: Usage level to display as arc fill (0-100)
        color_percentage: Percentage used to determine color (0-100)
        size: Icon size in pixels (default: 22)

    Returns:
        PIL.Image.Image object (RGBA mode) for use with pystray

    Notes:
        - percentage controls the arc fill amount (how full the gauge is)
        - color_percentage controls the color (via get_color_for_percentage)
        - This separation allows showing session usage while coloring by worst-case urgency
    """
    # Get color based on color_percentage parameter
    fill_color = get_color_for_percentage(color_percentage)
    gray_color = (128, 128, 128, 255)

    # Create transparent RGBA image
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Calculate center and radius (leave 2px margin)
    margin = 2
    line_width = 2

    # Bounding box for the arc (accounts for margin)
    bbox = [margin, margin, size - margin - 1, size - margin - 1]

    # Draw gray outline (full circle) as arc from 0 to 360
    draw.arc(bbox, start=0, end=360, fill=gray_color, width=line_width)

    # Draw colored fill arc (based on percentage)
    if percentage > 0:
        # Pillow arc: 0 degrees = 3 o'clock, angles go counter-clockwise
        # We want: start at 12 o'clock (-90 degrees), go clockwise
        # Pillow arc goes counter-clockwise, so we need to reverse direction
        # Start at -90 (12 o'clock), end at -90 + percentage*3.6
        start_angle = -90
        end_angle = -90 + (360 * percentage / 100)
        draw.arc(bbox, start=start_angle, end=end_angle, fill=fill_color, width=line_width)

    return image


def generate_gauge_icon_path(percentage: float, color_percentage: float, size: int = 22) -> str:
    """
    Generate a circular gauge icon and save to temp file.

    This function is for backwards compatibility with code that needs file paths.
    Prefer using generate_gauge_icon() directly with pystray.

    Args:
        percentage: Usage level to display as arc fill (0-100)
        color_percentage: Percentage used to determine color (0-100)
        size: Icon size in pixels (default: 22)

    Returns:
        Absolute path to generated PNG file in temp directory
    """
    import os
    import tempfile
    from pathlib import Path

    # Determine color name for filename (to bust icon cache)
    if color_percentage < 50:
        color_name = "green"
    elif color_percentage < 75:
        color_name = "yellow"
    else:
        color_name = "red"

    # Get or create temp directory
    temp_dir = tempfile.gettempdir()
    icon_dir = os.path.join(temp_dir, "claude-usage-icons")
    os.makedirs(icon_dir, exist_ok=True)

    # Generate icon
    image = generate_gauge_icon(percentage, color_percentage, size)

    # Save to file
    icon_path = os.path.join(icon_dir, f"gauge-{int(percentage)}-{color_name}.png")
    image.save(icon_path, 'PNG')

    return os.path.abspath(icon_path)

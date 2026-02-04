"""
Utility functions for Claude Code usage overlay.

Provides time formatting and other helper functions.
"""
from datetime import datetime, timezone
from typing import Optional
import humanize


def format_time_until(reset_time: Optional[datetime]) -> str:
    """
    Format time remaining until reset as human-readable string.

    Args:
        reset_time: Timezone-aware datetime when usage resets

    Returns:
        Human-readable string like "2 hours" or "15 minutes"
        Returns "Unknown" if reset_time is None
        Returns "Now" if reset_time is in the past
    """
    if reset_time is None:
        return "Unknown"

    # Calculate time delta
    now = datetime.now(timezone.utc)
    delta = reset_time - now

    # Check if time is in the past
    if delta.total_seconds() <= 0:
        return "Now"

    # Format using humanize
    return humanize.naturaldelta(delta)

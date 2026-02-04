"""Configuration module for loading Claude OAuth credentials."""

import json
import time
from pathlib import Path


CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"


def load_credentials() -> dict:
    """Load Claude OAuth credentials from ~/.claude/.credentials.json.

    Returns:
        dict: The claudeAiOauth object containing accessToken, expiresAt, etc.

    Raises:
        FileNotFoundError: If credentials file doesn't exist
        ValueError: If credentials file format is invalid
    """
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            "Claude credentials not found. Run `claude` first to authenticate."
        )

    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid credentials file format: {e}")

    if "claudeAiOauth" not in data:
        raise ValueError("Invalid credentials file format")

    return data["claudeAiOauth"]


def is_token_expired(credentials: dict) -> bool:
    """Check if the OAuth token has expired.

    Args:
        credentials: The claudeAiOauth object with expiresAt field

    Returns:
        bool: True if expired or expiresAt is None
    """
    expires_at = credentials.get("expiresAt")

    if expires_at is None:
        return True

    # expiresAt is in milliseconds since epoch
    current_time_ms = time.time() * 1000
    return current_time_ms >= expires_at


def get_access_token() -> str:
    """Get a valid OAuth access token.

    Returns:
        str: The access token string

    Raises:
        FileNotFoundError: If credentials file doesn't exist
        ValueError: If credentials are invalid or token expired
    """
    credentials = load_credentials()

    if is_token_expired(credentials):
        raise ValueError("OAuth token has expired")

    return credentials["accessToken"]

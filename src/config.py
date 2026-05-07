"""Configuration module for loading Claude OAuth credentials.

Cross-platform: uses platformdirs for config directory resolution.
"""

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import platformdirs


# Application info for platformdirs
APP_NAME = "claude-usage-overlay"
APP_AUTHOR = "claude-usage"  # Used on Windows


def get_credentials_path(claude_config_dir: Path = None) -> Path:
    """Resolve the credentials file path.

    Priority order:
      1. claude_config_dir argument (from --config CLI option)
      2. CLAUDE_CONFIG_DIR environment variable
      3. Default ~/.claude

    Args:
        claude_config_dir: Optional explicit override directory

    Returns:
        Path: Full path to .credentials.json
    """
    if claude_config_dir is not None:
        base = claude_config_dir
    else:
        env_dir = os.environ.get("CLAUDE_CONFIG_DIR")
        base = Path(env_dir) if env_dir else Path.home() / ".claude"
    return base / ".credentials.json"


def load_credentials(claude_config_dir: Path = None) -> dict:
    """Load Claude OAuth credentials.

    Args:
        claude_config_dir: Optional override for the Claude config directory.
            Respects CLAUDE_CONFIG_DIR env var if not provided.

    Returns:
        dict: The claudeAiOauth object containing accessToken, expiresAt, etc.

    Raises:
        FileNotFoundError: If credentials file doesn't exist
        ValueError: If credentials file format is invalid
    """
    credentials_path = get_credentials_path(claude_config_dir)

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Claude credentials not found at {credentials_path}. "
            "Run `claude` first to authenticate."
        )

    try:
        with open(credentials_path, 'r') as f:
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


def get_access_token(claude_config_dir: Path = None) -> str:
    """Get a valid OAuth access token.

    Args:
        claude_config_dir: Optional override for the Claude config directory.

    Returns:
        str: The access token string

    Raises:
        FileNotFoundError: If credentials file doesn't exist
        ValueError: If credentials are invalid or token expired
    """
    credentials = load_credentials(claude_config_dir)

    if is_token_expired(credentials):
        raise ValueError("OAuth token has expired")

    return credentials["accessToken"]


def get_config_dir() -> Path:
    """Get cross-platform config directory.

    Returns:
        Path: Config directory path
        - Linux: ~/.config/claude-usage-overlay/
        - Windows: %APPDATA%/claude-usage/claude-usage-overlay/
        - macOS: ~/Library/Application Support/claude-usage-overlay/
    """
    config_dir = Path(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get cross-platform config file path.

    Returns:
        Path: Path to config.json in platform-specific config directory
    """
    return get_config_dir() / 'config.json'


@dataclass
class UserConfig:
    """User configuration settings for Claude Usage Overlay."""

    session_thresholds: list[int] = None
    weekly_thresholds: list[int] = None
    polling_interval: int = 300
    pause_notifications: bool = False
    autostart_enabled: bool = False

    def __post_init__(self):
        """Validate configuration values and set defaults."""
        # Set defaults for None fields (avoid mutable default trap)
        if self.session_thresholds is None:
            self.session_thresholds = [50, 75, 90]
        if self.weekly_thresholds is None:
            self.weekly_thresholds = [50, 75, 90]

        # Validate thresholds
        for threshold in self.session_thresholds:
            if not isinstance(threshold, int) or not (0 <= threshold <= 100):
                raise ValueError(
                    f"Invalid session threshold: {threshold}. Must be integer 0-100."
                )
        for threshold in self.weekly_thresholds:
            if not isinstance(threshold, int) or not (0 <= threshold <= 100):
                raise ValueError(
                    f"Invalid weekly threshold: {threshold}. Must be integer 0-100."
                )

        # Validate polling_interval
        if not isinstance(self.polling_interval, int) or not (30 <= self.polling_interval <= 3600):
            raise ValueError(
                f"Invalid polling_interval: {self.polling_interval}. Must be integer 30-3600."
            )

        # Validate boolean fields
        if not isinstance(self.pause_notifications, bool):
            raise ValueError(
                f"Invalid pause_notifications: {self.pause_notifications}. Must be bool."
            )
        if not isinstance(self.autostart_enabled, bool):
            raise ValueError(
                f"Invalid autostart_enabled: {self.autostart_enabled}. Must be bool."
            )

    @classmethod
    def load(cls) -> 'UserConfig':
        """Load configuration from config file.

        Returns:
            UserConfig: Configuration object with values from file or defaults

        Raises:
            ValueError: If config file format is invalid
        """
        config_path = get_config_path()

        if not config_path.exists():
            return cls()

        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid config file format: {e}")

        try:
            return cls(**data)
        except TypeError as e:
            raise ValueError(f"Invalid config file structure: {e}")

    def save(self):
        """Save configuration to config file with secure permissions."""
        config_path = get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if sys.platform != 'win32':
            # Open with O_CREAT so the file is created with mode 0o600 atomically,
            # avoiding a window where the file exists with world-readable permissions.
            fd = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'w') as f:
                json.dump(asdict(self), f, indent=2)
        else:
            with open(config_path, 'w') as f:
                json.dump(asdict(self), f, indent=2)

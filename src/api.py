"""API client for fetching Claude Code usage data."""

import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests


USAGE_ENDPOINT = "https://api.anthropic.com/api/oauth/usage"


@dataclass
class UsageData:
    """Structured usage data from the Anthropic API."""

    session_percent: float  # from five_hour.utilization
    session_resets_at: Optional[datetime]  # from five_hour.resets_at
    weekly_percent: float  # from seven_day.utilization
    weekly_resets_at: Optional[datetime]  # from seven_day.resets_at


class APIError(Exception):
    """Base exception for API errors."""

    pass


class AuthenticationError(APIError):
    """Exception for 401 authentication failures."""

    pass


class RateLimitError(APIError):
    """Exception for 429 rate limit errors."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


def fetch_usage(access_token: str) -> UsageData:
    """Fetch usage data from the Anthropic API.

    Args:
        access_token: OAuth access token

    Returns:
        UsageData: Parsed usage information

    Raises:
        AuthenticationError: On 401 responses
        RateLimitError: On 429 responses
        APIError: On other errors
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "anthropic-beta": "oauth-2025-04-20",
    }

    try:
        response = requests.get(USAGE_ENDPOINT, headers=headers, timeout=10)
    except requests.RequestException as e:
        raise APIError(f"Network error: {e}")

    if response.status_code == 200:
        try:
            data = response.json()

            # Parse five_hour data
            five_hour = data.get("five_hour", {})
            session_percent = five_hour.get("utilization", 0.0)
            session_resets_str = five_hour.get("resets_at")
            session_resets_at = (
                datetime.fromisoformat(session_resets_str.replace("Z", "+00:00"))
                if session_resets_str
                else None
            )

            # Parse seven_day data
            seven_day = data.get("seven_day", {})
            weekly_percent = seven_day.get("utilization", 0.0)
            weekly_resets_str = seven_day.get("resets_at")
            weekly_resets_at = (
                datetime.fromisoformat(weekly_resets_str.replace("Z", "+00:00"))
                if weekly_resets_str
                else None
            )

            return UsageData(
                session_percent=session_percent,
                session_resets_at=session_resets_at,
                weekly_percent=weekly_percent,
                weekly_resets_at=weekly_resets_at,
            )
        except (KeyError, ValueError, TypeError) as e:
            raise APIError(f"Failed to parse API response: {e}")

    elif response.status_code == 401:
        raise AuthenticationError("OAuth token is invalid or expired")

    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise RateLimitError(
            f"Rate limited, retry after {retry_after} seconds", retry_after
        )

    elif 500 <= response.status_code < 600:
        raise APIError(f"Server error: {response.status_code}")

    else:
        raise APIError(
            f"Unexpected response: {response.status_code} - {response.text}"
        )


def fetch_with_retry(access_token: str, max_retries: int = 3) -> UsageData:
    """Fetch usage data with retry logic.

    Args:
        access_token: OAuth access token
        max_retries: Maximum number of retry attempts

    Returns:
        UsageData: Parsed usage information

    Raises:
        AuthenticationError: On 401 responses (no retry)
        APIError: If all retries exhausted
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return fetch_usage(access_token)

        except AuthenticationError:
            # Don't retry authentication errors - user action needed
            raise

        except RateLimitError as e:
            last_exception = e
            if attempt < max_retries - 1:
                print(
                    f"Rate limited, waiting {e.retry_after}s before retry {attempt + 2}/{max_retries}...",
                    file=sys.stderr,
                )
                time.sleep(e.retry_after)
            else:
                print(f"Rate limited, all retries exhausted", file=sys.stderr)

        except APIError as e:
            last_exception = e
            if attempt < max_retries - 1:
                # Exponential backoff with cap at 30 seconds
                wait_time = min(30, 2**attempt)
                print(
                    f"API error: {e}. Retrying in {wait_time}s ({attempt + 2}/{max_retries})...",
                    file=sys.stderr,
                )
                time.sleep(wait_time)
            else:
                print(f"API error, all retries exhausted: {e}", file=sys.stderr)

    # All retries exhausted
    if last_exception:
        raise last_exception
    else:
        raise APIError("All retries exhausted")

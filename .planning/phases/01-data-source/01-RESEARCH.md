# Phase 1 Research: Data Source

## Phase Goal
Application can fetch and parse Claude Code usage data from Anthropic API

## Requirements
- DATA-01: Read OAuth token from ~/.claude/.credentials.json
- DATA-02: Poll Anthropic usage API periodically
- DATA-03: Handle API errors gracefully with retry

## API Details (from project research)

### Endpoint
```
GET https://api.anthropic.com/api/oauth/usage
```

### Authentication
```
Authorization: Bearer <access_token>
```

Token location: `~/.claude/.credentials.json`

### Credentials File Structure
```json
{
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "sk-ant-ort01-...",
    "expiresAt": 1770217077531,
    "scopes": ["user:inference", "user:profile", ...],
    "subscriptionType": "pro",
    "rateLimitTier": "default_claude_ai"
  }
}
```

### Required Headers
```
Authorization: Bearer <access_token>
Accept: application/json
anthropic-beta: oauth-2025-04-20
```

### Response Structure
```json
{
  "five_hour": {
    "utilization": 36.0,
    "resets_at": "2026-02-04T10:59:59+00:00"
  },
  "seven_day": {
    "utilization": 77.0,
    "resets_at": "2026-02-05T10:59:59+00:00"
  },
  "seven_day_opus": {
    "utilization": 0.0,
    "resets_at": null
  }
}
```

## Implementation Approach

### File Structure for Phase 1
```
src/
├── __init__.py
├── config.py      # Credentials + config loading
└── api.py         # API client with retry logic
```

### Config Module (config.py)
**Responsibilities:**
- Load OAuth token from ~/.claude/.credentials.json
- Check token expiration (expiresAt field)
- Load app settings from ~/.config/claude-usage-overlay/config.json

**Key functions:**
```python
def load_credentials() -> dict:
    """Load OAuth credentials from Claude Code config."""

def is_token_expired(credentials: dict) -> bool:
    """Check if token has expired."""

def load_app_config() -> dict:
    """Load application settings (poll interval, thresholds)."""
```

### API Module (api.py)
**Responsibilities:**
- Make HTTP requests to usage endpoint
- Parse response into structured data
- Handle errors with retry logic

**Key functions:**
```python
@dataclass
class UsageData:
    session_percent: float
    session_resets_at: datetime
    weekly_percent: float
    weekly_resets_at: datetime

def fetch_usage(access_token: str) -> UsageData:
    """Fetch current usage from Anthropic API."""

def fetch_with_retry(access_token: str, max_retries: int = 3) -> UsageData:
    """Fetch with exponential backoff on failure."""
```

### Error Handling Strategy

| Error | Response Code | Action |
|-------|---------------|--------|
| Network error | N/A | Retry with backoff |
| Unauthorized | 401 | Log error, notify user token may be expired |
| Rate limited | 429 | Retry after Retry-After header |
| Server error | 5xx | Retry with backoff |
| Parse error | N/A | Log, return partial data or raise |

**Exponential backoff:**
- Initial delay: 1 second
- Max delay: 30 seconds
- Formula: `min(30, 2^attempt)` seconds

### Validation Approach
Phase 1 is complete when:
1. Running `python -m src.config` prints loaded credentials (redacted)
2. Running `python -m src.api` prints current usage percentages
3. Simulated failures trigger retry logic

## Dependencies

```bash
pip install requests
```

No GTK dependencies needed for Phase 1 - pure Python.

## Risks for This Phase

| Risk | Mitigation |
|------|------------|
| Credentials file missing | Clear error message: "Run `claude` first to authenticate" |
| Token expired | Check expiresAt before use, warn user |
| API structure changes | Defensive parsing with try/except |

## Out of Scope (Phase 1)
- Token refresh (v2 feature)
- GTK integration (Phase 2)
- Periodic polling timer (Phase 2 - needs GTK main loop)

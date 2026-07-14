"""Shared secret-hygiene helpers: redaction and environment-variable checks.

This is the single source of truth for redacting API keys in logs/output and
for confirming required `.env` variables are present before a demo, a
lecture recording, or a section's exercise runs. Every later section and the
`scripts/pre_record_check.py` CLI import from here rather than
reimplementing this logic.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_PREFIX_LEN = 4
_SUFFIX_LEN = 2
_MIN_SAFE_LENGTH = _PREFIX_LEN + _SUFFIX_LEN


def redact(value: str) -> str:
    """Mask a secret value for safe display in logs or on screen.

    Args:
        value: The raw secret string (e.g. an API key).

    Returns:
        The first 4 and last 2 characters, with everything between replaced
        by asterisks. If ``value`` is too short to safely reveal both ends
        without exposing most of the string, the entire value is masked.
    """
    if len(value) <= _MIN_SAFE_LENGTH:
        return "*" * len(value)

    masked_middle = "*" * (len(value) - _MIN_SAFE_LENGTH)
    return value[:_PREFIX_LEN] + masked_middle + value[-_SUFFIX_LEN:]


def check_required_keys(required: tuple[str, ...]) -> bool:
    """Confirm every named environment variable is present and non-empty.

    Args:
        required: Names of environment variables that must be set.

    Returns:
        True if every variable in ``required`` is present with a non-empty
        value, False otherwise. Missing or empty variable names are logged
        as a warning.
    """
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        logger.warning("Missing required environment variables: %s", ", ".join(missing))
        return False

    return True


def check_langsmith_tracing() -> bool:
    """Confirm LANGSMITH_TRACING is set to exactly ``"true"``.

    Returns:
        True if the ``LANGSMITH_TRACING`` environment variable is exactly
        the string ``"true"``, False otherwise (including when unset).
    """
    value = os.environ.get("LANGSMITH_TRACING")
    if value != "true":
        logger.warning("LANGSMITH_TRACING is not set to 'true' (got: %r)", value)
        return False

    return True

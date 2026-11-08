"""Sanity check: confirms all four free-tier API keys from Section 2.2 are
present in the environment and that LangSmith tracing is switched on.

This script has no third-party LLM calls — it only proves the keys exist
and are non-empty. Section 2.3 is the first lecture that actually spends
a token calling a provider.

Redaction and env-var checks are imported from era_platform.secrets, the
shared module introduced in the repo's security-hardening pass (commit
86bef4c) — this script is a thin, lecture-specific wrapper around that
shared logic, not a reimplementation of it.

Target location in the course repo:
    sections/02-dev-environment-and-llm-fundamentals/demo_2_2_env_check.py

Per course convention, this file is shown on screen during recording but
is NOT committed to the repo — only era_platform/secrets.py and
scripts/pre_record_check.py are.
"""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

from era_platform.secrets import check_langsmith_tracing, check_required_keys, redact

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

REQUIRED_KEYS: tuple[str, ...] = (
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "TAVILY_API_KEY",
    "LANGSMITH_API_KEY",
)


def log_redacted_keys(keys: tuple[str, ...]) -> None:
    """Log each key's redacted preview, once presence has already been confirmed.

    Args:
        keys: Names of environment variables already known to be present.
    """
    for key in keys:
        logger.info("%s OK: %s", key, redact(os.environ[key]))


def main() -> int:
    """Run all environment checks and report a single pass/fail result.

    Returns:
        0 if every check passed, 1 otherwise.
    """
    load_dotenv()

    keys_ok = check_required_keys(REQUIRED_KEYS)
    if keys_ok:
        log_redacted_keys(REQUIRED_KEYS)

    tracing_ok = check_langsmith_tracing()
    if tracing_ok:
        project = os.environ.get("LANGSMITH_PROJECT", "default")
        logger.info("LangSmith tracing: ON (project=%s)", project)

    if keys_ok and tracing_ok:
        logger.info("Environment OK — ready for Section 2.3.")
        return 0

    logger.error("Environment check failed — fix the issue above before continuing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

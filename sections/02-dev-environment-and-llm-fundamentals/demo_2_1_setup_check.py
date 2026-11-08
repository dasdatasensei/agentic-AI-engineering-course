"""Sanity check: confirms Python 3.12, the active venv, and the editor
toolchain (Pylance + Ruff) are all wired together correctly.

This script has no external dependencies — Section 2.1 deliberately
stops here. Repo dependencies, API keys, and Docker/Redis are
introduced in their own later lectures; this file only proves the
environment itself is correct before we add anything to it.
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

REQUIRED_MAJOR_MINOR: tuple[int, int] = (3, 12)


def check_python_version() -> bool:
    """Confirm the interpreter running this script is Python 3.12.x."""
    actual = (sys.version_info.major, sys.version_info.minor)
    if actual != REQUIRED_MAJOR_MINOR:
        logger.error(
            "Wrong interpreter: got Python %d.%d, need %d.%d. "
            "Check the interpreter selected in VS Code's status bar.",
            *actual,
            *REQUIRED_MAJOR_MINOR,
        )
        return False

    logger.info("Python version OK: %d.%d.%d", *sys.version_info[:3])
    return True


def check_venv_active() -> bool:
    """Confirm this interpreter is running inside .venv, not system Python."""
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        logger.error(
            "Not running inside a virtual environment. Activate .venv before running this script."
        )
        return False

    logger.info("Virtual environment active: %s", Path(sys.prefix))
    return True


def main() -> int:
    """Run all environment checks and report a single pass/fail result."""
    checks = (check_python_version(), check_venv_active())
    if all(checks):
        logger.info("Environment OK — ready for Section 2.2.")
        return 0

    logger.error("Environment check failed — fix the issue above before continuing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

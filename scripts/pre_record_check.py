"""Pre-recording safety check: the last thing to run before hitting record.

Confirms `.env` is git-ignored and absent from `git status`, scans every
*tracked* file for key-shaped strings, and confirms the Section 2.2 `.env`
variables are present and correctly configured. Exits 0 only if every check
passes.

Usage:
    python scripts/pre_record_check.py
"""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from era_platform.secrets import check_langsmith_tracing, check_required_keys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS: tuple[str, ...] = (
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "TAVILY_API_KEY",
    "LANGSMITH_API_KEY",
    "LANGSMITH_TRACING",
    "LANGSMITH_PROJECT",
)

KEY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Google", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("Groq", re.compile(r"gsk_[A-Za-z0-9]{20,}")),
    ("Tavily", re.compile(r"tvly-[A-Za-z0-9]{20,}")),
    ("LangSmith", re.compile(r"lsv2_(pt|sk)_[A-Za-z0-9]{20,}")),
)


def _load_dotenv() -> None:
    """Load `.env` into the process environment (thin wrapper for testability)."""
    load_dotenv()


def scan_file_for_secrets(path: Path) -> list[str]:
    """Scan a single file's contents for key-shaped patterns.

    Args:
        path: File to scan.

    Returns:
        One description string per match, formatted as
        ``"{path}:{line_number}: possible {provider} key"``. Files that
        cannot be decoded as UTF-8 (binary files) are skipped and yield no
        matches.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        logger.debug("Skipping unreadable file: %s", path)
        return []

    matches: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        for provider, pattern in KEY_PATTERNS:
            if pattern.search(line):
                matches.append(f"{path}:{line_number}: possible {provider} key")

    return matches


def scan_tracked_files_for_secrets(repo_root: Path) -> list[str]:
    """Scan every git-tracked file (excluding `.env`) for key-shaped patterns.

    Args:
        repo_root: Root of the git repository to scan.

    Returns:
        Aggregated match descriptions from :func:`scan_file_for_secrets`
        across all tracked files.
    """
    result = subprocess.run(["git", "ls-files"], cwd=repo_root, capture_output=True, text=True)
    tracked = [line for line in result.stdout.splitlines() if line and line != ".env"]

    matches: list[str] = []
    for relative_path in tracked:
        matches.extend(scan_file_for_secrets(repo_root / relative_path))

    return matches


def check_env_gitignored() -> bool:
    """Confirm `.env` is matched by a gitignore rule.

    Returns:
        True if `git check-ignore .env` succeeds, False otherwise.
    """
    result = subprocess.run(["git", "check-ignore", "-q", ".env"], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(".env is NOT git-ignored — add it to .gitignore before recording.")
        return False

    return True


def check_env_not_in_git_status() -> bool:
    """Confirm `.env` does not appear in `git status` (tracked, staged, or modified).

    Returns:
        True if `.env` is absent from `git status --porcelain`, False otherwise.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", ".env"], capture_output=True, text=True
    )
    if result.stdout.strip():
        logger.error(".env appears in `git status` — it may have been force-added.")
        return False

    return True


def check_env_vars() -> bool:
    """Load `.env` and confirm the Section 2.2 variables are correctly set.

    Returns:
        True if all required keys are present and non-empty AND
        LANGSMITH_TRACING is exactly "true", False otherwise.
    """
    _load_dotenv()
    keys_ok = check_required_keys(REQUIRED_ENV_VARS)
    tracing_ok = check_langsmith_tracing()
    return keys_ok and tracing_ok


def main() -> int:
    """Run every pre-recording check and print a PASS/FAIL summary.

    Returns:
        0 if every check passed, 1 otherwise.
    """
    repo_root = Path.cwd()

    gitignore_ok = check_env_gitignored()
    status_ok = check_env_not_in_git_status()
    secret_matches = scan_tracked_files_for_secrets(repo_root)
    env_ok = check_env_vars()

    for match in secret_matches:
        logger.error("Possible secret found: %s", match)

    checks = (
        (".env is git-ignored", gitignore_ok),
        (".env absent from git status", status_ok),
        ("no key-shaped strings in tracked files", not secret_matches),
        (".env variables configured correctly", env_ok),
    )

    print()
    for label, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {label}")
    print()

    all_passed = all(passed for _, passed in checks)
    print("PASS — safe to start recording." if all_passed else "FAIL — do not record yet.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

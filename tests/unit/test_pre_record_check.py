"""Unit tests for scripts/pre_record_check.py.

Key-shaped fixture strings are built via runtime string concatenation
rather than written as literals in this source file. If a real-looking
literal sat here, both the gitleaks pre-commit hook and this very script's
own tracked-file scan would flag this test file the moment it's committed.
Building the string at runtime keeps the source clean while still
exercising the regex-matching logic against a materialized tmp file.
"""

import logging
import subprocess
from pathlib import Path

import pytest

from scripts import pre_record_check


def _fake_google_key() -> str:
    return "AIza" + "B" * 35


def _fake_groq_key() -> str:
    return "gsk_" + "C" * 24


def _fake_tavily_key() -> str:
    return "tvly-" + "D" * 24


def _fake_langsmith_key() -> str:
    return "lsv2_sk_" + "E" * 24


def test_scan_file_for_secrets_flags_google_key_shaped_string(tmp_path: Path) -> None:
    target = tmp_path / "leaky.py"
    target.write_text(f'API_KEY = "{_fake_google_key()}"\n')

    matches = pre_record_check.scan_file_for_secrets(target)

    assert len(matches) == 1
    assert str(target) in matches[0]
    assert "1" in matches[0]
    assert "Google" in matches[0]


def test_scan_file_for_secrets_flags_groq_key_on_correct_line(tmp_path: Path) -> None:
    target = tmp_path / "leaky.py"
    target.write_text(f'first_line = "nothing here"\nGROQ = "{_fake_groq_key()}"\n')

    matches = pre_record_check.scan_file_for_secrets(target)

    assert len(matches) == 1
    assert ":2:" in matches[0]
    assert "Groq" in matches[0]


def test_scan_file_for_secrets_flags_tavily_key(tmp_path: Path) -> None:
    target = tmp_path / "leaky.env"
    target.write_text(f"TAVILY_API_KEY={_fake_tavily_key()}\n")

    matches = pre_record_check.scan_file_for_secrets(target)

    assert len(matches) == 1
    assert "Tavily" in matches[0]


def test_scan_file_for_secrets_flags_langsmith_key(tmp_path: Path) -> None:
    target = tmp_path / "leaky.env"
    target.write_text(f"LANGSMITH_API_KEY={_fake_langsmith_key()}\n")

    matches = pre_record_check.scan_file_for_secrets(target)

    assert len(matches) == 1
    assert "LangSmith" in matches[0]


def test_scan_file_for_secrets_returns_empty_for_a_clean_file(tmp_path: Path) -> None:
    target = tmp_path / "clean.py"
    target.write_text("def add(a: int, b: int) -> int:\n    return a + b\n")

    matches = pre_record_check.scan_file_for_secrets(target)

    assert matches == []


def test_scan_file_for_secrets_skips_unreadable_binary_file(tmp_path: Path) -> None:
    target = tmp_path / "image.png"
    target.write_bytes(bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x80, 0x81]))

    matches = pre_record_check.scan_file_for_secrets(target)

    assert matches == []


def test_scan_tracked_files_for_secrets_excludes_env_and_aggregates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "clean.py").write_text("x = 1\n")
    leaky = tmp_path / "leaky.py"
    leaky.write_text(f'KEY = "{_fake_google_key()}"\n')
    (tmp_path / ".env").write_text(f"GOOGLE_API_KEY={_fake_google_key()}\n")

    def fake_run(
        args: list[str], cwd: Path | None = None, capture_output: bool = True, text: bool = True
    ) -> subprocess.CompletedProcess[str]:
        assert args[:2] == ["git", "ls-files"]
        return subprocess.CompletedProcess(args, 0, stdout="clean.py\nleaky.py\n.env\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    matches = pre_record_check.scan_tracked_files_for_secrets(tmp_path)

    assert len(matches) == 1
    assert "leaky.py" in matches[0]


def test_check_env_gitignored_true_when_git_check_ignore_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        args: list[str], capture_output: bool = True, text: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, stdout=".env\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert pre_record_check.check_env_gitignored() is True


def test_check_env_gitignored_false_when_git_check_ignore_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        args: list[str], capture_output: bool = True, text: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert pre_record_check.check_env_gitignored() is False


def test_check_env_not_in_git_status_true_when_output_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        args: list[str], capture_output: bool = True, text: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert pre_record_check.check_env_not_in_git_status() is True


def test_check_env_not_in_git_status_false_when_env_appears(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        args: list[str], capture_output: bool = True, text: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, stdout="A  .env\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert pre_record_check.check_env_not_in_git_status() is False


def test_check_env_vars_true_when_all_present_and_tracing_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pre_record_check, "_load_dotenv", lambda: None)
    for name in pre_record_check.REQUIRED_ENV_VARS:
        monkeypatch.setenv(name, "true" if name == "LANGSMITH_TRACING" else "present")

    assert pre_record_check.check_env_vars() is True


def test_check_env_vars_false_when_a_key_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pre_record_check, "_load_dotenv", lambda: None)
    for name in pre_record_check.REQUIRED_ENV_VARS:
        monkeypatch.setenv(name, "true" if name == "LANGSMITH_TRACING" else "present")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    assert pre_record_check.check_env_vars() is False


def test_main_returns_0_when_every_check_passes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(pre_record_check, "check_env_gitignored", lambda: True)
    monkeypatch.setattr(pre_record_check, "check_env_not_in_git_status", lambda: True)
    monkeypatch.setattr(pre_record_check, "scan_tracked_files_for_secrets", lambda root: [])
    monkeypatch.setattr(pre_record_check, "check_env_vars", lambda: True)

    exit_code = pre_record_check.main()

    assert exit_code == 0
    assert "PASS" in capsys.readouterr().out


def test_main_returns_1_when_a_secret_is_found(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(pre_record_check, "check_env_gitignored", lambda: True)
    monkeypatch.setattr(pre_record_check, "check_env_not_in_git_status", lambda: True)
    monkeypatch.setattr(
        pre_record_check,
        "scan_tracked_files_for_secrets",
        lambda root: ["fake.py:1: possible Google key"],
    )
    monkeypatch.setattr(pre_record_check, "check_env_vars", lambda: True)

    with caplog.at_level(logging.ERROR):
        exit_code = pre_record_check.main()

    assert exit_code == 1


def test_main_returns_1_when_env_gitignore_check_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pre_record_check, "check_env_gitignored", lambda: False)
    monkeypatch.setattr(pre_record_check, "check_env_not_in_git_status", lambda: True)
    monkeypatch.setattr(pre_record_check, "scan_tracked_files_for_secrets", lambda root: [])
    monkeypatch.setattr(pre_record_check, "check_env_vars", lambda: True)

    assert pre_record_check.main() == 1

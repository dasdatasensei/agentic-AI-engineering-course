"""Unit tests for era_platform.secrets.

Mirrors the plain-function, typed style of test_research_summariser.py.
No real API keys are ever used here — only synthetic values shaped like
the thing under test (e.g. arbitrary letters standing in for a token).
"""

import logging

import pytest

from era_platform.secrets import (
    check_langsmith_tracing,
    check_required_keys,
    redact,
)


def test_redact_keeps_first_four_and_last_two_characters() -> None:
    value = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"

    result = redact(value)

    assert result.startswith("AIza")
    assert result.endswith("67")
    assert result == "AIza" + "*" * (len(value) - 6) + "67"


def test_redact_masks_entirely_when_string_too_short_to_split_safely() -> None:
    value = "abcdef"

    result = redact(value)

    assert result == "*" * len(value)


def test_redact_handles_empty_string() -> None:
    assert redact("") == ""


def test_check_required_keys_returns_true_when_all_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "present")
    monkeypatch.setenv("GROQ_API_KEY", "present")

    result = check_required_keys(("GOOGLE_API_KEY", "GROQ_API_KEY"))

    assert result is True


def test_check_required_keys_returns_false_when_one_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "present")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    result = check_required_keys(("GOOGLE_API_KEY", "GROQ_API_KEY"))

    assert result is False


def test_check_required_keys_returns_false_when_value_is_empty_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    result = check_required_keys(("GOOGLE_API_KEY",))

    assert result is False


def test_check_required_keys_logs_which_keys_are_missing(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with caplog.at_level(logging.WARNING, logger="era_platform.secrets"):
        check_required_keys(("TAVILY_API_KEY", "GROQ_API_KEY"))

    assert "TAVILY_API_KEY" in caplog.text
    assert "GROQ_API_KEY" in caplog.text


def test_check_langsmith_tracing_true_when_exactly_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    assert check_langsmith_tracing() is True


def test_check_langsmith_tracing_false_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)

    assert check_langsmith_tracing() is False


def test_check_langsmith_tracing_false_when_truthy_but_not_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "True")

    assert check_langsmith_tracing() is False

"""Unit tests for era_platform.generation.summarizer.

Every test drives the summariser with a *fake* LLM client — no network call is
made, which is exactly the point of the :class:`LLMClient` protocol. These
mirror the structure of test_state_schema.py (plain functions, typed, one
behaviour per test) and demonstrate the 2.6 self-correction loop end to end.
"""

import json
from collections.abc import Mapping

import pytest
from pydantic import ValidationError

from era_platform.generation.summarizer import (
    ResearchSummary,
    SummarizationError,
    SummarizerAgent,
)

_VALID_PAYLOAD = {
    "topic": "Caribbean fintech",
    "summary": "Fintech adoption is accelerating across the Caribbean. "
    "Mobile-first banking leads the growth.",
    "key_points": [
        "Mobile banking is the primary driver.",
        "Cross-border payments remain costly.",
        "Regulation is still fragmenting the market.",
    ],
    "entities": ["Central Bank of The Bahamas"],
}


def _json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload)


class _ScriptedLLM:
    """A fake LLMClient that returns preset responses in order and records prompts."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._responses.pop(0)


class _FailingLLM:
    """A fake LLMClient whose call always raises, simulating a transport failure."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, prompt: str) -> str:
        self.calls += 1
        raise RuntimeError("connection reset")


def test_summarize_returns_validated_summary() -> None:
    llm = _ScriptedLLM([_json(_VALID_PAYLOAD)])
    agent = SummarizerAgent(llm)

    result = agent.summarize("Some article about Caribbean fintech.")

    assert isinstance(result, ResearchSummary)
    assert result.topic == "Caribbean fintech"
    assert len(result.key_points) == 3
    assert len(llm.prompts) == 1


def test_source_text_is_included_in_the_prompt() -> None:
    llm = _ScriptedLLM([_json(_VALID_PAYLOAD)])
    agent = SummarizerAgent(llm)

    agent.summarize("UNIQUE-MARKER-TEXT")

    assert "UNIQUE-MARKER-TEXT" in llm.prompts[0]


def test_self_corrects_after_a_validation_error() -> None:
    too_few = {**_VALID_PAYLOAD, "key_points": ["only", "two"]}
    llm = _ScriptedLLM([_json(too_few), _json(_VALID_PAYLOAD)])
    agent = SummarizerAgent(llm)

    result = agent.summarize("Some article.")

    assert len(result.key_points) == 3
    # Two attempts were made, and the second prompt fed the error back to the model.
    assert len(llm.prompts) == 2
    assert "could not be parsed" in llm.prompts[1]
    assert "key_points" in llm.prompts[1]


def test_recovers_from_json_wrapped_in_markdown_fences() -> None:
    fenced = f"Sure! Here is the summary:\n```json\n{_json(_VALID_PAYLOAD)}\n```"
    llm = _ScriptedLLM([fenced])
    agent = SummarizerAgent(llm)

    result = agent.summarize("Some article.")

    assert result.topic == "Caribbean fintech"


def test_gives_up_after_exhausting_retries() -> None:
    invalid = _json({**_VALID_PAYLOAD, "key_points": ["one"]})
    llm = _ScriptedLLM([invalid, invalid, invalid])
    agent = SummarizerAgent(llm, max_retries=2)

    with pytest.raises(SummarizationError, match="after 3 attempts"):
        agent.summarize("Some article.")

    assert len(llm.prompts) == 3


def test_llm_transport_failure_is_wrapped_and_not_retried() -> None:
    llm = _FailingLLM()
    agent = SummarizerAgent(llm, max_retries=3)

    with pytest.raises(SummarizationError, match="LLM call failed"):
        agent.summarize("Some article.")

    # A broken connection is not something re-asking can fix, so we call once.
    assert llm.calls == 1


def test_empty_text_raises_before_calling_the_llm() -> None:
    llm = _ScriptedLLM([])
    agent = SummarizerAgent(llm)

    with pytest.raises(SummarizationError, match="empty text"):
        agent.summarize("   ")

    assert llm.prompts == []


def test_key_points_lower_bound_is_enforced_by_the_schema() -> None:
    with pytest.raises(ValidationError):
        ResearchSummary(topic="t", summary="s", key_points=["only", "two"], entities=[])


def test_key_points_upper_bound_is_enforced_by_the_schema() -> None:
    with pytest.raises(ValidationError):
        ResearchSummary(
            topic="t",
            summary="s",
            key_points=["1", "2", "3", "4", "5", "6"],
            entities=[],
        )


def test_entities_defaults_to_empty_list() -> None:
    summary = ResearchSummary(topic="t", summary="s", key_points=["a", "b", "c"])

    assert summary.entities == []

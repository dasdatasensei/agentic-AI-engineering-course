"""Unit tests for the Section 4 research agent (Exercise 4.E).

Every test runs fully offline. The ReAct loop is driven by a ``_ScriptedLLM``
that emits preset JSON decisions, and the agent's tools are lightweight fakes
built with :func:`era_platform.agents.tools.tool` — so there is no live model, no
Tavily call, no real subprocess exec, and no ChromaDB. This is the same
fake-dependency discipline as ``test_research_summariser.py`` and
``test_knowledge_retrieval.py``, applied to tool-using agents (lecture 4.8).

The one real component exercised directly is the code-sandbox *safety check*
(:func:`assert_code_is_safe`) — a pure static AST walk that runs nothing, so it
needs no subprocess.
"""

from __future__ import annotations

import json

import pytest

from era_platform.agents.base import AgentError
from era_platform.agents.research_agent import ResearchAgent, ResearchResult
from era_platform.agents.tools import (
    CodeSafetyError,
    FunctionTool,
    SearchHit,
    WebSearchTool,
    assert_code_is_safe,
    tool,
)
from era_platform.agents.tools.base import ToolError


class _ScriptedLLM:
    """A fake LLMClient that returns preset responses in order and records prompts."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        # Repeat the last response if the loop asks more than scripted (keeps a
        # never-finishing script simple for the max-steps test).
        return self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]


def _use(tool_name: str, thought: str = "using a tool", **args: object) -> str:
    return json.dumps({"thought": thought, "action": tool_name, "action_input": args})


def _finish(answer: str, thought: str = "done") -> str:
    return json.dumps({"thought": thought, "action": "finish", "action_input": {"answer": answer}})


@tool(
    name="echo",
    description="Echo the text back.",
    parameters={"text": "the text to echo"},
)
def _echo(text: str) -> str:
    return f"echo: {text}"


def _flaky_tool(fail_times: int) -> tuple[FunctionTool, dict[str, int]]:
    """A tool that raises ToolError ``fail_times`` times, then succeeds."""
    calls = {"n": 0}

    @tool(name="flaky", description="Fails then succeeds.", parameters={})
    def _flaky() -> str:
        calls["n"] += 1
        if calls["n"] <= fail_times:
            raise ToolError(f"transient failure #{calls['n']}")
        return "flaky succeeded"

    return _flaky, calls


# ── Tool selection (4.2/4.3) ───────────────────────────────────────────────


async def test_agent_selects_the_named_tool_and_records_the_observation() -> None:
    llm = _ScriptedLLM([_use("echo", text="hello"), _finish("the tool said hello")])
    agent = ResearchAgent(llm, [_echo])

    result = await agent.research("say hello")

    assert isinstance(result, ResearchResult)
    assert result.stopped_reason == "finished"
    assert result.tools_used == ["echo"]
    assert result.answer == "the tool said hello"
    # The tool actually ran and its observation is in the trace.
    assert any(step.observation == "echo: hello" for step in result.steps)


async def test_unknown_tool_is_fed_back_not_raised() -> None:
    llm = _ScriptedLLM([_use("does_not_exist"), _finish("recovered")])
    agent = ResearchAgent(llm, [_echo])

    result = await agent.research("q")

    assert result.answer == "recovered"
    assert result.tools_used == []  # the bad call never counts as a used tool
    assert any("unknown tool" in step.observation for step in result.steps)


async def test_malformed_json_is_fed_back_as_observation() -> None:
    llm = _ScriptedLLM(["not json at all", _finish("recovered after garbage")])
    agent = ResearchAgent(llm, [_echo])

    result = await agent.research("q")

    assert result.answer == "recovered after garbage"
    assert any("valid JSON" in step.observation for step in result.steps)


# ── Retry on tool failure (4.7) ────────────────────────────────────────────


async def test_flaky_tool_is_retried_then_succeeds() -> None:
    flaky, calls = _flaky_tool(fail_times=2)
    llm = _ScriptedLLM([_use("flaky"), _finish("got it")])
    agent = ResearchAgent(llm, [flaky], tool_retries=3)

    result = await agent.research("q")

    assert calls["n"] == 3  # two failures + one success
    assert any(step.observation == "flaky succeeded" for step in result.steps)
    assert result.tools_used == ["flaky"]


async def test_tool_failing_past_retry_budget_is_fed_back_not_raised() -> None:
    flaky, calls = _flaky_tool(fail_times=99)  # never succeeds
    llm = _ScriptedLLM([_use("flaky"), _finish("gave up on the tool")])
    agent = ResearchAgent(llm, [flaky], tool_retries=2)

    result = await agent.research("q")

    assert calls["n"] == 2  # exactly the retry budget, then feed the error back
    assert any("failed" in step.observation.lower() for step in result.steps)
    assert result.answer == "gave up on the tool"


# ── Max-steps termination (4.3) ────────────────────────────────────────────


async def test_never_finishing_agent_stops_at_max_steps() -> None:
    # A single scripted response the stub repeats every step: the agent keeps
    # calling the tool and never emits a finish, so it is cut off at max_steps.
    llm = _ScriptedLLM([_use("echo", text="loop")])
    agent = ResearchAgent(llm, [_echo], max_steps=3)

    result = await agent.research("q")

    assert result.stopped_reason == "max_steps"
    assert len([s for s in result.steps if s.action == "echo"]) == 3
    assert result.answer  # a non-empty forced answer, not a crash


async def test_max_steps_forced_answer_falls_back_to_last_observation() -> None:
    # One tool step, then the forced-answer call returns blank, so the agent
    # falls back to the most recent observation instead of an empty answer.
    llm = _ScriptedLLM([_use("echo", text="hi"), "   "])
    agent = ResearchAgent(llm, [_echo], max_steps=1)

    result = await agent.research("q")

    assert result.stopped_reason == "max_steps"
    assert result.answer == "echo: hi"


# ── validate_output() (BaseAgent contract) ─────────────────────────────────


async def test_validate_output_accepts_a_well_formed_result() -> None:
    llm = _ScriptedLLM([_finish("a real answer")])
    agent = ResearchAgent(llm, [_echo])

    # safe_run() runs validate_output() internally and must not raise.
    result = await agent.safe_run(question="q")

    assert result.answer == "a real answer"


def test_validate_output_rejects_empty_answer() -> None:
    agent = ResearchAgent(_ScriptedLLM([_finish("x")]), [_echo])
    bad = ResearchResult(
        question="q", answer="   ", tools_used=[], steps=[], stopped_reason="finished"
    )
    with pytest.raises(AgentError, match="empty answer"):
        agent.validate_output(bad)


def test_validate_output_rejects_unknown_tool_reference() -> None:
    agent = ResearchAgent(_ScriptedLLM([_finish("x")]), [_echo])
    bad = ResearchResult(
        question="q",
        answer="fine",
        tools_used=["ghost_tool"],
        steps=[],
        stopped_reason="finished",
    )
    with pytest.raises(AgentError, match="unknown tools"):
        agent.validate_output(bad)


async def test_empty_question_raises_agent_error() -> None:
    agent = ResearchAgent(_ScriptedLLM([_finish("x")]), [_echo])
    with pytest.raises(AgentError, match="non-empty 'question'"):
        await agent.research("  ")


# ── Construction guards ────────────────────────────────────────────────────


def test_agent_requires_at_least_one_tool() -> None:
    with pytest.raises(ValueError, match="at least one tool"):
        ResearchAgent(_ScriptedLLM([]), [])


def test_agent_rejects_duplicate_tool_names() -> None:
    with pytest.raises(ValueError, match="duplicate tool name"):
        ResearchAgent(_ScriptedLLM([]), [_echo, _echo])


# ── Code sandbox safety check (4.6) ────────────────────────────────────────


def test_assert_code_is_safe_allows_plain_arithmetic() -> None:
    assert_code_is_safe("print(sum(range(10)) * 2)")  # must not raise


@pytest.mark.parametrize(
    "snippet",
    [
        "import os",
        "from sys import exit",
        "open('/etc/passwd')",
        "().__class__.__bases__",
        "__import__('os').system('ls')",
        "eval('2+2')",
    ],
)
def test_assert_code_is_safe_rejects_dangerous_snippets(snippet: str) -> None:
    with pytest.raises(CodeSafetyError):
        assert_code_is_safe(snippet)


# ── Web search fallback (4.5) ──────────────────────────────────────────────


class _FakeProvider:
    def __init__(self, *, hits: list[SearchHit] | None = None, boom: bool = False) -> None:
        self._hits = hits or []
        self._boom = boom
        self.calls = 0

    def search(self, query: str, *, max_results: int) -> list[SearchHit]:
        self.calls += 1
        if self._boom:
            raise RuntimeError("provider down")
        return self._hits


def test_web_search_falls_back_when_primary_fails() -> None:
    primary = _FakeProvider(boom=True)
    fallback = _FakeProvider(hits=[SearchHit(title="T", url="u", content="a fallback result")])
    web = WebSearchTool(primary, fallback)

    observation = web.run(query="anything")

    assert primary.calls == 1 and fallback.calls == 1
    assert "a fallback result" in observation


def test_web_search_raises_when_all_providers_fail() -> None:
    web = WebSearchTool(_FakeProvider(boom=True), _FakeProvider(boom=True))
    with pytest.raises(ToolError, match="all web search providers failed"):
        web.run(query="anything")

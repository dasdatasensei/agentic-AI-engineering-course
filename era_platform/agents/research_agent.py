"""ResearchAgent — the first concrete :class:`BaseAgent`, a ReAct tool-user (4.E).

Created: 2026-07-02
Last updated: 2026-07-02

Exercise 4.E is where Section 4's threads come together into one agent:

* **Tools (4.1–4.2, 4.5, 4.6)** — the agent is handed a list of
  :class:`~era_platform.agents.tools.base.Tool`s (web search, code execution,
  knowledge search) and selects among them by name.
* **The ReAct loop (4.3)** — :meth:`ResearchAgent.run` iterates
  *reason → act → observe* until the model decides it can answer, bounded by a
  step limit so a confused loop cannot run forever.
* **Memory (4.4)** — every ``thought``/``action``/``observation`` is retained as a
  scratchpad and replayed into each prompt, so later reasoning can build on
  earlier observations. This is deliberately the *simple* version; the durable,
  compaction-aware treatment is a LangGraph-era concern (Section 5.6).
* **Error handling (4.7)** — a failing tool call is retried with backoff
  (``tenacity``) and, if it still fails, fed back to the model as an observation
  instead of crashing the loop — the spirit of 2.6's re-ask pattern applied to
  tool failures rather than validation failures.

This is the first class in the course to actually subclass
:class:`~era_platform.agents.base.BaseAgent`: 2.E's summariser and 3.P's
``KnowledgeRetrievalAgent`` both explicitly declined to, deferring the async,
tool-using contract to here. Subclassing it means :meth:`run` and
:meth:`validate_output` are implemented, and the logging + error boundary in
``BaseAgent.safe_run`` come for free.

It depends only on the tiny :class:`~era_platform.generation.summarizer.LLMClient`
protocol and on ``Tool`` objects, so the whole loop is driven by a scripted fake
LLM and fake tools in tests — no live model, no network, no subprocess.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field
from tenacity import (
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from era_platform.agents.base import AgentError, BaseAgent
from era_platform.agents.tools.base import Tool, ToolError
from era_platform.generation.summarizer import LLMClient

logger = logging.getLogger(__name__)

DEFAULT_MAX_STEPS = 6
DEFAULT_TOOL_RETRIES = 3

# Prompts stay as named module-level constants until
# era_platform/generation/prompt_templates.py exists (CLAUDE.md no-inline-prompts
# rule / 2.E fallback) — the later migration is then mechanical.
RESEARCH_SYSTEM_PROMPT = (
    "You are a research agent that answers questions by reasoning step by step and "
    "using tools. On each step you think about what to do next, then either call ONE "
    "tool or finish with a final answer.\n\n"
    "Respond with ONLY a single JSON object and nothing else, in one of two shapes:\n"
    '  To use a tool:  {"thought": "<your reasoning>", "action": "<tool_name>", '
    '"action_input": {<arguments>}}\n'
    '  To finish:      {"thought": "<your reasoning>", "action": "finish", '
    '"action_input": {"answer": "<your final answer>"}}\n\n'
    "Rules:\n"
    "- Use a tool only when you need information you do not already have.\n"
    "- Prefer knowledge_search for anything the user's own documents may cover; use "
    "web_search for current or external facts.\n"
    "- When you have enough to answer, use the finish action.\n"
    "- Base your final answer only on tool observations and the question."
)


class ReActStep(BaseModel):
    """One turn of the loop: what the agent thought, did, and observed.

    The retained sequence of these *is* the agent's working memory (lecture 4.4):
    it is replayed into every subsequent prompt so the model can reason over what
    it has already found.
    """

    thought: str = Field(description="The agent's reasoning before acting.")
    action: str = Field(description="The tool selected, or 'finish'.")
    action_input: dict[str, Any] = Field(
        default_factory=dict, description="Arguments passed to the tool (or the final answer)."
    )
    observation: str = Field(description="The tool's result, or an error/parse note fed back in.")


class ResearchResult(BaseModel):
    """The typed contract a research run returns.

    Validated by :meth:`ResearchAgent.validate_output` before the orchestrator
    ever sees it: a non-empty answer, plus a trace referencing only real tools.
    """

    question: str = Field(description="The question the agent was asked.")
    answer: str = Field(description="The agent's final answer.")
    tools_used: list[str] = Field(
        default_factory=list,
        description="Distinct tool names invoked during the run, in first-use order.",
    )
    steps: list[ReActStep] = Field(
        default_factory=list, description="The full reason→act→observe trace, for inspection."
    )
    stopped_reason: Literal["finished", "max_steps"] = Field(
        description="Whether the agent finished on its own or was cut off at the step limit."
    )


class ResearchAgent(BaseAgent):
    """A single ReAct agent that answers questions using a set of tools.

    Args mirror the four Section-4 concerns: the tools it may use, how many
    reason→act→observe steps it may take, and how hard to retry a flaky tool.
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: list[Tool],
        *,
        name: str = "research",
        max_steps: int = DEFAULT_MAX_STEPS,
        tool_retries: int = DEFAULT_TOOL_RETRIES,
        system_prompt: str = RESEARCH_SYSTEM_PROMPT,
    ) -> None:
        """Build the research agent.

        Args:
            llm: Anything satisfying :class:`LLMClient` (Gemini in the course
                default; a scripted fake in tests).
            tools: The tools the agent may select. Names must be unique.
            name: Agent name, used for logging (see ``BaseAgent``).
            max_steps: Hard cap on reason→act→observe iterations.
            tool_retries: Attempts per tool call before the failure is fed back as
                an observation.
            system_prompt: The ReAct instructions; override to customise behaviour.

        Raises:
            ValueError: If ``tools`` is empty, tool names collide, or a bound is
                not positive.
        """
        if not tools:
            raise ValueError("ResearchAgent needs at least one tool")
        if max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if tool_retries <= 0:
            raise ValueError("tool_retries must be positive")
        registry: dict[str, Tool] = {}
        for candidate in tools:
            if candidate.name in registry:
                raise ValueError(f"duplicate tool name: {candidate.name!r}")
            registry[candidate.name] = candidate

        super().__init__(name)
        self._llm = llm
        self._tools = registry
        self._max_steps = max_steps
        self._tool_retries = tool_retries
        self._system_prompt = system_prompt

    async def run(self, **kwargs: Any) -> ResearchResult:
        """Answer the ``question`` keyword argument via the ReAct loop.

        Accepts ``**kwargs`` to satisfy ``BaseAgent.run``'s signature; the typed
        :meth:`research` wrapper is the ergonomic entry point.

        Raises:
            AgentError: If no non-empty ``question`` is supplied.
        """
        question = kwargs.get("question")
        if not isinstance(question, str) or not question.strip():
            raise AgentError("ResearchAgent.run requires a non-empty 'question'")
        return self._react(question.strip())

    async def research(self, question: str) -> ResearchResult:
        """Typed convenience wrapper over :meth:`run`."""
        return await self.run(question=question)

    def validate_output(self, output: Any) -> bool:
        """Enforce the research contract: a non-empty answer plus a sane trace.

        A "valid" research result is one the orchestrator can actually use: it has
        a non-empty answer, and every tool it claims to have used is one this agent
        actually owns. Raises :class:`AgentError` (per ``BaseAgent``) rather than
        returning ``False`` so ``safe_run`` surfaces the failure.
        """
        if not isinstance(output, ResearchResult):
            raise AgentError(f"expected ResearchResult, got {type(output).__name__}")
        if not output.answer.strip():
            raise AgentError("research produced an empty answer")
        unknown = [name for name in output.tools_used if name not in self._tools]
        if unknown:
            raise AgentError(f"result references unknown tools: {unknown}")
        return True

    # ── ReAct loop ─────────────────────────────────────────────────────────────

    def _react(self, question: str) -> ResearchResult:
        steps: list[ReActStep] = []
        tools_used: list[str] = []

        for step_number in range(1, self._max_steps + 1):
            raw = self._llm.invoke(self._build_prompt(question, steps))
            decision = self._parse_decision(raw)

            if decision is None:
                # Malformed action — feed the parse error back and let the model retry.
                steps.append(
                    ReActStep(
                        thought="(unparseable model response)",
                        action="_invalid",
                        observation=(
                            "Your response was not a single valid JSON object with "
                            '"thought"/"action"/"action_input". Respond again in the '
                            "required format."
                        ),
                    )
                )
                continue

            thought, action, action_input = decision

            if action == "finish":
                answer = str(action_input.get("answer", "")).strip()
                self._logger.info("agent finished after %d step(s)", step_number)
                steps.append(
                    ReActStep(
                        thought=thought,
                        action="finish",
                        action_input=action_input,
                        observation=answer,
                    )
                )
                return ResearchResult(
                    question=question,
                    answer=answer,
                    tools_used=tools_used,
                    steps=steps,
                    stopped_reason="finished",
                )

            observation = self._act(action, action_input)
            if action in self._tools and action not in tools_used:
                tools_used.append(action)
            steps.append(
                ReActStep(
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation=observation,
                )
            )

        # Ran out of steps without a finish — force a best-effort answer from the
        # trace so the loop always terminates with something usable.
        self._logger.warning(
            "hit max_steps=%d without finishing; forcing an answer", self._max_steps
        )
        answer = self._forced_answer(question, steps)
        return ResearchResult(
            question=question,
            answer=answer,
            tools_used=tools_used,
            steps=steps,
            stopped_reason="max_steps",
        )

    def _act(self, action: str, action_input: dict[str, Any]) -> str:
        """Dispatch one tool call, with retry/backoff, returning the observation.

        An unknown tool or a tool that keeps failing does not raise — the problem
        is returned as an observation string so the agent can recover on its next
        step (lecture 4.7).
        """
        tool = self._tools.get(action)
        if tool is None:
            available = ", ".join(sorted(self._tools)) or "(none)"
            return f"Error: unknown tool {action!r}. Available tools: {available}."
        try:
            return self._call_tool_with_retry(tool, action_input)
        except ToolError as exc:
            self._logger.warning("tool %s failed after retries: %s", action, exc)
            return f"Error: tool {action!r} failed ({exc}). Consider another approach."

    def _call_tool_with_retry(self, tool: Tool, action_input: dict[str, Any]) -> str:
        """Invoke ``tool`` with exponential-backoff retries on :class:`ToolError`.

        Uses ``tenacity`` (not a hand-rolled loop): retry only transient
        ``ToolError``s; a bad-argument ``TypeError`` surfaces immediately rather
        than being retried pointlessly.

        Raises:
            ToolError: If every attempt fails.
        """
        retrying = Retrying(
            stop=stop_after_attempt(self._tool_retries),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(ToolError),
            reraise=True,
        )
        try:
            return retrying(tool.run, **action_input)
        except TypeError as exc:  # wrong/missing arguments from the model
            raise ToolError(f"invalid arguments for {tool.name!r}: {exc}") from exc
        except RetryError as exc:  # pragma: no cover - reraise=True makes this unlikely
            raise ToolError(f"tool {tool.name!r} failed after retries: {exc}") from exc

    def _forced_answer(self, question: str, steps: list[ReActStep]) -> str:
        """Ask the model to answer *now* from the trace when steps are exhausted."""
        prompt = (
            f"{self._system_prompt}\n\n"
            f"QUESTION: {question}\n\n"
            f"{self._render_scratchpad(steps)}\n\n"
            "You have run out of steps. Using only the observations above, write the "
            "best final answer you can now, as plain text (no JSON)."
        )
        try:
            answer = self._llm.invoke(prompt).strip()
        except Exception as exc:  # noqa: BLE001 — fall back to the last observation
            self._logger.error("forced-answer LLM call failed: %s", exc)
            answer = ""
        if answer:
            return answer
        last = next((s.observation for s in reversed(steps) if s.observation), "")
        return last or "I was unable to complete the research within the step limit."

    # ── Prompt / parsing helpers ───────────────────────────────────────────────

    def _build_prompt(self, question: str, steps: list[ReActStep]) -> str:
        tool_specs = "\n".join(tool.render_spec() for tool in self._tools.values())
        return (
            f"{self._system_prompt}\n\n"
            f"AVAILABLE TOOLS:\n{tool_specs}\n\n"
            f"QUESTION: {question}\n\n"
            f"{self._render_scratchpad(steps)}\n\n"
            "What is your next step? Respond with only the JSON object."
        )

    @staticmethod
    def _render_scratchpad(steps: list[ReActStep]) -> str:
        if not steps:
            return "SCRATCHPAD: (empty — this is your first step)"
        lines = ["SCRATCHPAD (your work so far):"]
        for i, step in enumerate(steps, start=1):
            lines.append(f"Step {i} thought: {step.thought}")
            if step.action not in {"finish", "_invalid"}:
                lines.append(f"Step {i} action: {step.action}({json.dumps(step.action_input)})")
            lines.append(f"Step {i} observation: {step.observation}")
        return "\n".join(lines)

    def _parse_decision(self, raw: str) -> tuple[str, str, dict[str, Any]] | None:
        """Extract ``(thought, action, action_input)`` from a raw model response.

        Tolerant of prose or ```` ```json ```` fences (takes the first ``{`` to the
        last ``}``, like the 2.E summariser). Returns ``None`` when no valid
        decision can be parsed, so the caller can feed the error back as an
        observation rather than crash.
        """
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None

        action = data.get("action")
        if not isinstance(action, str) or not action:
            return None
        thought = data.get("thought", "")
        thought = thought if isinstance(thought, str) else str(thought)
        action_input = data.get("action_input", {})
        if not isinstance(action_input, dict):
            return None
        return thought, action, action_input

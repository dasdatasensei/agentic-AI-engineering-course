"""Exercise 4.E — starter.

Build a research agent that answers a question by reasoning step by step and
calling tools (the ReAct loop). Fill in every ``TODO`` below. This is a
standalone practice file — build it yourself, then compare against the packaged
reference in ``era_platform/agents/`` (``research_agent.py`` + ``tools/``).

You depend on two tiny abstractions so you can test with fakes and never hit a
live API:

  * ``Tool`` — a named, described, callable capability (lectures 4.1–4.2).
  * ``LLMClient`` — the same ``invoke(prompt) -> str`` protocol as 2.E / 3.E.

Concepts you are applying (see the lectures if you get stuck):
  * 4.1/4.2 — a tool is a name + description + parameter schema + a callable.
  * 4.3 — the ReAct loop: reason → act → observe → repeat, bounded by max-steps.
  * 4.4 — memory: keep the step history and replay it into each prompt.
  * 4.7 — error handling: retry a flaky tool (tenacity), then feed the failure
    back as an observation instead of crashing the loop.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol

# You'll add these as you implement the TODOs below:
#   import json                              # to parse the model's JSON decision
#   from tenacity import (                   # for the retry-on-tool-failure path
#       Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential,
#   )

logger = logging.getLogger(__name__)

DEFAULT_MAX_STEPS = 6
DEFAULT_TOOL_RETRIES = 3

# Keep prompts as named module-level constants (not buried string literals), per
# CLAUDE.md's no-inline-prompts rule.
SYSTEM_PROMPT = (
    "You are a research agent. On each step, think, then either call ONE tool or "
    "finish. Respond with ONLY a JSON object:\n"
    '  Use a tool:  {"thought": "...", "action": "<tool_name>", "action_input": {...}}\n'
    '  Finish:      {"thought": "...", "action": "finish", "action_input": {"answer": "..."}}'
)


class ToolError(Exception):
    """Raise this when a tool cannot complete its call."""


class LLMClient(Protocol):
    """The same protocol as Exercise 2.E: ``invoke(prompt) -> raw text``."""

    def invoke(self, prompt: str) -> str: ...


class Tool(ABC):
    """A named, described, callable capability the agent can select and run.

    TODO:
      1. Store ``name``, ``description``, and ``parameters`` (a ``{arg: what_it_is}``
         schema) so the agent can describe the tool to its LLM.
      2. Declare ``run(**kwargs) -> str`` as an ``@abstractmethod``.
      3. Add ``render_spec() -> str`` returning a one-line description the agent
         can drop into its prompt (e.g. ``- web_search(query) — Search the web.``).
    """

    def __init__(self, name: str, description: str, parameters: dict[str, str]) -> None:
        raise NotImplementedError("Store name/description/parameters")

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        """Execute the tool and return its observation as text."""
        raise NotImplementedError


class FunctionTool(Tool):
    """A ``Tool`` backed by a plain callable — the simple, stateless case (4.2).

    TODO:
      1. Store the wrapped ``func`` (plus name/description/parameters via super()).
      2. In ``run``, call ``func(**kwargs)``; wrap any non-``ToolError`` exception
         in ``ToolError`` so the agent sees one consistent failure type.
    """

    def run(self, **kwargs: Any) -> str:
        raise NotImplementedError("Call the wrapped function, normalising errors to ToolError")


class ReActAgent:
    """A single agent that answers a question by looping reason → act → observe.

    You are given an ``LLMClient`` and a list of ``Tool``s. (The packaged
    reference subclasses ``era_platform.agents.BaseAgent`` and is async; here,
    build a plain synchronous loop first to understand the mechanics.)
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: list[Tool],
        *,
        max_steps: int = DEFAULT_MAX_STEPS,
        tool_retries: int = DEFAULT_TOOL_RETRIES,
    ) -> None:
        # TODO: reject an empty tool list; index tools by name for dispatch.
        self._llm = llm
        self._tools = {tool.name: tool for tool in tools}
        self._max_steps = max_steps
        self._tool_retries = tool_retries

    def run(self, question: str) -> str:
        """Answer ``question`` via the ReAct loop; return the final answer text.

        TODO:
          1. Keep a ``steps`` list of (thought, action, action_input, observation)
             — this is the agent's memory (4.4).
          2. Loop up to ``max_steps`` times. Each iteration:
             a. Build a prompt from SYSTEM_PROMPT + the tool specs + the question +
                the scratchpad so far, and ``invoke`` the LLM.
             b. Parse the JSON decision (tolerate prose/fences: first ``{`` to last
                ``}``). If it won't parse, record an observation telling the model
                to fix its format, and continue.
             c. If ``action == "finish"``, return ``action_input["answer"]``.
             d. Otherwise dispatch the tool by name (see ``_act``) and record the
                observation.
          3. If you fall out of the loop without finishing, return a best-effort
             answer (e.g. the last observation) — never loop forever.
        """
        raise NotImplementedError("Implement the ReAct loop")

    def _act(self, action: str, action_input: dict[str, Any]) -> str:
        """Run one tool call with retry; return an observation (never raise).

        TODO:
          1. Look up the tool by ``action``. If unknown, return an error
             observation listing the available tools (don't raise).
          2. Otherwise call the tool via ``_call_with_retry``. If it still fails
             after retries, return an error observation so the agent can recover.
        """
        raise NotImplementedError("Dispatch the tool, feeding failures back as observations")

    def _call_with_retry(self, tool: Tool, action_input: dict[str, Any]) -> str:
        """Invoke ``tool.run(**action_input)`` with exponential backoff on ToolError.

        Use ``tenacity`` (already imported) — NOT a hand-rolled loop. Retry only
        ``ToolError`` so a bad-argument ``TypeError`` surfaces immediately.

        TODO: build a ``Retrying`` controller (``stop_after_attempt`` +
        ``wait_exponential`` + ``retry_if_exception_type(ToolError)``, ``reraise=True``)
        and call ``retrying(tool.run, **action_input)``.
        """
        raise NotImplementedError("Wrap the tool call in tenacity retry")

    @staticmethod
    def _parse_decision(raw: str) -> tuple[str, str, dict[str, Any]] | None:
        """Extract (thought, action, action_input) from a raw model response.

        TODO: take the span from the first ``{`` to the last ``}``, ``json.loads``
        it, and return the three fields — or ``None`` if anything is missing/invalid
        so the caller can feed the error back.
        """
        raise NotImplementedError("Parse the JSON decision tolerantly")

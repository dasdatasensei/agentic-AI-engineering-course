"""Section 4 exercise — Build a research agent with 3 tools from scratch.

No LangGraph yet. This is a plain ReAct loop you write by hand: the LLM
proposes an action, you execute it, feed the observation back, repeat until
the LLM signals it's done. Understanding this loop without a framework
makes Section 5's "why graphs?" lecture land much harder.

Tools to implement: web search (Tavily + DuckDuckGo fallback), a simple
calculator, and a "finish" tool the agent calls when it has its answer.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class Tool:
    """A single callable tool the agent can invoke, with a name and
    description the LLM uses to decide when to call it.
    """

    name: str
    description: str
    func: Callable[..., Any]


@dataclass
class AgentMemory:
    """Tracks the running history of thoughts, actions, and observations
    for one agent run. See Lecture 4.4 for the summarisation strategy you'll
    eventually want once this grows long.
    """

    history: list[dict[str, str]] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})


def web_search_tool(query: str) -> str:
    """TODO: implement using Tavily, falling back to DuckDuckGo if the
    Tavily free-tier credits are exhausted (see Lecture 4.5).
    """
    raise NotImplementedError("Implement web_search_tool")


def calculator_tool(expression: str) -> str:
    """TODO: implement a safe arithmetic evaluator — do NOT use raw eval().
    Lecture 4.6 covers why and what a safer alternative looks like.
    """
    raise NotImplementedError("Implement calculator_tool")


def run_react_loop(question: str, tools: list[Tool], max_steps: int = 8) -> str:
    """TODO: implement the Reason -> Act -> Observe loop described in
    Lecture 4.3. Each iteration: ask the LLM what to do next given the
    history so far, execute the chosen tool, append the observation,
    repeat until the LLM calls 'finish' or max_steps is reached.

    Wrap tool execution in error handling per Lecture 4.7 — a single
    failing tool call should not crash the whole loop.
    """
    raise NotImplementedError("Implement run_react_loop")


if __name__ == "__main__":
    tools = [
        Tool("web_search", "Search the web for current information", web_search_tool),
        Tool("calculator", "Evaluate a math expression", calculator_tool),
    ]
    answer = run_react_loop("What is the population of Jamaica times 2?", tools)
    logger.info("Final answer: %s", answer)

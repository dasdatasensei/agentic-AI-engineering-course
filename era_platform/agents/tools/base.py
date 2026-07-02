"""The tool abstraction every ERA agent tool implements — Section 4 (lectures 4.1–4.2).

Created: 2026-07-02
Last updated: 2026-07-02

Lecture 4.1 asks "what is a tool?" (a named, described, callable side effect) and
4.2 covers "building and registering tools: decorators and schemas". This module
is the payoff of both: a tiny :class:`Tool` contract the ReAct agent
(:mod:`era_platform.agents.research_agent`) can enumerate, describe to its LLM,
and invoke uniformly — plus a :func:`tool` decorator that turns a plain function
into one, which is what "decorators and schemas" means in practice.

A tool exposes three things the agent's LLM call needs to *select* it and fill in
its arguments — a ``name``, a ``description``, and a ``parameters`` schema (arg
name → what it is) — and one thing the agent needs to *act*: :meth:`Tool.run`.

Deliberately minimal. The ``parameters`` schema is ``dict[str, str]`` (name →
description), not full JSON Schema: it is exactly enough for the LLM to produce a
JSON ``action_input``, and it keeps the surface tests must fake tiny — the same
"smallest honest interface" discipline as :class:`~era_platform.rag.embeddings.Embedder`
and :class:`~era_platform.generation.summarizer.LLMClient`.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class ToolError(Exception):
    """Raised when a tool cannot complete its call.

    This is the boundary the agent catches: a tool that fails wraps the cause in
    :class:`ToolError` (rather than leaking a provider/SDK exception) so the ReAct
    loop can either retry it (lecture 4.7) or feed the failure back as an
    observation and let the model choose another approach.
    """


class Tool(ABC):
    """A named, described, callable capability an agent can select and invoke.

    Subclasses set ``name``/``description``/``parameters`` (via ``super().__init__``)
    and implement :meth:`run`. The agent never imports a concrete tool directly in
    its reasoning path — it holds a list of :class:`Tool` objects, renders their
    specs into the prompt, and dispatches by name. That indirection is what lets
    the same loop drive web search, code execution, and knowledge retrieval
    without knowing anything about any of them.
    """

    def __init__(self, name: str, description: str, parameters: dict[str, str]) -> None:
        """Initialise the shared tool metadata.

        Args:
            name: The identifier the LLM uses to select this tool. Must be unique
                within an agent's tool set.
            description: One line telling the model what the tool does and when to
                reach for it.
            parameters: Argument schema as ``{arg_name: what_it_is}``. Empty for a
                no-argument tool.
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self._logger = logging.getLogger(f"era_platform.agents.tools.{name}")

    @abstractmethod
    def run(self, **kwargs: Any) -> str:
        """Execute the tool and return its observation as text.

        Args:
            **kwargs: The arguments named in :attr:`parameters`, as chosen by the
                agent's LLM.

        Returns:
            A human/LLM-readable string the agent records as the observation.

        Raises:
            ToolError: If the tool cannot complete the call.
        """
        raise NotImplementedError

    def render_spec(self) -> str:
        """Render a single-line spec for this tool, for the ReAct system prompt.

        Example::

            - web_search(query) — Search the web for current information.
              (args: query: the search query)
        """
        signature = ", ".join(self.parameters) or ""
        arg_docs = "; ".join(f"{name}: {desc}" for name, desc in self.parameters.items())
        arg_suffix = f" (args: {arg_docs})" if arg_docs else " (no arguments)"
        return f"- {self.name}({signature}) — {self.description}{arg_suffix}"


class FunctionTool(Tool):
    """A :class:`Tool` backed by a plain callable — the target of :func:`tool`.

    Lets the "decorators and schemas" idea (4.2) work for simple, stateless tools:
    write a function, describe its arguments, and get a registrable tool. Stateful
    tools that hold injected clients (web search, knowledge retrieval) subclass
    :class:`Tool` directly instead; this is for the function-shaped cases (and for
    building fake tools in tests without boilerplate).
    """

    def __init__(
        self,
        func: Callable[..., str],
        *,
        name: str,
        description: str,
        parameters: dict[str, str],
    ) -> None:
        super().__init__(name=name, description=description, parameters=parameters)
        self._func = func

    def run(self, **kwargs: Any) -> str:
        """Call the wrapped function, wrapping any failure in :class:`ToolError`."""
        try:
            return self._func(**kwargs)
        except ToolError:
            raise
        except Exception as exc:  # noqa: BLE001 — normalise arbitrary callable errors
            self._logger.error("tool %s raised: %s", self.name, exc)
            raise ToolError(f"tool {self.name!r} failed: {exc}") from exc


def tool(
    *,
    name: str,
    description: str,
    parameters: dict[str, str],
) -> Callable[[Callable[..., str]], FunctionTool]:
    """Decorator that registers a function as a :class:`FunctionTool` (lecture 4.2).

    Example::

        @tool(
            name="add",
            description="Add two integers.",
            parameters={"a": "first addend", "b": "second addend"},
        )
        def add(a: int, b: int) -> str:
            return str(a + b)

    Args:
        name: Tool identifier the LLM selects by.
        description: One-line summary of what the tool does.
        parameters: ``{arg_name: what_it_is}`` schema.

    Returns:
        A decorator that turns the function into a :class:`FunctionTool`.
    """

    def decorator(func: Callable[..., str]) -> FunctionTool:
        return FunctionTool(func, name=name, description=description, parameters=parameters)

    return decorator

"""Base agent abstraction shared by every specialist agent in the ERA Platform.

Introduced conceptually in Section 4 (tools, memory, the ReAct loop) and
formalised here as the contract every later agent — web intelligence, RAG
retrieval, quantitative analyst, synthesis — implements identically.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Raised when an agent fails in a way that should be surfaced to the
    orchestrator rather than silently swallowed.
    """


class BaseAgent(ABC):
    """Common contract for every agent in the ERA Platform.

    Subclasses implement `run()` with their specific logic (web search,
    retrieval, code execution, synthesis, etc.) and `validate_output()` to
    enforce the typed contract each agent promises to the orchestrator.

    Centralising logging and error handling here means every agent gets the
    same observability and failure behaviour for free — a pattern referenced
    again in Section 6 (resilient concurrency) and Section 9 (observability).
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._logger = logging.getLogger(f"era_platform.agents.{name}")

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the agent's core logic. Must be implemented by subclasses."""
        raise NotImplementedError

    @abstractmethod
    def validate_output(self, output: Any) -> bool:
        """Validate that `output` satisfies this agent's contract before it's
        handed back to the orchestrator. Subclasses should raise `AgentError`
        with a clear message on failure rather than returning False silently,
        unless the caller specifically wants a boolean check.
        """
        raise NotImplementedError

    async def safe_run(self, **kwargs: Any) -> Any:
        """Wraps `run()` with logging and a consistent error boundary.

        This is the method the orchestrator should actually call — it ensures
        every agent failure is logged with context before propagating, which
        matters once you're debugging a five-agent system instead of one.
        """
        self._logger.info("agent_started", extra={"agent": self.name})
        try:
            result = await self.run(**kwargs)
            self.validate_output(result)
            self._logger.info("agent_completed", extra={"agent": self.name})
            return result
        except Exception as exc:
            self._logger.error(
                "agent_failed",
                extra={"agent": self.name, "error": str(exc)},
                exc_info=True,
            )
            raise AgentError(f"{self.name} failed: {exc}") from exc

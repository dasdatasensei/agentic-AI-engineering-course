"""Exercise 2.E — starter.

Build a structured research summariser. Fill in every ``TODO`` below until the
tests in ``tests/unit/test_research_summariser.py`` pass. Your goal is a small
class that turns a block of source text into a *validated* object — not a
formatted string — and that re-asks the model when the first answer does not fit.

Concepts you are applying (see the lectures if you get stuck):
  * 2.4 — prompt engineering: give the model a system role and explicit output rules.
  * 2.5 — structured outputs: make the LLM return JSON that validates against a
          Pydantic model.
  * 2.6 — self-correcting outputs: catch ``ValidationError`` and ask again.

You depend only on the ``LLMClient`` protocol below, so you can test with a fake
client and never hit a live API. The reference implementation lives in
``era_platform/generation/summarizer.py`` — try it yourself before you peek.
"""

from __future__ import annotations

import json  # noqa: F401 — you will need this once you implement _parse
import logging
from typing import Protocol

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

MIN_KEY_POINTS = 3
MAX_KEY_POINTS = 5


class SummarizationError(Exception):
    """Raise this when a summary cannot be produced (empty input, LLM failure,
    or too many invalid responses)."""


class ResearchSummary(BaseModel):
    """The typed contract a summary must satisfy — this is what "structured" means.

    The four fields are given so the module imports cleanly. Your job is the
    ``key_points`` validator below (and the whole ``SummarizerAgent`` further
    down). Tune the ``Field(...)`` metadata if you like.
    """

    topic: str = Field(description="The main subject of the source text.")
    summary: str = Field(description="A 2-3 sentence abstract of the source text.")
    key_points: list[str] = Field(
        description=f"The {MIN_KEY_POINTS}-{MAX_KEY_POINTS} most important takeaways."
    )
    entities: list[str] = Field(
        default_factory=list,
        description="Notable organisations, people, or technologies named in the text.",
    )

    @field_validator("key_points")
    @classmethod
    def _bounded_key_points(cls, value: list[str]) -> list[str]:
        """TODO: raise ValueError unless there are between MIN_KEY_POINTS and
        MAX_KEY_POINTS items, then return ``value``. This is the validation that
        makes the 2.6 self-correction loop meaningful — without a rule that can
        fail, there is nothing to re-ask on."""
        raise NotImplementedError("Implement the key_points bound check")


class LLMClient(Protocol):
    """Minimal interface the summariser needs: ``invoke(prompt) -> raw text``."""

    def invoke(self, prompt: str) -> str: ...


class SummarizerAgent:
    """Turns source text into a validated ``ResearchSummary``."""

    def __init__(self, llm: LLMClient, *, max_retries: int = 2) -> None:
        self._llm = llm
        self._max_retries = max_retries

    def summarize(self, text: str) -> ResearchSummary:
        """Summarise ``text``, retrying on validation failure.

        TODO:
          1. Reject empty input with SummarizationError.
          2. Build a prompt (system role + explicit JSON field instructions + text).
          3. Loop up to ``max_retries + 1`` times:
               - call ``self._llm.invoke(prompt)`` (wrap failures in SummarizationError)
               - try to parse + validate the response into a ResearchSummary
               - on ValidationError/ValueError, feed the error back into the prompt
                 and try again.
          4. If every attempt fails, raise SummarizationError.
        """
        raise NotImplementedError("Implement summarize()")

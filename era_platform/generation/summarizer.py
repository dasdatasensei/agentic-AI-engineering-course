"""Structured research summariser — the first LLM-backed component of the ERA Platform.

Built in Section 2 (Exercise 2.E) as the payoff of the LLM-fundamentals lectures.
It stitches together three ideas taught just before it:

* **2.4 — prompt engineering:** a system role plus explicit output instructions.
* **2.5 — structured outputs with Pydantic:** the LLM must return data that
  validates against :class:`ResearchSummary`, not just nicely formatted prose.
* **2.6 — self-correcting outputs:** when validation fails, the error is fed
  back to the model and it is asked again, up to a bounded number of retries.

The reusable logic lives here, in the installed package, so it is type-checked
under ``mypy --strict``, unit-tested, and importable by later sections. The
exercise's ``starter/`` scaffolds toward this module and its ``solution/``
demonstrates driving it with a real Gemini client.

The summariser is deliberately provider-agnostic: it depends only on the small
:class:`LLMClient` protocol, so it can be driven by Gemini (the course default),
Groq, or a fake client in tests — no live API call is ever required to test it.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)

MIN_KEY_POINTS = 3
MAX_KEY_POINTS = 5

DEFAULT_SYSTEM_PROMPT = (
    "You are a meticulous research analyst. You read source material and distil "
    "it into a concise, structured summary. You never invent facts that are not "
    "present in the source text."
)


class SummarizationError(Exception):
    """Raised when the summariser cannot produce a valid :class:`ResearchSummary`.

    This is the error boundary the caller sees: either the LLM call itself failed
    (a transport/provider problem, which re-asking cannot fix), or the model kept
    returning output that would not validate even after the allowed retries.
    """


class ResearchSummary(BaseModel):
    """The typed contract a summarised document must satisfy.

    This is what "structured" means in this exercise: not prettily formatted
    text, but a validated object downstream code can rely on. The ``key_points``
    bound is what makes the 2.6 self-correction loop worth demonstrating — an LLM
    will occasionally return two points or seven, and that is a
    :class:`~pydantic.ValidationError` we can catch and re-ask on.
    """

    topic: str = Field(min_length=1, description="The main subject of the source text.")
    summary: str = Field(min_length=1, description="A 2-3 sentence abstract of the source text.")
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
        if not MIN_KEY_POINTS <= len(value) <= MAX_KEY_POINTS:
            raise ValueError(
                f"key_points must contain between {MIN_KEY_POINTS} and "
                f"{MAX_KEY_POINTS} items, got {len(value)}"
            )
        if any(not point.strip() for point in value):
            raise ValueError("key_points must not contain empty strings")
        return value


class LLMClient(Protocol):
    """The minimal interface the summariser needs from an LLM.

    Any object exposing ``invoke(prompt: str) -> str`` satisfies it: a thin
    wrapper around ``langchain_google_genai.ChatGoogleGenerativeAI`` (the course
    default — see the exercise ``solution/``), a Groq wrapper, or a fake used in
    tests. Depending on this protocol rather than a concrete SDK is what keeps
    the summariser testable without a network call.
    """

    def invoke(self, prompt: str) -> str:
        """Send ``prompt`` to the model and return its raw text response."""
        ...


class SummarizerAgent:
    """Turns a block of source text into a validated :class:`ResearchSummary`.

    A small single-purpose class rather than a bare function: it bundles the
    prompt, the injected LLM client, and the retry budget so callers configure
    the behaviour once and call :meth:`summarize` repeatedly. It intentionally
    does *not* subclass ``era_platform.agents.BaseAgent`` — that async, tool-using
    contract belongs to Section 4; a Section 2 summariser stays synchronous and
    self-contained.
    """

    def __init__(
        self,
        llm: LLMClient,
        *,
        max_retries: int = 2,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be zero or greater")
        self._llm = llm
        self._max_retries = max_retries
        self._system_prompt = system_prompt

    def summarize(self, text: str) -> ResearchSummary:
        """Summarise ``text`` into a validated :class:`ResearchSummary`.

        Makes up to ``max_retries + 1`` attempts. A parse or validation failure
        is fed back to the model as a correction (the 2.6 pattern); a failure of
        the LLM call itself is not retried, because re-asking cannot fix a broken
        connection or a bad key.

        Raises:
            SummarizationError: if ``text`` is empty, the LLM call fails, or no
                valid summary is produced within the retry budget.
        """
        if not text.strip():
            raise SummarizationError("cannot summarise empty text")

        base_prompt = self._build_prompt(text)
        attempts = self._max_retries + 1
        last_error: str | None = None

        for attempt in range(1, attempts + 1):
            prompt = (
                base_prompt
                if last_error is None
                else self._build_correction_prompt(base_prompt, last_error)
            )

            try:
                raw = self._llm.invoke(prompt)
            except Exception as exc:  # noqa: BLE001 — provider errors are wrapped, not retried
                logger.error("LLM call failed on attempt %d/%d: %s", attempt, attempts, exc)
                raise SummarizationError(f"LLM call failed: {exc}") from exc

            try:
                summary = self._parse(raw)
            except (ValueError, ValidationError) as exc:
                last_error = str(exc)
                logger.warning(
                    "attempt %d/%d produced invalid output, will re-ask: %s",
                    attempt,
                    attempts,
                    exc,
                )
                continue

            logger.info("produced a valid summary on attempt %d/%d", attempt, attempts)
            return summary

        raise SummarizationError(
            f"failed to produce a valid summary after {attempts} attempts; "
            f"last validation error: {last_error}"
        )

    def _build_prompt(self, text: str) -> str:
        return (
            f"{self._system_prompt}\n\n"
            "Summarise the SOURCE TEXT below into a single JSON object with "
            "exactly these fields:\n"
            '  - "topic": a short string naming the main subject\n'
            '  - "summary": a 2-3 sentence abstract\n'
            f'  - "key_points": an array of {MIN_KEY_POINTS} to {MAX_KEY_POINTS} '
            "short strings\n"
            '  - "entities": an array of notable organisations, people, or '
            "technologies named (may be empty)\n\n"
            "Respond with ONLY the JSON object — no markdown fences, no commentary.\n\n"
            f"SOURCE TEXT:\n{text}"
        )

    def _build_correction_prompt(self, base_prompt: str, error: str) -> str:
        return (
            f"{base_prompt}\n\n"
            "Your previous response could not be parsed into the required "
            f"structure. The error was:\n{error}\n\n"
            "Correct the problem and respond again with ONLY the valid JSON object."
        )

    def _parse(self, raw: str) -> ResearchSummary:
        """Extract and validate a :class:`ResearchSummary` from a raw response.

        Tolerates models that wrap JSON in prose or `````json`` fences by taking
        the span from the first ``{`` to the last ``}``. Raises ``ValueError``
        (which includes ``json.JSONDecodeError``) or ``ValidationError`` so the
        caller can treat every malformed response uniformly as "re-ask".
        """
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("no JSON object found in model response")
        data = json.loads(raw[start : end + 1])
        return ResearchSummary.model_validate(data)

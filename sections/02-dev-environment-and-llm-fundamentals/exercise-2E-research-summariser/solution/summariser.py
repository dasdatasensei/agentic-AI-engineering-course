"""Exercise 2.E — solution (runnable demo).

The reference *logic* lives in ``era_platform/generation/summarizer.py`` — it is
type-checked and unit-tested there, so it is not duplicated here. This file shows
how to *drive* it: it wires a real Gemini client (the course default provider for
synthesis tasks — see ``.env.example``) into the ``SummarizerAgent`` and prints a
structured summary of a sample document.

Run it:

    # With a key in your .env (real Gemini call):
    python sections/02-dev-environment-and-llm-fundamentals/\\
        exercise-2E-research-summariser/solution/summariser.py

    # With no GOOGLE_API_KEY set, it falls back to a canned offline response so
    # you can still see the end-to-end shape without spending a token.
"""

from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv

from era_platform.generation.summarizer import ResearchSummary, SummarizerAgent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SAMPLE_TEXT = (
    "The ERA Platform is a five-agent research system built incrementally across "
    "this course. A supervisor agent coordinates a web-intelligence agent, a RAG "
    "retrieval agent over ChromaDB, a quantitative analyst, and a synthesis agent. "
    "Orchestration uses LangGraph; results are served over HTTP with FastAPI and "
    "traced in LangSmith. The whole stack is designed to run on free API tiers."
)


class GeminiLLM:
    """A thin ``LLMClient`` adapter around Gemini via langchain-google-genai.

    Imports are done lazily inside ``__init__`` so this file still runs (via the
    offline fallback below) on a machine that has not installed the LLM extras.
    """

    def __init__(self, model: str | None = None, temperature: float = 0.0) -> None:
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Model name is env-driven per the zero-hardcoding rule (falls back to a
        # sensible default until era_platform/config.py centralises settings).
        model_name = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self._model = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)

    def invoke(self, prompt: str) -> str:
        response = self._model.invoke(prompt)
        content = response.content
        return content if isinstance(content, str) else str(content)


class _OfflineLLM:
    """A canned client used when no GOOGLE_API_KEY is set, so the demo always runs."""

    def invoke(self, prompt: str) -> str:  # noqa: ARG002 — prompt ignored on purpose
        return json.dumps(
            {
                "topic": "The ERA Platform",
                "summary": (
                    "The ERA Platform is a five-agent research system built across "
                    "the course. It orchestrates specialised agents with LangGraph "
                    "and serves traced results over FastAPI on free API tiers."
                ),
                "key_points": [
                    "A supervisor coordinates four specialist agents.",
                    "LangGraph handles orchestration; FastAPI serves results.",
                    "RAG retrieval runs over ChromaDB.",
                    "The stack is designed to run entirely on free API tiers.",
                ],
                "entities": ["LangGraph", "ChromaDB", "FastAPI", "LangSmith"],
            }
        )


def main() -> None:
    load_dotenv()

    if os.environ.get("GOOGLE_API_KEY"):
        logger.info("GOOGLE_API_KEY found — using Gemini.")
        agent = SummarizerAgent(GeminiLLM())
    else:
        logger.warning("No GOOGLE_API_KEY — using the offline canned client.")
        agent = SummarizerAgent(_OfflineLLM())

    summary: ResearchSummary = agent.summarize(SAMPLE_TEXT)

    logger.info("Topic:   %s", summary.topic)
    logger.info("Summary: %s", summary.summary)
    for i, point in enumerate(summary.key_points, start=1):
        logger.info("  %d. %s", i, point)
    logger.info("Entities: %s", ", ".join(summary.entities) or "(none)")


if __name__ == "__main__":
    main()

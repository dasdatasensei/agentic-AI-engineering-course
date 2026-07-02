"""Grounded document question-answering — the headline deliverable of Exercise 3.E.

Created: 2026-07-02
Last updated: 2026-07-02

Section 2 built a summariser that distils text you hand it. Section 3's Exercise
3.E "upgrades your summariser to answer questions from your own documents": the
model no longer works from text in the prompt, it works from chunks *retrieved*
from your indexed collection. That retrieval-then-answer shape is what makes RAG
fix hallucination (lecture 3.1) — the model is told to answer only from the
supplied context and to say so when the answer is not there.

:class:`DocumentQAAgent` composes three pieces built earlier, all injected:

* a Chroma ``Collection`` + an :class:`~era_platform.rag.embeddings.Embedder`
  (the 3.E retrieval core), and
* an :class:`~era_platform.generation.summarizer.LLMClient` — the *same* tiny
  protocol the 2.E summariser depends on, reused here rather than reinvented.

Because every dependency is a protocol or an injected object, the agent is
unit-tested with a fake embedder, an in-memory collection, and a scripted LLM —
no network, no API key.
"""

from __future__ import annotations

import logging

from chromadb.api.models.Collection import Collection
from pydantic import BaseModel, Field

from era_platform.generation.summarizer import LLMClient
from era_platform.rag.embeddings import Embedder
from era_platform.rag.retrieval import RetrievedChunk, similarity_search

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 4

# Prompts are named module-level constants until era_platform/generation/prompt_templates.py
# exists, per CLAUDE.md's no-inline-prompts rule — the later migration is then mechanical.
QA_SYSTEM_PROMPT = (
    "You are a precise research assistant. You answer questions using ONLY the "
    "provided context passages. If the answer is not contained in the context, "
    'reply exactly: "I could not find that in the provided documents." Never use '
    "outside knowledge and never invent citations."
)

_NO_CONTEXT_ANSWER = "I could not find that in the provided documents."


class QAError(Exception):
    """Raised when a grounded answer cannot be produced (e.g. the LLM call fails)."""


class GroundedAnswer(BaseModel):
    """A question, the grounded answer, and the passages the answer was drawn from."""

    question: str = Field(description="The question that was asked.")
    answer: str = Field(description="The model's answer, grounded in retrieved context.")
    sources: list[str] = Field(
        default_factory=list,
        description="Distinct source names of the passages supplied as context.",
    )
    passages: list[RetrievedChunk] = Field(
        default_factory=list, description="The retrieved passages used as context."
    )


class DocumentQAAgent:
    """Answers questions grounded in a ChromaDB-indexed document collection.

    Retrieves the most relevant chunks for a question, formats them as context,
    and asks the injected LLM to answer strictly from that context. Like the 2.E
    ``SummarizerAgent`` it is a small synchronous class and deliberately does not
    subclass ``era_platform.agents.BaseAgent`` — the async tool-using contract is
    Section 4's concern.
    """

    def __init__(
        self,
        collection: Collection,
        embedder: Embedder,
        llm: LLMClient,
        *,
        top_k: int = DEFAULT_TOP_K,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        self._collection = collection
        self._embedder = embedder
        self._llm = llm
        self._top_k = top_k

    def answer(self, question: str, *, where: dict[str, str] | None = None) -> GroundedAnswer:
        """Answer ``question`` using retrieved context.

        Args:
            question: The natural-language question.
            where: Optional metadata filter passed through to retrieval.

        Returns:
            A :class:`GroundedAnswer`. If nothing relevant is retrieved, returns
            the fixed can't-answer response **without** calling the LLM (saving a
            request against the free-tier quota).

        Raises:
            QAError: If ``question`` is blank or the LLM call fails.
        """
        if not question.strip():
            raise QAError("cannot answer an empty question")

        passages = similarity_search(
            self._collection, self._embedder, question, top_k=self._top_k, where=where
        )
        if not passages:
            logger.info("no passages retrieved for %r; returning can't-answer", question)
            return GroundedAnswer(question=question, answer=_NO_CONTEXT_ANSWER)

        prompt = self._build_prompt(question, passages)
        try:
            answer_text = self._llm.invoke(prompt).strip()
        except Exception as exc:  # noqa: BLE001 — provider errors wrapped at this boundary
            logger.error("LLM call failed while answering %r: %s", question, exc)
            raise QAError(f"LLM call failed: {exc}") from exc

        sources = _distinct_sources(passages)
        logger.info(
            "answered %r from %d passages, %d sources", question, len(passages), len(sources)
        )
        return GroundedAnswer(
            question=question, answer=answer_text, sources=sources, passages=passages
        )

    def _build_prompt(self, question: str, passages: list[RetrievedChunk]) -> str:
        context = "\n\n".join(
            f"[{i}] (source: {chunk.metadata.get('source', 'unknown')})\n{chunk.text}"
            for i, chunk in enumerate(passages, start=1)
        )
        return (
            f"{QA_SYSTEM_PROMPT}\n\n"
            f"CONTEXT PASSAGES:\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            "Answer using only the context above."
        )


def _distinct_sources(passages: list[RetrievedChunk]) -> list[str]:
    """Return source names in first-seen order, de-duplicated."""
    seen: dict[str, None] = {}
    for chunk in passages:
        seen.setdefault(chunk.metadata.get("source", "unknown"), None)
    return list(seen)

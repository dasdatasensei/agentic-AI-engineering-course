"""Exercise 3.E — solution (runnable demo).

The reference *logic* lives in ``era_platform/rag/`` — it is type-checked and
unit-tested there, so it is not duplicated here. This file shows how to *drive*
it: it ingests a few sample documents into an in-memory ChromaDB collection, then
uses ``DocumentQAAgent`` to answer a question grounded in them.

Run it:

    # With a key in your .env (real Gemini embeddings + Gemini answer):
    python sections/03-rag-fundamentals/exercise-3E-document-qa/solution/document_qa.py

    # With no GOOGLE_API_KEY set, it falls back to a local bag-of-words embedder
    # and a canned LLM so you can still see the end-to-end shape offline.
"""

from __future__ import annotations

import hashlib
import logging
import os

from dotenv import load_dotenv

from era_platform.rag import (
    DocumentIngestor,
    DocumentQAAgent,
    GroundedAnswer,
    SourceDocument,
    get_ephemeral_collection,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SAMPLE_DOCS = [
    SourceDocument(
        text=(
            "The ERA Platform orchestrates five agents with LangGraph. A supervisor "
            "coordinates a web-intelligence agent, a RAG retrieval agent over ChromaDB, "
            "a quantitative analyst, and a synthesis agent."
        ),
        metadata={"source": "architecture.txt"},
    ),
    SourceDocument(
        text=(
            "Retrieval-augmented generation reduces hallucination by grounding the "
            "model's answer in passages retrieved from a trusted document collection "
            "rather than relying on the model's parametric memory."
        ),
        metadata={"source": "rag-primer.txt"},
    ),
    SourceDocument(
        text=(
            "ChromaDB is an in-process vector database. The ERA Platform stores chunk "
            "embeddings in it and retrieves them with cosine similarity search."
        ),
        metadata={"source": "chromadb.txt"},
    ),
]

QUESTION = "How does the ERA Platform reduce hallucination?"


class _LocalEmbedder:
    """A deterministic offline embedder used when no GOOGLE_API_KEY is set.

    A bag-of-words hash embedding — not good enough for production, but enough to
    demonstrate the retrieve-then-answer flow without a network call.
    """

    def __init__(self, dim: int = 128) -> None:
        self._dim = dim

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        for token in text.lower().split():
            digest = hashlib.md5(token.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % self._dim] += 1.0
        if not any(vector):
            vector[0] = 1.0
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class _GeminiLLM:
    """A thin ``LLMClient`` adapter around Gemini via langchain-google-genai."""

    def __init__(self) -> None:
        from langchain_google_genai import ChatGoogleGenerativeAI

        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self._model = ChatGoogleGenerativeAI(model=model_name, temperature=0.0)

    def invoke(self, prompt: str) -> str:
        content = self._model.invoke(prompt).content
        return content if isinstance(content, str) else str(content)


class _OfflineLLM:
    """A canned LLM used when no GOOGLE_API_KEY is set, so the demo always runs."""

    def invoke(self, prompt: str) -> str:  # noqa: ARG002 — prompt ignored on purpose
        return (
            "It grounds each answer in passages retrieved from a trusted document "
            "collection instead of relying on the model's parametric memory."
        )


def main() -> None:
    load_dotenv()

    if os.environ.get("GOOGLE_API_KEY"):
        logger.info("GOOGLE_API_KEY found — using Gemini embeddings + Gemini answers.")
        from era_platform.rag import GeminiEmbedder

        embedder: object = GeminiEmbedder()
        llm: object = _GeminiLLM()
    else:
        logger.warning("No GOOGLE_API_KEY — using the offline local embedder and canned LLM.")
        embedder = _LocalEmbedder()
        llm = _OfflineLLM()

    collection = get_ephemeral_collection("exercise-3e")
    indexed = DocumentIngestor(embedder, collection).ingest(SAMPLE_DOCS)  # type: ignore[arg-type]
    logger.info("Indexed %d chunks.", indexed)

    agent = DocumentQAAgent(collection, embedder, llm)  # type: ignore[arg-type]
    result: GroundedAnswer = agent.answer(QUESTION)

    logger.info("Q: %s", result.question)
    logger.info("A: %s", result.answer)
    logger.info("Sources: %s", ", ".join(result.sources) or "(none)")


if __name__ == "__main__":
    main()

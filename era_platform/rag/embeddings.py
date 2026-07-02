"""Embedding interface for the ERA Platform RAG stack.

Created: 2026-07-02
Last updated: 2026-07-02

This module plays the same role for Section 3 that :class:`LLMClient` plays for
the Section 2 summariser: it defines a *tiny* structural interface —
:class:`Embedder` — that the ingestion and retrieval code depends on, so the
rest of ``era_platform.rag`` never imports a concrete embedding SDK and never
needs a network call or an API key to be unit-tested.

* The **course-default** implementation, :class:`GeminiEmbedder`, wraps
  LlamaIndex's ``GoogleGenAIEmbedding`` (``gemini-embedding-001`` on the free
  Google AI Studio tier — the same ``GOOGLE_API_KEY`` used by the 2.E solution).
  Its import is deferred to ``__init__`` so this module is importable, and the
  package is type-checkable, on a machine that has not installed the LLM extras.
* **Tests** inject a deterministic fake that satisfies :class:`Embedder`
  structurally — see ``tests/unit/test_knowledge_retrieval.py``.

Why LlamaIndex here rather than calling the SDK directly? Section 3 introduces
LlamaIndex as the RAG framework, and its embedding classes give us one batching
interface (``get_text_embedding_batch`` / ``get_query_embedding``) across every
provider. We adapt that down to the two methods the pipeline actually needs so
the surface tests must fake stays small and provider-agnostic.
"""

from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# Env-driven per the zero-hardcoding rule. Falls back to the current free-tier
# Gemini embedding model until era_platform/config.py centralises settings.
DEFAULT_EMBED_MODEL = "models/gemini-embedding-001"


class EmbeddingError(Exception):
    """Raised when embeddings cannot be produced for one or more inputs.

    This is the error boundary the ingestion/retrieval layers see. A transport
    or quota failure from the provider is wrapped in this rather than leaking the
    concrete SDK's exception type, so callers depend only on this package.
    """


@runtime_checkable
class Embedder(Protocol):
    """The minimal embedding interface the RAG pipeline depends on.

    Two methods, deliberately split so the query path can use an
    optimisation-appropriate task type where the provider supports it:

    * :meth:`embed_documents` — embed a batch of chunk texts for indexing.
    * :meth:`embed_query` — embed a single search query.

    Any object exposing these satisfies the protocol: :class:`GeminiEmbedder`
    (the course default) or a deterministic fake in tests.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in input order."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Return a single embedding vector for a search query."""
        ...


class GeminiEmbedder:
    """An :class:`Embedder` backed by Gemini via LlamaIndex.

    Wraps ``llama_index.embeddings.google_genai.GoogleGenAIEmbedding``. The
    import is lazy (inside ``__init__``) so importing this module never requires
    the ``llama-index-embeddings-google-genai`` extra to be installed — only
    actually constructing a :class:`GeminiEmbedder` does.
    """

    def __init__(self, model: str | None = None, *, api_key: str | None = None) -> None:
        """Build a Gemini-backed embedder.

        Args:
            model: Embedding model name. Defaults to ``GEMINI_EMBED_MODEL`` from
                the environment, then to :data:`DEFAULT_EMBED_MODEL`.
            api_key: Google AI Studio key. Defaults to ``GOOGLE_API_KEY`` from the
                environment (the same variable the 2.E solution uses).

        Raises:
            EmbeddingError: If no API key can be resolved.
        """
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

        resolved_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not resolved_key:
            raise EmbeddingError("GOOGLE_API_KEY is not set; cannot construct a Gemini embedder")
        model_name = model or os.environ.get("GEMINI_EMBED_MODEL", DEFAULT_EMBED_MODEL)
        self._model_name = model_name
        self._embedding = GoogleGenAIEmbedding(model_name=model_name, api_key=resolved_key)
        logger.info("Initialised GeminiEmbedder | model=%s", model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document chunks. See :meth:`Embedder.embed_documents`."""
        if not texts:
            return []
        try:
            vectors = self._embedding.get_text_embedding_batch(texts)
        except Exception as exc:  # noqa: BLE001 — provider errors are wrapped, not leaked
            logger.error("Gemini batch embedding failed for %d texts: %s", len(texts), exc)
            raise EmbeddingError(f"embedding {len(texts)} documents failed: {exc}") from exc
        logger.info("Embedded %d document chunks | model=%s", len(texts), self._model_name)
        return [list(vector) for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query. See :meth:`Embedder.embed_query`."""
        try:
            vector = self._embedding.get_query_embedding(text)
        except Exception as exc:  # noqa: BLE001 — provider errors are wrapped, not leaked
            logger.error("Gemini query embedding failed: %s", exc)
            raise EmbeddingError(f"embedding query failed: {exc}") from exc
        return list(vector)

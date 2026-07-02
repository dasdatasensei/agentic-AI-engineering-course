"""Dense retrieval over a ChromaDB collection.

Created: 2026-07-02
Last updated: 2026-07-02

The second half of the Section 3 RAG core (Exercise 3.E): given a query, embed it
and return the most similar indexed chunks. This is the ``similarity_search``
primitive the exercise proves out; Project 1 (3.P) layers metadata filtering and
hybrid keyword fusion on top of it in
:class:`~era_platform.rag.knowledge_agent.KnowledgeRetrievalAgent`.

Similarity is reported as a **cosine similarity score in ``[0, 1]``** (``1 -
distance``), because the collection is built with cosine distance (see
:mod:`era_platform.rag.store`). Higher is more relevant — the natural direction
for callers and for hybrid fusion.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from chromadb.api.models.Collection import Collection
from pydantic import BaseModel, Field

from era_platform.rag.embeddings import Embedder

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5


class RetrievalError(Exception):
    """Raised when a retrieval query cannot be executed."""


class RetrievedChunk(BaseModel):
    """A single retrieval hit: the chunk text, its relevance score, and its metadata."""

    chunk_id: str = Field(description="The stable id assigned at ingestion time.")
    text: str = Field(description="The chunk's text content.")
    score: float = Field(description="Cosine similarity in [0, 1]; higher is more relevant.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Source metadata carried from ingestion."
    )


def similarity_search(
    collection: Collection,
    embedder: Embedder,
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    where: dict[str, str] | None = None,
) -> list[RetrievedChunk]:
    """Return the ``top_k`` chunks most similar to ``query``.

    Args:
        collection: The Chroma collection to search (built by
            :mod:`era_platform.rag.store`, cosine distance, no embedding function).
        embedder: Used to embed the query; must be the same model family used at
            ingestion time or scores are meaningless.
        query: The natural-language search query.
        top_k: Maximum number of hits to return.
        where: Optional ChromaDB metadata filter, e.g. ``{"source": "notes.txt"}``.

    Returns:
        Hits sorted most-relevant first. Empty if the collection is empty.

    Raises:
        RetrievalError: If ``query`` is blank, ``top_k`` is not positive, or the
            underlying query fails.
    """
    if not query.strip():
        raise RetrievalError("cannot search with an empty query")
    if top_k <= 0:
        raise RetrievalError("top_k must be positive")

    query_embedding = embedder.embed_query(query)
    try:
        # Cast at the ChromaDB boundary: its numpy-flavoured arg types do not
        # accept our plain list[float]/dict shapes under invariance, though the
        # values are exactly what the API expects at runtime.
        result = collection.query(
            query_embeddings=cast(Any, [query_embedding]),
            n_results=top_k,
            where=cast(Any, where or None),
            include=cast(Any, ["documents", "metadatas", "distances"]),
        )
    except Exception as exc:  # noqa: BLE001 — surface store errors through our boundary
        logger.error("Chroma query failed: %s", exc)
        raise RetrievalError(f"retrieval query failed: {exc}") from exc

    hits = _parse_query_result(result)
    logger.info("retrieved %d chunks for query %r (top_k=%d)", len(hits), query, top_k)
    return hits


def _parse_query_result(result: object) -> list[RetrievedChunk]:
    """Flatten ChromaDB's single-query batched result into :class:`RetrievedChunk`s."""
    # Chroma returns each field as a list-of-lists keyed by query; we sent one query.
    assert isinstance(result, dict)
    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    hits: list[RetrievedChunk] = []
    for chunk_id, text, metadata, distance in zip(
        ids, documents, metadatas, distances, strict=False
    ):
        raw_metadata = metadata or {}
        hits.append(
            RetrievedChunk(
                chunk_id=str(chunk_id),
                text=text or "",
                score=_distance_to_similarity(distance),
                metadata={str(k): str(v) for k, v in raw_metadata.items()},
            )
        )
    return hits


def _distance_to_similarity(distance: float | None) -> float:
    """Convert a cosine *distance* (0 = identical) to a similarity in ``[0, 1]``."""
    if distance is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 - float(distance)))

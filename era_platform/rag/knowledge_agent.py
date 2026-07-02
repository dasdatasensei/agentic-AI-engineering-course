"""KnowledgeRetrievalAgent — the Project 1 (3.P) retrieval layer.

Created: 2026-07-02
Last updated: 2026-07-02

Project 1 turns the 3.E ingestion/retrieval core into a reusable *personal
knowledge assistant* over a document collection of the learner's choosing. Per
``README.md``'s package table this is where ``KnowledgeRetrievalAgent`` lands,
and it is the zero-cost, simplified realisation of ``docs/ERA_Platform_SOW_v1.md``
§3.3 (Knowledge Retrieval Agent): ChromaDB in place of Pinecone, Gemini
Embeddings in place of ``text-embedding-3-large``, and plain/hybrid retrieval in
place of the SOW's full hybrid+rerank+HyDE pipeline.

What 3.P adds on top of 3.E:

* **Metadata filtering** — restrict retrieval to a subset of the corpus
  (e.g. one source file) via a ChromaDB ``where`` clause.
* **Hybrid search (lecture 3.6)** — fuse dense (embedding) similarity with sparse
  BM25 keyword scores using Reciprocal Rank Fusion, which needs no score
  normalisation between the two very different scales.

Deliberately **out of scope** here (so later exercises are not made redundant):
HyDE query expansion and cross-encoder reranking are Exercise 7.E's job; the
async/tool-calling ``BaseAgent`` contract is Section 4's; contradiction detection
is the Section 6/12 multi-agent concern. Like the 2.E summariser, this class is
synchronous and does **not** subclass ``era_platform.agents.BaseAgent``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from chromadb.api.models.Collection import Collection
from pydantic import BaseModel, Field

from era_platform.rag.bm25 import BM25Index
from era_platform.rag.embeddings import Embedder
from era_platform.rag.ingestion import DocumentIngestor, SourceDocument
from era_platform.rag.retrieval import RetrievedChunk, similarity_search

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
# RRF's rank constant. 60 is the value from the original Cormack et al. (2009)
# paper and the de facto default in search systems; it damps the influence of
# very high ranks so no single list dominates the fusion.
DEFAULT_RRF_K = 60


class KnowledgeQuery(BaseModel):
    """A structured retrieval request against the knowledge base."""

    question: str = Field(min_length=1, description="The natural-language query.")
    top_k: int = Field(default=DEFAULT_TOP_K, gt=0, description="Max hits to return.")
    where: dict[str, str] | None = Field(
        default=None, description="Optional ChromaDB metadata filter, e.g. {'source': 'x.txt'}."
    )
    hybrid: bool = Field(
        default=True, description="Fuse BM25 keyword scores with dense similarity."
    )


class KnowledgeRetrievalAgent:
    """Retrieval-focused knowledge assistant over an ingested document collection.

    Wraps the 3.E core: it owns a :class:`~era_platform.rag.ingestion.DocumentIngestor`
    for building the index and exposes :meth:`retrieve` for querying it with
    optional metadata filtering and hybrid dense+BM25 fusion.

    The BM25 half is built lazily from the collection's own documents on first
    hybrid query and cached, so a pure-dense deployment pays nothing for it. Call
    :meth:`refresh_keyword_index` after ingesting more documents to rebuild it.
    """

    def __init__(
        self,
        embedder: Embedder,
        collection: Collection,
        *,
        rrf_k: int = DEFAULT_RRF_K,
    ) -> None:
        self._embedder = embedder
        self._collection = collection
        self._ingestor = DocumentIngestor(embedder, collection)
        self._rrf_k = rrf_k
        self._bm25: BM25Index | None = None
        self._bm25_ids: list[str] = []
        self._bm25_docs: dict[str, RetrievedChunk] = {}

    # ── Ingestion ────────────────────────────────────────────────────────────

    def ingest_documents(self, documents: list[SourceDocument]) -> int:
        """Index ``documents`` and invalidate the cached keyword index."""
        count = self._ingestor.ingest(documents)
        self._bm25 = None
        return count

    def ingest_directory(self, source_dir: Path) -> int:
        """Index every ``*.txt`` under ``source_dir`` and invalidate the keyword index."""
        count = self._ingestor.ingest_directory(source_dir)
        self._bm25 = None
        return count

    def refresh_keyword_index(self) -> None:
        """Rebuild the in-memory BM25 index from the collection's current contents."""
        self._bm25 = None
        self._ensure_keyword_index()

    # ── Retrieval ────────────────────────────────────────────────────────────

    def retrieve(self, query: KnowledgeQuery) -> list[RetrievedChunk]:
        """Return the chunks most relevant to ``query``.

        Dense-only when ``query.hybrid`` is false; otherwise fuses dense and BM25
        rankings with Reciprocal Rank Fusion. ``query.where`` restricts the dense
        (and, when possible, the keyword) candidate set by metadata.
        """
        dense_hits = similarity_search(
            self._collection,
            self._embedder,
            query.question,
            top_k=query.top_k,
            where=query.where,
        )
        if not query.hybrid:
            return dense_hits

        keyword_hits = self._keyword_search(query.question, query.top_k, query.where)
        fused = self._reciprocal_rank_fusion(dense_hits, keyword_hits, top_k=query.top_k)
        logger.info(
            "hybrid retrieve %r | dense=%d keyword=%d fused=%d",
            query.question,
            len(dense_hits),
            len(keyword_hits),
            len(fused),
        )
        return fused

    def _keyword_search(
        self, question: str, top_k: int, where: dict[str, str] | None
    ) -> list[RetrievedChunk]:
        self._ensure_keyword_index()
        if self._bm25 is None:
            return []
        raw_hits = self._bm25.search(question, top_k=top_k * 3)
        hits: list[RetrievedChunk] = []
        for position, _score in raw_hits:
            chunk = self._bm25_docs[self._bm25_ids[position]]
            if where and not _matches(chunk.metadata, where):
                continue
            hits.append(chunk)
            if len(hits) >= top_k:
                break
        return hits

    def _ensure_keyword_index(self) -> None:
        if self._bm25 is not None:
            return
        stored = self._collection.get(include=["documents", "metadatas"])
        ids = [str(i) for i in (stored.get("ids") or [])]
        documents = stored.get("documents") or []
        metadatas = stored.get("metadatas") or []
        if not ids:
            logger.info("keyword index skipped: collection is empty")
            return
        self._bm25_ids = ids
        self._bm25_docs = {
            chunk_id: RetrievedChunk(
                chunk_id=chunk_id,
                text=text or "",
                score=0.0,
                metadata={str(k): str(v) for k, v in (metadata or {}).items()},
            )
            for chunk_id, text, metadata in zip(ids, documents, metadatas, strict=False)
        }
        self._bm25 = BM25Index([self._bm25_docs[i].text for i in ids])
        logger.info("built keyword index over %d chunks", len(ids))

    def _reciprocal_rank_fusion(
        self,
        dense_hits: list[RetrievedChunk],
        keyword_hits: list[RetrievedChunk],
        *,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Combine two ranked lists with RRF: score = Σ 1/(k + rank).

        RRF fuses on *rank* not raw score, so the incomparable cosine-similarity
        and BM25 scales never need normalising. The fused ``score`` on each
        returned chunk is its RRF score (not a similarity), sorted descending.
        """
        fused_scores: dict[str, float] = {}
        chunks: dict[str, RetrievedChunk] = {}
        for ranked in (dense_hits, keyword_hits):
            for rank, chunk in enumerate(ranked):
                fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0.0) + 1.0 / (
                    self._rrf_k + rank
                )
                chunks.setdefault(chunk.chunk_id, chunk)
        ordered = sorted(fused_scores, key=lambda cid: (-fused_scores[cid], cid))
        return [
            chunks[cid].model_copy(update={"score": fused_scores[cid]}) for cid in ordered[:top_k]
        ]


def _matches(metadata: dict[str, str], where: dict[str, str]) -> bool:
    """True if ``metadata`` satisfies every key/value in ``where`` (equality only)."""
    return all(metadata.get(key) == value for key, value in where.items())

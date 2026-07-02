"""ERA Platform retrieval-augmented generation (RAG) building blocks.

Born in Section 3 (Exercise 3.E + Project 1). The package is intentionally
layered so later sections extend it rather than rewrite it:

* :mod:`~era_platform.rag.embeddings` — the ``Embedder`` protocol + Gemini adapter.
* :mod:`~era_platform.rag.store` — the ChromaDB collection factory (cosine, env-driven).
* :mod:`~era_platform.rag.ingestion` — load → chunk (LlamaIndex) → embed → index.
* :mod:`~era_platform.rag.retrieval` — the ``similarity_search`` dense primitive.
* :mod:`~era_platform.rag.qa` — ``DocumentQAAgent``, grounded question answering (3.E).
* :mod:`~era_platform.rag.bm25` — a dependency-free BM25 keyword index.
* :mod:`~era_platform.rag.knowledge_agent` — ``KnowledgeRetrievalAgent``, the 3.P
  hybrid + metadata-filtered retrieval layer.
"""

from era_platform.rag.bm25 import BM25Index
from era_platform.rag.embeddings import Embedder, EmbeddingError, GeminiEmbedder
from era_platform.rag.ingestion import (
    DocumentChunk,
    DocumentIngestor,
    IngestionError,
    SourceDocument,
    chunk_documents,
    load_text_files,
)
from era_platform.rag.knowledge_agent import KnowledgeQuery, KnowledgeRetrievalAgent
from era_platform.rag.qa import DocumentQAAgent, GroundedAnswer, QAError
from era_platform.rag.retrieval import (
    RetrievalError,
    RetrievedChunk,
    similarity_search,
)
from era_platform.rag.store import get_ephemeral_collection, get_persistent_collection

__all__ = [
    "BM25Index",
    "DocumentChunk",
    "DocumentIngestor",
    "DocumentQAAgent",
    "Embedder",
    "EmbeddingError",
    "GeminiEmbedder",
    "GroundedAnswer",
    "IngestionError",
    "KnowledgeQuery",
    "KnowledgeRetrievalAgent",
    "QAError",
    "RetrievalError",
    "RetrievedChunk",
    "SourceDocument",
    "chunk_documents",
    "get_ephemeral_collection",
    "get_persistent_collection",
    "load_text_files",
    "similarity_search",
]

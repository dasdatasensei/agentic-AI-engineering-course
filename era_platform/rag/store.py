"""ChromaDB collection factory for the ERA Platform RAG stack.

Created: 2026-07-02
Last updated: 2026-07-02

Section 3 stores vectors in ChromaDB (the zero-cost, in-process stand-in for the
Pinecone pod in ``docs/ERA_Platform_SOW_v1.md`` §3.3). This module is the single
place that constructs a collection, so two rules live in exactly one spot:

* **Persistence path is environment-driven** — ``CHROMA_PERSIST_DIR`` (default
  ``./chroma_db``, matching ``.env.example``), never a hardcoded absolute path,
  because learners run this on Windows, macOS, and Linux.
* **Distance is cosine** — set via ``hnsw:space`` so the metric matches the
  documented Pinecone production path and the ADR comparison stays valid.

The collection is created **without** a Chroma embedding function: the ERA
pipeline always computes vectors itself through an :class:`~era_platform.rag.embeddings.Embedder`
and passes them explicitly. That keeps embedding provider-agnostic *and* avoids
Chroma's default all-MiniLM ONNX model download, so tests and first runs need no
network access.
"""

from __future__ import annotations

import logging
import os

import chromadb
from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)

DEFAULT_PERSIST_DIR = "./chroma_db"
DEFAULT_COLLECTION_NAME = "knowledge_base"

# Tells Chroma to rank with cosine distance rather than the default squared-L2.
_COSINE_METADATA = {"hnsw:space": "cosine"}


def get_persistent_collection(
    *, persist_dir: str | None = None, collection_name: str | None = None
) -> Collection:
    """Open (or create) the on-disk knowledge-base collection.

    Args:
        persist_dir: Directory for the Chroma database. Defaults to
            ``CHROMA_PERSIST_DIR`` then :data:`DEFAULT_PERSIST_DIR`.
        collection_name: Collection name. Defaults to ``CHROMA_COLLECTION_NAME``
            then :data:`DEFAULT_COLLECTION_NAME`.

    Returns:
        A cosine-distance :class:`~chromadb.api.models.Collection.Collection`
        with no attached embedding function.
    """
    path = persist_dir or os.environ.get("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR)
    name = collection_name or os.environ.get("CHROMA_COLLECTION_NAME", DEFAULT_COLLECTION_NAME)
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(
        name=name, embedding_function=None, metadata=_COSINE_METADATA
    )
    logger.info("Opened persistent Chroma collection %r at %s", name, path)
    return collection


def get_ephemeral_collection(collection_name: str = DEFAULT_COLLECTION_NAME) -> Collection:
    """Create an in-memory collection with no persistence — used by the test suite.

    Identical cosine configuration to :func:`get_persistent_collection` but backed
    by an ephemeral client, so unit tests exercise the real Chroma add/query path
    without touching disk, the network, or an embedding-model download.
    """
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(
        name=collection_name, embedding_function=None, metadata=_COSINE_METADATA
    )

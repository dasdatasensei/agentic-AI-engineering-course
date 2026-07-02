"""Document ingestion: load → chunk → embed → index into ChromaDB.

Created: 2026-07-02
Last updated: 2026-07-02

This is the first half of the Section 3 RAG core (Exercise 3.E): the pipeline
that turns a folder of source documents into a queryable ChromaDB collection.
Retrieval — the second half — lives in :mod:`era_platform.rag.retrieval`.

The chunking step uses LlamaIndex's :class:`~llama_index.core.node_parser.SentenceSplitter`
(Section 3's chosen RAG framework), which respects sentence boundaries rather
than blindly slicing every ``N`` characters. Embedding goes through the injected
:class:`~era_platform.rag.embeddings.Embedder` protocol, and storage through an
injected Chroma collection — so the whole pipeline is exercised in tests with a
deterministic fake embedder and an in-memory collection, no network required.

Design note: :class:`DocumentIngestor` takes its embedder and collection as
constructor arguments (dependency injection), mirroring how the 2.E
``SummarizerAgent`` takes its ``LLMClient``. Nothing here reaches out to a global
client or an environment variable directly; wiring lives in the section
``solution/`` and CLI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from chromadb.api.models.Collection import Collection

from era_platform.rag.embeddings import Embedder

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 50


class IngestionError(Exception):
    """Raised when documents cannot be loaded or indexed."""


@dataclass(frozen=True)
class SourceDocument:
    """A single source document plus the metadata carried onto each of its chunks.

    ``metadata`` values are strings because ChromaDB only stores scalar metadata;
    keeping to ``str`` keeps the metadata-filtering path (3.P) predictable.
    """

    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentChunk:
    """One embed-ready chunk: its text, a stable id, and inherited source metadata."""

    chunk_id: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


def load_text_files(source_dir: Path) -> list[SourceDocument]:
    """Load every ``*.txt`` file under ``source_dir`` into :class:`SourceDocument` objects.

    Each document's ``source`` metadata is set to the file name so retrieved
    chunks can be traced back to their origin (and filtered on in 3.P).

    Raises:
        IngestionError: If the directory is missing or contains no readable text.
    """
    if not source_dir.exists():
        raise IngestionError(f"source directory does not exist: {source_dir}")

    documents: list[SourceDocument] = []
    for path in sorted(source_dir.glob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            logger.warning("could not read %s: %s", path, exc)
            continue
        if text:
            documents.append(SourceDocument(text=text, metadata={"source": path.name}))

    if not documents:
        raise IngestionError(f"no readable .txt documents found in {source_dir}")

    logger.info("loaded %d documents from %s", len(documents), source_dir)
    return documents


def chunk_documents(
    documents: list[SourceDocument],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """Split documents into overlapping, sentence-aware chunks via LlamaIndex.

    Uses :class:`~llama_index.core.node_parser.SentenceSplitter`. Chunk ids are
    ``"{source}::{n}"`` when a ``source`` is present, else ``"doc{d}::{n}"`` —
    stable and unique so re-ingesting the same corpus upserts rather than
    duplicates.

    Raises:
        IngestionError: If ``chunk_overlap`` is not smaller than ``chunk_size``.
    """
    if chunk_overlap >= chunk_size:
        raise IngestionError("chunk_overlap must be smaller than chunk_size")

    from llama_index.core import Document as LlamaDocument
    from llama_index.core.node_parser import SentenceSplitter

    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[DocumentChunk] = []
    for doc_index, document in enumerate(documents):
        nodes = splitter.get_nodes_from_documents([LlamaDocument(text=document.text)])
        source = document.metadata.get("source", f"doc{doc_index}")
        for node_index, node in enumerate(nodes):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{source}::{node_index}",
                    text=node.get_content(),
                    metadata=dict(document.metadata),
                )
            )
    logger.info("produced %d chunks from %d documents", len(chunks), len(documents))
    return chunks


class DocumentIngestor:
    """Loads, chunks, embeds, and indexes documents into a ChromaDB collection.

    Bundles the injected :class:`Embedder` and Chroma ``Collection`` so the caller
    configures them once and ingests repeatedly. Embeddings are computed here and
    written to Chroma explicitly, so the collection needs no embedding function of
    its own (see :mod:`era_platform.rag.store`).
    """

    def __init__(
        self,
        embedder: Embedder,
        collection: Collection,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self._embedder = embedder
        self._collection = collection
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def ingest(self, documents: list[SourceDocument]) -> int:
        """Chunk, embed, and index ``documents``. Returns the number of chunks indexed.

        Raises:
            IngestionError: If there is nothing to index after chunking.
        """
        chunks = chunk_documents(
            documents, chunk_size=self._chunk_size, chunk_overlap=self._chunk_overlap
        )
        if not chunks:
            raise IngestionError("no chunks were produced from the supplied documents")
        return self.ingest_chunks(chunks)

    def ingest_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Embed and upsert already-chunked text. Returns the number of chunks indexed."""
        texts = [chunk.text for chunk in chunks]
        embeddings = self._embedder.embed_documents(texts)
        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=texts,
            # Cast at the ChromaDB boundary — see the note in retrieval.py.
            embeddings=cast(Any, embeddings),
            metadatas=cast(Any, [chunk.metadata or {"source": "unknown"} for chunk in chunks]),
        )
        logger.info("indexed %d chunks into collection %r", len(chunks), self._collection.name)
        return len(chunks)

    def ingest_directory(self, source_dir: Path) -> int:
        """Convenience wrapper: :func:`load_text_files` then :meth:`ingest`."""
        return self.ingest(load_text_files(source_dir))

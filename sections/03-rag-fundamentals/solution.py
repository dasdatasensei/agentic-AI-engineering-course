"""Section 3 solution — Project 1: Personal Knowledge Assistant

A working reference implementation of the RAG pipeline from exercise.py.
Uses ChromaDB's built-in default embedding function here for portability
(no API key required to run this file standalone); swap in
`langchain_google_genai.GoogleGenerativeAIEmbeddings` for the Gemini
Embeddings version used in the course videos — see the commented block
below `build_index`.

This becomes era_platform/rag/ once you're satisfied it works.

Verification note: the pipeline logic (chunking, indexing, querying) was
tested end-to-end against ChromaDB. The default embedding function
downloads a small ONNX model on first use, which requires outbound network
access to an S3 bucket — if that download fails in a restricted network
environment, switch to the Gemini Embeddings function shown in the
build_index() docstring below, which only needs your Google AI Studio key.
"""

from __future__ import annotations

import logging
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class DocumentLoadError(Exception):
    """Raised when no readable documents are found in the source directory."""


def load_documents(source_dir: Path) -> list[str]:
    """Load raw text from every .txt file in `source_dir`."""
    if not source_dir.exists():
        raise DocumentLoadError(f"Source directory does not exist: {source_dir}")

    documents: list[str] = []
    for path in sorted(source_dir.glob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                documents.append(text)
        except OSError as exc:
            logger.warning("Could not read %s: %s", path, exc)

    if not documents:
        raise DocumentLoadError(f"No readable .txt documents found in {source_dir}")

    logger.info("Loaded %d documents from %s", len(documents), source_dir)
    return documents


def chunk_documents(documents: list[str], chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split documents into overlapping chunks suitable for embedding.

    A simple character-based sliding window. LlamaIndex's
    SentenceWindowNodeParser (covered in 3.4) does this more intelligently
    by respecting sentence boundaries — this hand-rolled version exists so
    you understand the underlying mechanics before relying on the library.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[str] = []
    for doc in documents:
        start = 0
        while start < len(doc):
            end = start + chunk_size
            chunks.append(doc[start:end])
            start = end - overlap

    logger.info("Produced %d chunks from %d documents", len(chunks), len(documents))
    return chunks


def build_index(chunks: list[str], persist_dir: str = "./chroma_db", collection_name: str = "knowledge_base") -> None:
    """Embed each chunk and store in a persistent ChromaDB collection.

    Uses ChromaDB's `DefaultEmbeddingFunction`, which downloads a small
    ONNX sentence-transformer model on first use. If you're behind a
    restrictive network/proxy and that download fails, swap in Gemini
    Embeddings instead — it needs only your free Google AI Studio key and
    has no separate model download step:

        import os
        from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
        embedding_function = GoogleGenerativeAiEmbeddingFunction(
            api_key=os.environ["GOOGLE_API_KEY"]
        )
        collection = client.get_or_create_collection(
            name=collection_name, embedding_function=embedding_function
        )

    This is the version taught in the course videos (Lecture 3.4) — the
    local ONNX default here exists purely so this file can run standalone
    with zero configuration for a first pass.
    """
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(name=collection_name)

    ids = [f"chunk-{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids)

    logger.info("Indexed %d chunks into collection '%s' at %s", len(chunks), collection_name, persist_dir)


def query(
    question: str,
    persist_dir: str = "./chroma_db",
    collection_name: str = "knowledge_base",
    top_k: int = 5,
) -> list[str]:
    """Retrieve the top_k most relevant chunks for `question`."""
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(name=collection_name)

    results = collection.query(query_texts=[question], n_results=top_k)
    documents = results.get("documents", [[]])[0]

    logger.info("Retrieved %d chunks for query: %r", len(documents), question)
    return documents


if __name__ == "__main__":
    sample_dir = Path(__file__).parent / "sample_docs"
    if not sample_dir.exists():
        sample_dir.mkdir()
        (sample_dir / "example.txt").write_text(
            "The ERA Platform is a five-agent research system built across "
            "this course. It uses LangGraph for orchestration, ChromaDB for "
            "retrieval, and FastAPI to serve results over HTTP."
        )
        logger.info("Created a sample document at %s — re-run to index it.", sample_dir)

    docs = load_documents(sample_dir)
    chunks = chunk_documents(docs, chunk_size=200, overlap=20)
    build_index(chunks)
    results = query("What does the ERA Platform use for orchestration?")
    for r in results:
        logger.info("Retrieved: %s", r[:150])

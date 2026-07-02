"""Section 3 exercise — Project 1: Personal Knowledge Assistant

Build a RAG pipeline over a document collection of your choice: ingest,
chunk, embed, store in ChromaDB, and retrieve relevant chunks for a query.

Fill in each function below. Run this file directly to sanity-check your
implementation against a tiny built-in sample corpus before pointing it at
your own documents.

Compare against solution.py once you have something working.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_documents(source_dir: Path) -> list[str]:
    """Load raw text from every .txt file in `source_dir`.

    TODO: implement this. Should return a list of raw document strings.
    Use Python's standard logging (not print) to report how many files
    were loaded — this matters once you're debugging a pipeline with
    hundreds of documents, not just three.
    """
    raise NotImplementedError("Implement load_documents")


def chunk_documents(documents: list[str], chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split documents into overlapping chunks suitable for embedding.

    TODO: implement a simple sliding-window chunker. You'll replace this
    with LlamaIndex's SentenceWindowNodeParser in later sections — for now,
    build it by hand so you understand what that abstraction is doing for you.
    """
    raise NotImplementedError("Implement chunk_documents")


def build_index(chunks: list[str], persist_dir: str = "./chroma_db") -> None:
    """Embed each chunk with Gemini Embeddings and store in a persistent
    ChromaDB collection.

    TODO: implement using chromadb.PersistentClient and the
    langchain_google_genai embeddings interface.
    """
    raise NotImplementedError("Implement build_index")


def query(question: str, persist_dir: str = "./chroma_db", top_k: int = 5) -> list[str]:
    """Retrieve the top_k most relevant chunks for `question`.

    TODO: implement retrieval against the ChromaDB collection built above.
    """
    raise NotImplementedError("Implement query")


if __name__ == "__main__":
    # Minimal sanity check — replace with your own document directory.
    sample_dir = Path(__file__).parent / "sample_docs"
    if not sample_dir.exists():
        logger.warning(
            "No sample_docs/ directory found — create one with a few .txt files to test."
        )
    else:
        docs = load_documents(sample_dir)
        chunks = chunk_documents(docs)
        build_index(chunks)
        results = query("What is this collection about?")
        for r in results:
            logger.info("Retrieved: %s", r[:100])

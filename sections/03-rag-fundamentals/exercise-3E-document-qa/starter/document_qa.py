"""Exercise 3.E — starter.

Build a document question-answerer grounded in your own documents. Fill in every
``TODO`` below. Your goal: retrieve the passages relevant to a question, then have
an LLM answer *only* from those passages — the pattern that makes RAG fix
hallucination (lecture 3.1).

You depend on two tiny protocols, so you can test with fakes and never hit a live
API: ``Embedder`` (turn text into vectors) and ``LLMClient`` (the same protocol
from Exercise 2.E). The reference implementation lives in ``era_platform/rag/`` —
try it yourself before you peek.

Concepts you are applying (see the lectures if you get stuck):
  * 3.2 — embeddings: text → vectors whose distance encodes similarity.
  * 3.3 — ChromaDB: an in-process vector store (cosine distance).
  * 3.4 — ingestion: load → chunk → embed → index.
  * 3.5 — retrieval: top-k similarity search.
  * 3.1 — grounded answering: answer only from retrieved context.
"""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 50
DEFAULT_TOP_K = 4

QA_SYSTEM_PROMPT = (
    "You are a precise research assistant. You answer questions using ONLY the "
    "provided context passages. If the answer is not contained in the context, "
    'reply exactly: "I could not find that in the provided documents."'
)
NO_CONTEXT_ANSWER = "I could not find that in the provided documents."


class DocumentQAError(Exception):
    """Raise this when a grounded answer cannot be produced (e.g. the LLM call fails)."""


class Embedder(Protocol):
    """Minimal embedding interface: batch-embed documents, single-embed a query."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class LLMClient(Protocol):
    """The same protocol as Exercise 2.E: ``invoke(prompt) -> raw text``."""

    def invoke(self, prompt: str) -> str: ...


def chunk_text(
    text: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP
) -> list[str]:
    """Split ``text`` into overlapping chunks suitable for embedding.

    TODO:
      1. Raise ValueError if ``overlap >= chunk_size``.
      2. Slide a window of ``chunk_size`` characters across ``text``, stepping
         forward by ``chunk_size - overlap`` each time, collecting each slice.
      3. Return the list of chunks. (The packaged reference uses LlamaIndex's
         sentence-aware splitter — build it by hand here to understand what that
         abstraction does for you.)
    """
    raise NotImplementedError("Implement chunk_text")


class DocumentQA:
    """Indexes documents into a ChromaDB collection and answers questions from them.

    You are given an ``Embedder``, a ChromaDB ``collection`` (already created by
    the caller with cosine distance and no embedding function), and an
    ``LLMClient``. Compute embeddings yourself and pass them to Chroma explicitly.
    """

    def __init__(
        self, embedder: Embedder, collection: object, llm: LLMClient, *, top_k: int = DEFAULT_TOP_K
    ) -> None:
        self._embedder = embedder
        self._collection = collection
        self._llm = llm
        self._top_k = top_k

    def index(self, documents: list[str]) -> int:
        """Chunk, embed, and store ``documents``. Return the number of chunks indexed.

        TODO:
          1. Chunk every document with ``chunk_text`` into one flat list of chunks.
          2. Embed the chunks with ``self._embedder.embed_documents``.
          3. ``self._collection.add(ids=..., documents=..., embeddings=...)`` with a
             unique id per chunk.
          4. Log how many chunks you indexed, and return that count.
        """
        raise NotImplementedError("Implement index")

    def retrieve(self, query: str) -> list[str]:
        """Return the ``top_k`` chunk texts most relevant to ``query``.

        TODO:
          1. Embed the query with ``self._embedder.embed_query``.
          2. ``self._collection.query(query_embeddings=[...], n_results=self._top_k)``.
          3. Return the list of retrieved chunk texts (Chroma nests them one level
             deep: ``result["documents"][0]``).
        """
        raise NotImplementedError("Implement retrieve")

    def answer(self, question: str) -> str:
        """Answer ``question`` grounded in retrieved context.

        TODO:
          1. Retrieve passages for ``question``.
          2. If there are none, return ``NO_CONTEXT_ANSWER`` WITHOUT calling the LLM
             (don't spend a request when you have no context to ground on).
          3. Otherwise build a prompt: ``QA_SYSTEM_PROMPT`` + the numbered passages
             + the question, then call ``self._llm.invoke(prompt)``. Wrap any
             failure of that call in ``DocumentQAError``.
          4. Return the model's answer.
        """
        raise NotImplementedError("Implement answer")

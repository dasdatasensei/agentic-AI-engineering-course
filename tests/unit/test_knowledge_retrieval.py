"""Unit tests for the Section 3 RAG stack (Exercise 3.E + Project 1).

Every test runs fully offline: a deterministic bag-of-words :class:`_FakeEmbedder`
stands in for Gemini, and an *in-memory* ChromaDB collection
(``get_ephemeral_collection``) stands in for the on-disk store — so no network,
no API key, and no embedding-model download are ever required. This is the same
fake-dependency discipline as ``test_research_summariser.py``, extended to the
vector store: because the ERA pipeline always supplies its own vectors, the
ephemeral collection never touches Chroma's default ONNX embedder.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from chromadb.api.models.Collection import Collection

from era_platform.rag.bm25 import BM25Index
from era_platform.rag.ingestion import (
    DocumentIngestor,
    IngestionError,
    SourceDocument,
    chunk_documents,
    load_text_files,
)
from era_platform.rag.knowledge_agent import KnowledgeQuery, KnowledgeRetrievalAgent
from era_platform.rag.qa import DocumentQAAgent, GroundedAnswer, QAError
from era_platform.rag.retrieval import RetrievalError, similarity_search
from era_platform.rag.store import get_ephemeral_collection

_EMBED_DIM = 96


class _FakeEmbedder:
    """A deterministic bag-of-words embedder — no network, stable across runs.

    Each whitespace token is hashed (via md5, so it does not depend on
    ``PYTHONHASHSEED``) into a fixed-width count vector. Texts that share words
    get similar vectors, so cosine ranking is meaningful and retrieval order is
    assertable without a real embedding model.
    """

    def __init__(self, dim: int = _EMBED_DIM) -> None:
        self._dim = dim

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        for token in text.lower().split():
            digest = hashlib.md5(token.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:4], "big") % self._dim] += 1.0
        # Avoid an all-zero vector (undefined cosine) for empty/OOV text.
        if not any(vector):
            vector[0] = 1.0
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


class _ScriptedLLM:
    """A fake LLMClient that returns preset responses in order and records prompts."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._responses.pop(0)


class _FailingLLM:
    """A fake LLMClient whose call always raises, simulating a transport failure."""

    def invoke(self, prompt: str) -> str:
        raise RuntimeError("connection reset")


_DOCS = [
    SourceDocument(
        text="Cats are small carnivorous mammals kept as companion pets worldwide.",
        metadata={"source": "cats.txt"},
    ),
    SourceDocument(
        text="LangGraph orchestrates multi-agent systems with typed state and routing.",
        metadata={"source": "langgraph.txt"},
    ),
    SourceDocument(
        text="ChromaDB is an in-process vector database used for retrieval augmented generation.",
        metadata={"source": "chroma.txt"},
    ),
]


def _index(embedder: _FakeEmbedder, documents: list[SourceDocument]) -> Collection:
    collection = get_ephemeral_collection("test-kb")
    DocumentIngestor(embedder, collection).ingest(documents)
    return collection


# ── Ingestion: loading + chunking ──────────────────────────────────────────


def test_load_text_files_reads_txt_and_tags_source(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("first document", encoding="utf-8")
    (tmp_path / "b.txt").write_text("second document", encoding="utf-8")
    (tmp_path / "ignore.md").write_text("not a txt", encoding="utf-8")

    documents = load_text_files(tmp_path)

    assert [doc.metadata["source"] for doc in documents] == ["a.txt", "b.txt"]


def test_load_text_files_missing_dir_raises() -> None:
    with pytest.raises(IngestionError, match="does not exist"):
        load_text_files(Path("/no/such/dir/anywhere"))


def test_load_text_files_empty_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(IngestionError, match="no readable"):
        load_text_files(tmp_path)


def test_chunk_documents_carries_metadata_and_unique_ids() -> None:
    chunks = chunk_documents(_DOCS)

    assert len(chunks) == len(_DOCS)  # short docs → one chunk each
    assert chunks[0].metadata["source"] == "cats.txt"
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


def test_chunk_documents_rejects_overlap_not_smaller_than_size() -> None:
    with pytest.raises(IngestionError, match="chunk_overlap"):
        chunk_documents(_DOCS, chunk_size=100, chunk_overlap=100)


# ── Dense retrieval (3.E) ──────────────────────────────────────────────────


def test_similarity_search_ranks_the_relevant_chunk_first() -> None:
    embedder = _FakeEmbedder()
    collection = _index(embedder, _DOCS)

    hits = similarity_search(collection, embedder, "vector database retrieval", top_k=3)

    assert hits[0].metadata["source"] == "chroma.txt"
    assert 0.0 <= hits[0].score <= 1.0


def test_similarity_search_metadata_filter_restricts_results() -> None:
    embedder = _FakeEmbedder()
    collection = _index(embedder, _DOCS)

    hits = similarity_search(
        collection, embedder, "anything at all", top_k=5, where={"source": "cats.txt"}
    )

    assert hits
    assert {hit.metadata["source"] for hit in hits} == {"cats.txt"}


def test_similarity_search_empty_query_raises() -> None:
    embedder = _FakeEmbedder()
    collection = _index(embedder, _DOCS)

    with pytest.raises(RetrievalError, match="empty query"):
        similarity_search(collection, embedder, "   ")


# ── BM25 keyword index (3.6) ───────────────────────────────────────────────


def test_bm25_ranks_document_with_the_query_term_first() -> None:
    index = BM25Index(
        [
            "the quick brown fox jumps over the lazy dog",
            "python is a popular programming language",
            "vector databases power retrieval augmented generation",
        ]
    )

    results = index.search("python programming", top_k=3)

    assert results[0][0] == 1  # second document


def test_bm25_returns_empty_when_no_term_matches() -> None:
    index = BM25Index(["alpha beta gamma", "delta epsilon"])

    assert index.search("zzz nonexistent", top_k=5) == []


# ── DocumentQAAgent (3.E headline) ─────────────────────────────────────────


def test_qa_agent_answers_from_retrieved_context() -> None:
    embedder = _FakeEmbedder()
    collection = _index(embedder, _DOCS)
    llm = _ScriptedLLM(["ChromaDB is an in-process vector database."])
    agent = DocumentQAAgent(collection, embedder, llm, top_k=2)

    result = agent.answer("What is ChromaDB?")

    assert isinstance(result, GroundedAnswer)
    assert "vector database" in result.answer
    assert "chroma.txt" in result.sources
    # The retrieved passage text must actually appear in the prompt sent to the LLM.
    assert "ChromaDB is an in-process vector database" in llm.prompts[0]


def test_qa_agent_returns_cant_answer_without_calling_llm_on_no_hits() -> None:
    embedder = _FakeEmbedder()
    collection = get_ephemeral_collection("empty-kb")  # nothing ingested
    llm = _ScriptedLLM([])  # would IndexError if invoked
    agent = DocumentQAAgent(collection, embedder, llm)

    result = agent.answer("Anything?")

    assert result.sources == []
    assert "could not find" in result.answer.lower()
    assert llm.prompts == []


def test_qa_agent_wraps_llm_failure() -> None:
    embedder = _FakeEmbedder()
    collection = _index(embedder, _DOCS)
    agent = DocumentQAAgent(collection, embedder, _FailingLLM())

    with pytest.raises(QAError, match="LLM call failed"):
        agent.answer("What is ChromaDB?")


def test_qa_agent_empty_question_raises() -> None:
    embedder = _FakeEmbedder()
    collection = _index(embedder, _DOCS)
    agent = DocumentQAAgent(collection, embedder, _ScriptedLLM([]))

    with pytest.raises(QAError, match="empty question"):
        agent.answer("  ")


# ── KnowledgeRetrievalAgent (3.P) ──────────────────────────────────────────


def test_knowledge_agent_hybrid_retrieves_relevant_chunk() -> None:
    embedder = _FakeEmbedder()
    collection = get_ephemeral_collection("kb-hybrid")
    agent = KnowledgeRetrievalAgent(embedder, collection)
    agent.ingest_documents(_DOCS)

    hits = agent.retrieve(KnowledgeQuery(question="ChromaDB vector database", top_k=3))

    assert hits
    assert hits[0].metadata["source"] == "chroma.txt"


def test_knowledge_agent_metadata_filter_scopes_hybrid_results() -> None:
    embedder = _FakeEmbedder()
    collection = get_ephemeral_collection("kb-filter")
    agent = KnowledgeRetrievalAgent(embedder, collection)
    agent.ingest_documents(_DOCS)

    hits = agent.retrieve(
        KnowledgeQuery(question="orchestration", top_k=5, where={"source": "langgraph.txt"})
    )

    assert hits
    assert {hit.metadata["source"] for hit in hits} == {"langgraph.txt"}


def test_knowledge_agent_dense_only_path_skips_fusion() -> None:
    embedder = _FakeEmbedder()
    collection = get_ephemeral_collection("kb-dense")
    agent = KnowledgeRetrievalAgent(embedder, collection)
    agent.ingest_documents(_DOCS)

    hits = agent.retrieve(
        KnowledgeQuery(question="vector database retrieval", top_k=3, hybrid=False)
    )

    # Dense-only scores are cosine similarities in [0, 1], not RRF scores.
    assert hits[0].metadata["source"] == "chroma.txt"
    assert 0.0 <= hits[0].score <= 1.0

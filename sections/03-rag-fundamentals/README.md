# Section 3 · RAG Fundamentals — 🏆 Project 1

**Phase:** 🔵 Foundations · **Fast-track:** partial (see fast-track list in [`docs/curriculum.md`](../../docs/curriculum.md))

This is where `era_platform/rag/` is born. By the end of this section you'll have a working retrieval-augmented generation pipeline over your own documents — the foundation every later agent builds retrieval on top of.

## What you'll build

Two connected deliverables that share one packaged core (`era_platform/rag/`):

- **Exercise 3.E — Document Q&A.** The smaller first step: extend the Section 2 summariser so it *answers questions from your own documents* instead of summarising text you paste in. You build and prove out the RAG core — ingestion (load → chunk → embed → index into ChromaDB) and a `similarity_search` retrieval primitive — then wrap them in a `DocumentQAAgent` that answers strictly from retrieved context (the pattern that fixes hallucination, lecture 3.1).
- **🏆 Project 1 (3.P) — Personal Knowledge Assistant.** The portfolio-ready assembly: a `KnowledgeRetrievalAgent` that wraps the 3.E core and adds **metadata filtering** and **hybrid search** (dense embeddings + BM25 keyword, lecture 3.6), plus a runnable CLI you point at a document collection of your choice.

Both are the zero-cost realisation of `docs/ERA_Platform_SOW_v1.md` §3.3 (Knowledge Retrieval Agent): ChromaDB in place of Pinecone, Gemini Embeddings in place of `text-embedding-3-large`, plain/hybrid retrieval in place of the full hybrid+rerank+HyDE pipeline. Reranking and HyDE arrive later, in Exercise 7.E.

## Lectures

Covers: why RAG fixes hallucination (3.1), embeddings and vector representations (3.2), ChromaDB setup (3.3), the ingestion pipeline (3.4), retrieval strategies — similarity, MMR, metadata filtering (3.5), hybrid search with BM25 (3.6), and evaluating retrieval quality (3.7). Full lecture list and citations: [`docs/curriculum.md`](../../docs/curriculum.md#section-3).

## Folder layout

```
03-rag-fundamentals/
├── README.md                                  # you are here
├── exercise-3E-document-qa/
│   ├── README.md                              # objective, acceptance criteria, lecture links
│   ├── starter/document_qa.py                 # stubbed TODOs — the learner edits this
│   └── solution/document_qa.py                # runnable demo driving the packaged reference
└── project-3P-personal-knowledge-assistant/
    ├── README.md
    ├── starter/knowledge_assistant.py         # CLI skeleton with TODOs
    └── solution/knowledge_assistant.py        # complete runnable CLI
```

The reusable logic lives in the installed **`era_platform/rag/`** package (type-checked under `mypy --strict`, unit-tested in [`tests/unit/test_knowledge_retrieval.py`](../../tests/unit/test_knowledge_retrieval.py)), not duplicated in `solution/`. The `solution/` scripts show how to *drive* it. This follows the pilot pattern introduced by [Exercise 2.E](../02-dev-environment-and-llm-fundamentals/exercise-2E-research-summariser/).

## What `era_platform/rag/` gains this section

| Module | Role |
|---|---|
| `embeddings.py` | `Embedder` protocol + `GeminiEmbedder` (Gemini via LlamaIndex) |
| `store.py` | ChromaDB collection factory — cosine distance, `CHROMA_PERSIST_DIR`-driven |
| `ingestion.py` | load → chunk (LlamaIndex `SentenceSplitter`) → embed → index |
| `retrieval.py` | the `similarity_search` dense primitive |
| `qa.py` | `DocumentQAAgent` — grounded question answering (3.E) |
| `bm25.py` | a dependency-free BM25 keyword index |
| `knowledge_agent.py` | `KnowledgeRetrievalAgent` — hybrid + metadata-filtered retrieval (3.P) |

## Before you start

You'll need your Google AI Studio key (free tier, no credit card) for Gemini Embeddings — see the root [Quick Start](../../README.md#-quick-start). Both `solution/` scripts also run **fully offline** with a local bag-of-words embedder when `GOOGLE_API_KEY` is unset, so you can see the end-to-end shape before spending a token.

## Where this code goes next

`era_platform/rag/` is extended, never rewritten, by later sections: Section 5 wraps retrieval in a LangGraph node, **Exercise 7.E** upgrades it with HyDE and cross-encoder reranking, and Section 12 assembles it into the full five-agent system.

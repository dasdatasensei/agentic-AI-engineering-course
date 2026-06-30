# Section 3 · RAG Fundamentals — 🏆 Project 1

**Phase:** 🔵 Foundations · **Fast-track:** partial (see fast-track list in [`docs/curriculum.md`](../../docs/curriculum.md))

This is where `era_platform/rag/` is born. By the end of this section you'll have a working retrieval-augmented generation pipeline over your own document collection — the foundation every later agent builds retrieval on top of.

## What you'll build

**Project 1 — Personal Knowledge Assistant:** a RAG-powered Q&A system over a document collection of your choice, using ChromaDB, LlamaIndex, and Gemini Embeddings.

This becomes `era_platform/rag/` — unchanged in spirit through the rest of the course. Section 5 wraps it in a LangGraph node; Section 7 upgrades its retrieval strategy; Section 12 assembles it into the full five-agent system.

## Lectures

Covers: embeddings and vector representations, chunking strategies, ChromaDB setup, retrieval strategies (similarity, MMR, metadata filtering), hybrid search (vector + keyword/BM25), and evaluating retrieval quality (precision, recall). Full lecture list and citations: [`docs/curriculum.md`](../../docs/curriculum.md#section-3).

## Files in this folder

```
03-rag-fundamentals/
├── README.md           # you are here
├── exercise.py          # starter: build the ingestion + retrieval pipeline
└── solution.py          # reference implementation — becomes era_platform/rag/
```

## Before you start

You'll need your Google AI Studio key (free tier, no credit card) for Gemini Embeddings — see the root [Quick Start](../../README.md#-quick-start) if you haven't set this up yet.

## Working through the exercise

1. Read `exercise.py` — it's scaffolded with function signatures and docstrings but no implementation
2. Implement ingestion (`load_documents`, `chunk_documents`) and retrieval (`build_index`, `query`)
3. Run it against a small document set of your own choosing — anything you have rights to use, not real client data
4. Compare against `solution.py` once you have something working, or if you get stuck

## Where this code goes next

Once this section's exercise is complete, copy your working retrieval logic into `era_platform/rag/`. Section 5 imports from there directly — there's no copy-paste in Section 5, only extension.

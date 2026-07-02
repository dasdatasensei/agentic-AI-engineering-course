# 🏆 Project 1 (3.P) · Personal Knowledge Assistant

**Section:** 3 · RAG Fundamentals
**Type:** Project (portfolio piece) · **Applies:** Lectures 3.1–3.7 · **Builds on:** Exercise 3.E

---

## What you're building

A **personal knowledge assistant**: point it at a folder of your own `.txt`
documents and ask questions across the whole collection. This is the polished,
portfolio-ready assembly of the RAG core you proved out in 3.E — the piece you
can put in front of an employer.

It centres on **`KnowledgeRetrievalAgent`** (in `era_platform/rag/knowledge_agent.py`),
which wraps the 3.E ingestion + retrieval core and adds the two capabilities that
make retrieval production-grade:

- **Metadata filtering (3.5)** — scope a query to part of your corpus, e.g. one
  source file, via a ChromaDB `where` clause.
- **Hybrid search (3.6)** — fuse **dense** embedding similarity with **sparse**
  BM25 keyword matching using Reciprocal Rank Fusion. Dense retrieval catches
  paraphrases; BM25 catches exact terms (names, error codes, acronyms) that
  embeddings often blur. RRF fuses the two rankings without having to normalise
  their very different score scales.

## How this maps to the enterprise spec

This project is the **zero-cost, simplified** realisation of
`docs/ERA_Platform_SOW_v1.md`:

- **§3.3 Knowledge Retrieval Agent** — same responsibility, swapped stack:
  **ChromaDB** for Pinecone, **Gemini Embeddings (`gemini-embedding-001`)** for
  `text-embedding-3-large`, and **plain/hybrid retrieval** for the SOW's full
  hybrid + rerank + HyDE pipeline.
- **§8 Phase 1 (Core Scaffold)** — "Pinecone namespace setup + LlamaIndex
  ingestion pipeline for a sample document corpus" is the enterprise-scale
  equivalent of this project's local ChromaDB ingestion.

## Explicit non-goals (deferred on purpose)

- **HyDE query expansion and cross-encoder reranking** → **Exercise 7.E** upgrades
  *this* agent with them. Building them now would make 7.E redundant.
- **Async / tool-calling `BaseAgent` structure** → Section 4's contract. Like the
  2.E summariser, `KnowledgeRetrievalAgent` stays synchronous.
- **Contradiction detection / evidence graphs** → the multi-agent Section 6/12 concern.

## Structure — why starter + solution (not one script)

A project is something you *assemble*, so it keeps the 2.E starter→solution
split: `starter/knowledge_assistant.py` is a CLI skeleton with `TODO`s that wire
the packaged `KnowledgeRetrievalAgent` to `argparse`; `solution/knowledge_assistant.py`
is the complete, runnable CLI. The heavy lifting lives in `era_platform/rag/`
(type-checked, unit-tested) — the CLI is a thin driver.

## Run it

```bash
# Index a folder of your own .txt files and ask a question:
python sections/03-rag-fundamentals/project-3P-personal-knowledge-assistant/solution/knowledge_assistant.py \
    --docs ./my_notes --query "What did I write about vector databases?"

# Restrict to one source file (metadata filter):
... --query "deadlines" --source project-plan.txt

# Turn off hybrid fusion to compare pure dense retrieval:
... --query "..." --dense-only
```

With `GOOGLE_API_KEY` set it uses Gemini Embeddings; without one it falls back to
a local bag-of-words embedder so you can try the flow offline. Persistence uses
`CHROMA_PERSIST_DIR` (default `./chroma_db`).

## Acceptance criteria

- [ ] Ingests every `.txt` under a directory you pass on the command line.
- [ ] Answers a query by retrieving relevant chunks, printing each with its source and score.
- [ ] `--source X` restricts results to chunks whose `source` metadata equals `X`.
- [ ] Hybrid retrieval is on by default; `--dense-only` switches to pure embedding similarity.
- [ ] Uses `logging` (not `print` for diagnostics), full type hints, and explicit error handling.

## Concepts this applies

- **3.1–3.4** — the RAG core from Exercise 3.E (grounding, embeddings, ChromaDB, ingestion).
- **3.5 — Retrieval strategies:** metadata filtering.
- **3.6 — Hybrid search:** dense + BM25 keyword fusion (Reciprocal Rank Fusion).
- **3.7 — Evaluating retrieval:** inspect the ranked results and their scores to judge quality.

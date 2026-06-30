# Section 7 · Advanced RAG — Agentic Retrieval and Knowledge Graphs

**Estimated runtime:** 2h 15m · **Fast-track:** ❌ No (full path only) · **Phase:** 🟢 Building Agents

Upgrades the retrieval logic from Section 3 with techniques that matter once "good enough" RAG stops being good enough: hypothetical document embeddings, multi-query reformulation, reranking, and detecting when sources contradict each other.

## Lectures

| # | Title | Duration |
|---|---|---|
| 7.1 | Naive RAG vs. agentic RAG — what changes when retrieval is a reasoning step | 10 min |
| 7.2 | HyDE: generating hypothetical documents to improve recall | 12 min |
| 7.3 | Multi-query retrieval: reformulating queries to widen coverage | 12 min |
| 7.4 | Reranking with cross-encoders: getting the right 10 from 80 candidates | 14 min |
| 7.5 | Corrective RAG: detecting bad retrieval and re-querying | 12 min |
| 7.6 | Contradiction detection: what to do when sources disagree | 12 min |
| 7.E | Exercise: Upgrade Project 3's retrieval agent with HyDE and reranking | — |
| 7.Q | Quiz: Advanced retrieval (8 questions) | — |

## Files in this folder

```
07-advanced-rag/
├── README.md
├── exercise.py          # upgrade era_platform/agents/rag_retrieval.py
└── solution.py
```

## Where this code goes next

This section modifies `era_platform/agents/rag_retrieval.py` and `era_platform/rag/` in place — it's an upgrade to existing code from Section 3/6, not a new module.

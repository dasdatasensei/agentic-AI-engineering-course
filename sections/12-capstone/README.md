# Section 12 · Capstone — Build and Deploy a Full Five-Agent Research System — 🏆 Project 5

**Estimated runtime:** 4h 00m · **Fast-track:** ✅ Yes (summary walkthrough) · **Phase:** 🔴 Deployment & Capstone

Everything converges here. By the end of this section, `era_platform/` is the complete ERA Platform — five agents, a typed state graph, a streaming API, full observability, and a live URL.

## What you'll build

**Project 5 — Capstone:** all five agents assembled — orchestrator, web intelligence, knowledge retrieval, quantitative analyst, and synthesis — deployed to Railway.app with Docker and GitHub Actions, traced end-to-end in LangSmith.

This is not new code grafted onto the side of the course. It is Sections 3, 5, 6, and 8's work, plus the two remaining agents (quant analyst, tool execution) and a deployment pipeline.

## Lectures

| # | Title | Duration |
|---|---|---|
| 12.1 | Capstone architecture walkthrough — how the five agents connect | 20 min |
| 12.2 | Building the orchestrator: LangGraph StateGraph with full state schema | 30 min |
| 12.3 | Web intelligence agent: Tavily + deduplication + credibility scoring | 25 min |
| 12.4 | Knowledge retrieval agent: hybrid RAG + reranking + contradiction detection | 25 min |
| 12.5 | Quantitative analyst agent: code generation + safe execution + charts | 20 min |
| 12.6 | Synthesis agent: structured report output with citations and confidence | 20 min |
| 12.7 | FastAPI + SSE: live-streaming agent progress to a browser | 20 min |
| 12.8 | LangSmith tracing + cost attribution: the full observability setup | 15 min |
| 12.9 | Deploy to Railway: your system live on the internet, for free | 15 min |
| 12.10 | Course wrap-up: what you've built, where to go next | 10 min |
| 12.P | 🏆 **Project 5 (Capstone)** | — |

## Files in this folder

```
12-capstone/
├── README.md                # you are here
├── architecture-walkthrough.md   # every decision, explained (12.1)
└── deploy/
    ├── railway.toml
    └── deploy-checklist.md
```

There's no separate `exercise.py` / `solution.py` split for this section — by now you're assembling `era_platform/` itself, not a standalone script. Treat the whole package as the exercise.

## Where this code goes next

This is the end of the course path — but not the end of the system. `era_platform/` as it stands here is what gets documented in [`docs/production.md`](../../docs/production.md): the same agent logic, state schema, and API surface, hardened for a real client deployment (Claude instead of Gemini, Pinecone instead of ChromaDB, AWS ECS instead of Railway). Read that doc once you've finished this section — it's the honest answer to "what's next."

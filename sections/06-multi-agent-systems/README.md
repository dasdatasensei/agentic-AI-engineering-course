# Section 6 · Multi-Agent Systems — Orchestration and Specialisation — 🏆 Project 3

**Estimated runtime:** 2h 59m · **Fast-track:** ✅ Yes · **Phase:** 🟢 Building Agents

This is where the orchestrator from Section 5 stops being a single agent's control flow and becomes a true supervisor coordinating specialists. `era_platform/agents/web_intelligence.py`, `rag_retrieval.py`, and `synthesis.py` are born here.

## What you'll build

**Project 3 — Three-Agent Team:** a supervisor agent coordinating a web intelligence agent, a knowledge retrieval agent, and a synthesis agent, running in parallel via `asyncio`.

## Lectures

| # | Title | Duration |
|---|---|---|
| 6.1 | Why split into multiple agents? Separation of concerns in AI systems | 10 min |
| 6.2 | Supervisor pattern: one orchestrator, many specialists | 16 min |
| 6.3 | Agent handoffs: typed message passing between agents | 14 min |
| 6.4 | Parallel execution: `asyncio.gather` for concurrent agent dispatch | 14 min |
| 6.5 | Resilient concurrency: handling partial failures so one agent can't crash the batch | 14 min |
| 6.6 | Shared state vs. message passing — tradeoffs and when to use each | 12 min |
| 6.7 | Evidence aggregation: combining outputs from multiple agents coherently | 12 min |
| 6.8 | Designing for failure: what happens when one agent in a team breaks | 12 min |
| 6.P | 🏆 **Project 3** | — |
| 6.Q | Quiz: Multi-agent patterns (8 questions) | — |

### Production note — 6.5, Resilient concurrency

A bare `await asyncio.gather(*tasks)` cancels every sibling coroutine the instant one raises — a single failing specialist takes down the whole supervisor turn. This lecture covers `asyncio.gather(*tasks, return_exceptions=True)` so failures come back as values to inspect, followed by a reduction step that separates successful `AgentResult`s from exceptions and lets the orchestrator decide whether to proceed on partial evidence, retry, or degrade gracefully.

Ties back to the per-agent retry/backoff pattern from 4.7 and the self-correction pattern from 5.8.

Sources: [Python `asyncio.gather`](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather) · [Python `asyncio` timeouts](https://docs.python.org/3/library/asyncio-task.html#timeouts) · [LangGraph durable execution](https://docs.langchain.com/oss/python/langgraph/overview)

## Files in this folder

```
06-multi-agent-systems/
├── README.md
├── exercise.py
└── solution.py          # becomes era_platform/agents/web_intelligence.py,
                          # rag_retrieval.py, synthesis.py
```

## Where this code goes next

Three new agent modules join `era_platform/agents/`, all dispatched as parallel nodes from the orchestrator built in Section 5. Section 8 wraps this whole team in a FastAPI service. Section 12 adds the remaining two agents (quant analyst, tool execution) to complete the five-agent system.

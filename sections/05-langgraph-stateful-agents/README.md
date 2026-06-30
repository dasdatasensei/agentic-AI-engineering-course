# Section 5 · LangGraph — Stateful Agents and Graph-Based Control Flow — 🏆 Project 2

**Estimated runtime:** 3h 14m · **Fast-track:** ✅ Yes · **Phase:** 🟢 Building Agents

`era_platform/agents/orchestrator.py` and `era_platform/state/` are born here. Your Section 3 RAG pipeline and Section 4 tool-using agent get wrapped into a proper `StateGraph` with typed state, conditional routing, checkpointing, and a human-in-the-loop gate.

## What you'll build

**Project 2 — Autonomous Research Assistant:** Project 1's knowledge base wrapped in a LangGraph `StateGraph`, with conditional routing, checkpoint persistence, and a human-in-the-loop review gate.

## Lectures

| # | Title | Duration |
|---|---|---|
| 5.1 | Why graphs? From linear chains to branching stateful pipelines | 10 min |
| 5.2 | StateGraph fundamentals: nodes, edges, and the state object | 18 min |
| 5.3 | Typed state with Pydantic: versioned state contracts between agents | 14 min |
| 5.4 | Conditional routing: making your graph branch based on agent output | 16 min |
| 5.5 | Checkpoint persistence: saving and resuming long-running workflows | 14 min |
| 5.6 | State compaction: trimming and summarising message history before it bloats | 14 min |
| 5.7 | Human-in-the-loop: `interrupt_before` and resume patterns | 16 min |
| 5.8 | Self-correcting loops: agents that detect and fix their own errors | 14 min |
| 5.9 | LangGraph Studio: visual debugging your graph locally | 10 min |
| 5.E | Exercise: Convert your Section 4 agent into a LangGraph StateGraph | — |
| 5.P | 🏆 **Project 2** | — |
| 5.Q | Quiz: LangGraph (10 questions) | — |

### Production note — 5.6, State compaction

Long-running graphs accumulate message history that eventually exceeds the model's context window. This lecture covers `trim_messages` (a non-destructive copy right before the LLM call) versus `RemoveMessage` / `REMOVE_ALL_MESSAGES` (which edits the persisted checkpoint permanently), plus the summarise-then-remove pattern as a dedicated compaction node ahead of `checkpoint`.

**Caveat to internalize:** after trimming, the surviving history must remain provider-valid — it must start on a human message, and every tool call must keep its matching tool result.

Sources: [LangChain — Short-Term Memory](https://docs.langchain.com/oss/python/langchain/short-term-memory) · [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)

## Files in this folder

```
05-langgraph-stateful-agents/
├── README.md
├── exercise.py          # starter: wrap Section 4's agent in a StateGraph
└── solution.py           # reference — becomes era_platform/agents/orchestrator.py
                           # + era_platform/state/schema.py
```

## Where this code goes next

`solution.py`'s `ResearchState` schema becomes `era_platform/state/schema.py`. The graph definition becomes `era_platform/agents/orchestrator.py`. Section 6 adds parallel specialist agents as additional nodes on this same graph — it does not replace it.

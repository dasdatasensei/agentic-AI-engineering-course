# Section 4 · Single Agents — Tools, Memory, and the ReAct Loop

**Estimated runtime:** 2h 30m · **Fast-track:** ✅ Yes · **Phase:** 🟢 Building Agents

Your first real agent: a single LLM with tools it can call, memory of what it's already done, and the ReAct (Reason → Act → Observe) loop driving its decisions. No LangGraph yet — that's Section 5, once you understand what a graph is actually buying you over a plain loop.

## What you'll build

**Exercise 4.E — a research agent with three tools, from scratch.** This is where the `BaseAgent` contract (`era_platform/agents/base.py`) — defined back in Section 4's setup and deliberately *not* subclassed by the 2.E summariser or the 3.P `KnowledgeRetrievalAgent` — finally gets its first real implementation: `ResearchAgent(BaseAgent)`. It runs a ReAct loop over three tools:

1. **Web search** — Tavily primary, DuckDuckGo fallback (4.5).
2. **Code execution** — a safe local Python sandbox: a static AST safety check, then a locked-down subprocess (4.6). *Not* a real sandbox provider — that's the production E2B path.
3. **Knowledge search** — wraps the `KnowledgeRetrievalAgent` you built in Project 1 (3.P), so the agent can search your own documents. Reusing Section 3's work is what makes this a *research* agent rather than three disconnected demos.

That web-search + RAG pairing is exactly what Project 2 (5.P) lifts into a LangGraph `StateGraph` — so 4.E is a running start on it, not a throwaway.

## Lectures

| # | Title | Duration |
|---|---|---|
| 4.1 | What is a tool? Functions, APIs, and side effects | 10 min |
| 4.2 | Building and registering tools: decorators and schemas | 15 min |
| 4.3 | The ReAct loop in depth: Reason → Act → Observe → Repeat | 12 min |
| 4.4 | Agent memory: conversation history, summarisation, episodic storage | 14 min |
| 4.5 | Web search tool: Tavily integration + DuckDuckGo fallback | 12 min |
| 4.6 | Code execution tool: safe Python sandbox patterns | 14 min |
| 4.7 | Error handling in agents: retries, fallbacks, and graceful failure | 12 min |
| 4.8 | Testing your agent: unit tests for tool calls and agent responses | 12 min |
| 4.E | Exercise: Build a research agent with 3 tools from scratch | — |
| 4.Q | Quiz: Agent patterns (8 questions) | — |

Full lecture list and citations: [`docs/curriculum.md`](../../docs/curriculum.md#section-4).

## Folder layout

```
04-single-agents-tools-memory-react/
├── README.md                                   # you are here
└── exercise-4E-research-agent/
    ├── README.md                               # objective, acceptance criteria, lecture links
    ├── starter/research_agent.py               # stubbed TODOs — the learner edits this
    └── solution/research_agent.py              # runnable demo driving the packaged reference
```

The reusable logic lives in the installed **`era_platform/agents/`** package (type-checked under `mypy --strict`, unit-tested in [`tests/unit/test_research_agent.py`](../../tests/unit/test_research_agent.py)), not duplicated in `solution/`. The `solution/` script shows how to *drive* it. This follows the pilot pattern introduced by [Exercise 2.E](../02-dev-environment-and-llm-fundamentals/exercise-2E-research-summariser/) and continued in 3.E/3.P.

## What `era_platform/agents/` gains this section

| Module | Role |
|---|---|
| `research_agent.py` | `ResearchAgent(BaseAgent)` — the ReAct loop, memory, retry-on-tool-failure |
| `tools/base.py` | the `Tool` abstraction, `FunctionTool`, the `@tool` decorator, `ToolError` (4.1–4.2) |
| `tools/web_search.py` | `WebSearchTool` — Tavily → DuckDuckGo (4.5) |
| `tools/code_execution.py` | `CodeExecutionTool` — AST-checked subprocess sandbox (4.6) |
| `tools/knowledge_search.py` | `KnowledgeSearchTool` — wraps the 3.P `KnowledgeRetrievalAgent` |

`base.py` already existed (the Section 4 agent contract); everything else is new this section.

## Before you start

The `solution/` runs **fully offline** — a scripted planner drives the ReAct loop and the tools use local fakes — so you can see the end-to-end shape with no keys. Supply `GOOGLE_API_KEY` (Gemini) and optionally `TAVILY_API_KEY` and it drives the real LLM and real web search instead. See the root [Quick Start](../../README.md#-quick-start).

## Where this code goes next

Section 5 takes this agent's tool definitions and ReAct logic and re-expresses them as nodes and edges in a LangGraph `StateGraph` — the underlying capability doesn't change, only the control-flow structure around it. `AgentError`, `validate_output()`, and the tools carry straight over.

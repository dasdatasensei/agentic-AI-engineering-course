# Section 4 · Single Agents — Tools, Memory, and the ReAct Loop

**Estimated runtime:** 2h 30m · **Fast-track:** ✅ Yes · **Phase:** 🟢 Building Agents

Your first real agent: a single LLM with tools it can call, memory of what it's already done, and the ReAct (Reason → Act → Observe) loop driving its decisions. No LangGraph yet — that's Section 5, once you understand what a graph is actually buying you over a plain loop.

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

## Files in this folder

```
04-single-agents-tools-memory-react/
├── README.md
├── exercise.py          # build a 3-tool ReAct agent from scratch
└── solution.py
```

## Where this code goes next

Section 5 takes this agent's tool definitions and ReAct logic and re-expresses them as nodes and edges in a LangGraph `StateGraph` — the underlying capability doesn't change, only the control-flow structure around it.

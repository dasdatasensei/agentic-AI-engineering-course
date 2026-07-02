# Exercise 4.E · Build a research agent with 3 tools from scratch

**Section:** 4 · Single Agents — Tools, Memory, and the ReAct Loop
**Type:** Coding exercise · **Applies:** Lectures 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8

---

## Learning objective

Everything Section 4 taught in isolation — tools, the ReAct loop, memory, error
handling — comes together here into one working agent. You'll build a
`ResearchAgent` that answers a question by **reasoning step by step and calling
tools**: it thinks, picks a tool, runs it, observes the result, and repeats until
it can answer — bounded by a step limit so a confused loop can't run forever.

This is also the first agent in the course to implement the `BaseAgent` contract
(`era_platform/agents/base.py`). The 2.E summariser and the 3.P
`KnowledgeRetrievalAgent` both deliberately *declined* to subclass it, deferring
the async, tool-using contract to right here. Subclassing it means you implement
`run()` and `validate_output()` and get `safe_run()`'s logging + error boundary
for free.

## The three tools

1. **Web search (4.5)** — `WebSearchTool`, Tavily primary with a DuckDuckGo
   fallback. When Tavily's free-tier quota is exhausted (a *real* limit, not an
   edge case), the tool degrades to keyless DuckDuckGo instead of failing.
2. **Code execution (4.6)** — `CodeExecutionTool`, a **safe Python sandbox**: a
   static AST safety check (no imports, no dunder access, no `os`/`subprocess`/
   `socket`/`open`…) runs *before* the snippet, then the snippet runs in a
   locked-down subprocess with a timeout. This is a *teaching* sandbox — the
   honest caveat is that a blocklist on the same host is not real isolation; the
   production ERA Platform uses an E2B micro-VM (see `docs/production.md`).
3. **Knowledge search (reuses Section 3)** — `KnowledgeSearchTool` wraps the
   `KnowledgeRetrievalAgent` you built in Project 1 (3.P). No new retrieval
   concepts — this is what turns three disconnected demos into a genuine
   *research* agent, and it's exactly the web + RAG pairing Project 2 (5.P)
   re-expresses as a LangGraph graph.

## The design mirrors 2.E / 3.E

Just as the summariser depended on a tiny `LLMClient` protocol and the RAG core on
an `Embedder` protocol, the agent depends on a tiny **`Tool`** abstraction (a
`name`, a `description`, a `parameters` schema, and a `run()`), plus the *same*
`LLMClient` protocol. That's what keeps the whole ReAct loop testable with **no
network and no API key**: the tests drive it with a scripted fake LLM and fake
tools — no live model, no Tavily call, no real subprocess, no ChromaDB.

## Where the code lives

| Path | What it is |
|---|---|
| `starter/research_agent.py` | Stubbed single-file scaffold with `TODO`s — **start here.** |
| `solution/research_agent.py` | Runnable demo that drives the packaged reference (real or offline). |
| `era_platform/agents/research_agent.py` | The reference `ResearchAgent`, packaged + type-checked. |
| `era_platform/agents/tools/` | The `Tool` abstraction and the three tools. |
| `tests/unit/test_research_agent.py` | The unit tests (repo-root `tests/`). |

> **Note on structure:** the reusable logic lives in the `era_platform.agents`
> package (not duplicated in `solution/`) so it's covered by `mypy --strict` and
> the test suite. The `starter/` is a standalone practice file — build it
> yourself, then compare against the packaged reference. Same pilot pattern as
> Exercise 2.E.

## Your task

1. Open `starter/research_agent.py` and implement every `TODO`: the `Tool`
   base, a `FunctionTool`, and the `ReActAgent`'s loop — select a tool, run it
   with retry, record the observation, repeat until finish or max-steps.
2. Run the packaged tests to see the reference behaviour you're aiming at (they
   drive the `era_platform.agents` reference with a **fake LLM and fake tools** —
   no key, no network, no spend):
   ```bash
   pytest tests/unit/test_research_agent.py -v
   ```
3. Run the demo end-to-end:
   ```bash
   python sections/04-single-agents-tools-memory-react/exercise-4E-research-agent/solution/research_agent.py
   ```
   With no keys it runs fully offline (a scripted planner + fake tools). With
   `GOOGLE_API_KEY` (and optionally `TAVILY_API_KEY`) set it drives the real
   Gemini LLM and real web search.

## Acceptance criteria

- [ ] A `Tool` has a `name`, a `description`, a `parameters` schema, and a
      `run(**kwargs) -> str`; the agent renders the tools into its prompt and
      dispatches by name.
- [ ] `ResearchAgent(BaseAgent)` implements async `run()` and `validate_output()`.
- [ ] `run()` executes a ReAct loop: reason → select a tool → observe → repeat,
      terminating on a `finish` action **or** a `max_steps` cap.
- [ ] Step history (thought / action / observation) is retained and replayed into
      each prompt (memory, 4.4).
- [ ] A failing tool call is retried with backoff (**`tenacity`**, not a
      hand-rolled loop) and, if it still fails, fed back to the model as an
      observation instead of crashing the loop (4.7).
- [ ] An unknown-tool selection or malformed model output is fed back as an
      observation, not raised.
- [ ] `validate_output()` requires a non-empty answer (and rejects references to
      tools the agent doesn't own), raising `AgentError` on failure.
- [ ] The code sandbox rejects imports / dunder access / blocked names **before**
      executing anything.
- [ ] Uses the standard `logging` module (not `print`) and full type hints.
- [ ] All tests in `tests/unit/test_research_agent.py` pass.

## Concepts this applies

- **4.1 — What is a tool:** a named, described, callable side effect.
- **4.2 — Tools: decorators and schemas:** the `Tool` abstraction + `@tool`
  decorator give the LLM enough structure to select a tool and its arguments.
- **4.3 — The ReAct loop:** reason → act → observe → repeat, bounded by max-steps.
- **4.4 — Agent memory:** retain the step trace and replay it into each prompt.
- **4.5 — Web search tool:** Tavily primary, DuckDuckGo fallback on quota loss.
- **4.6 — Safe Python sandbox:** AST safety check before a locked-down subprocess.
- **4.7 — Error handling:** `tenacity` retry/backoff, then feed failures back.
- **4.8 — Testing agents:** drive the loop with a scripted LLM and fake tools.

# Course Curriculum — Full Reference

**Agentic AI Engineering: Build & Deploy Multi-Agent Systems**

This is the complete lecture-by-lecture breakdown. For the condensed project-to-section map, see the [root README](../README.md#-the-five-projects).

## Course at a glance

| Metric | Value |
|---|---|
| Total sections | 12 |
| Total lectures (est.) | ~143 |
| Full path video | ~25 hours |
| Fast-track path | ~4 hours |
| Projects | 5 |
| Section quizzes | 12 |
| Coding exercises | 25+ |
| Capstone | 1 deployed system |

Two learning paths: the **complete path** (~25 hrs) covers every lecture, exercise, and project. The **fast-track path** (~4 hrs) is a curated subset of lectures that still includes all 5 projects. See [Fast-Track Lecture List](#fast-track-lecture-list) below.

---

## 🔵 Phase 1 · Foundations (Sections 1–3)

### Section 1 · Welcome & the Agentic AI Landscape
**Runtime:** 1h 10m · **Fast-track:** ✅

| # | Lecture | Duration |
|---|---|---|
| 1.1 | Why agentic AI is different from prompting or chatbots *(preview)* | 8 min |
| 1.2 | The two paths through this course — choose yours now | 5 min |
| 1.3 | How LLMs actually work (what you need to know, nothing more) | 12 min |
| 1.4 | The agent loop: perceive → reason → act → observe | 10 min |
| 1.5 | Agentic AI vs. RPA vs. workflow automation — honest comparison | 8 min |
| 1.6 | Framework landscape: LangGraph, CrewAI, AutoGen — when to use what | 12 min |
| 1.7 | Course project overview: what you'll build and why | 7 min |
| 1.Q | Quiz: Foundations check (5 questions) | — |

Key sources: Wang et al. (2024) *A Survey on LLM-Based Autonomous Agents* (Frontiers of Computer Science) · Yao et al. (2022) *ReAct* (arXiv:2210.03629) · Vaswani et al. (2017) *Attention Is All You Need* (arXiv:1706.03762) · LangChain Academy — Introduction to LangGraph.

### Section 2 · Development Environment & LLM Fundamentals
**Runtime:** 1h 57m · **Fast-track:** ❌ (full path only)

| # | Lecture | Duration |
|---|---|---|
| 2.1 | Setting up Python 3.12, virtual environment, VS Code / Cursor | 10 min |
| 2.2 | Free-tier API keys: Google AI Studio, Groq, Tavily, LangSmith (zero spend) | 12 min |
| 2.3 | Your first LLM call in Python — tokens, context windows, and cost | 10 min |
| 2.4 | Prompt engineering that actually matters: system roles, few-shot, chain-of-thought | 15 min |
| 2.5 | Structured outputs with Pydantic v2 | 14 min |
| 2.6 | Automated self-correction: retrying on `ValidationError` | 14 min |
| ... | (remaining 2.x lectures) | |
| 2.Q | Quiz | — |

Key sources: Brown et al. (2020) *Language Models are Few-Shot Learners* (arXiv:2005.14165) · Wei et al. (2022) *Chain-of-Thought Prompting* (arXiv:2201.11903) · Anthropic API Docs — Messages.

### Section 3 · RAG Fundamentals — 🏆 Project 1
**Runtime:** ~2h · **Fast-track:** partial

| # | Lecture | Duration |
|---|---|---|
| 3.1–3.4 | Embeddings, vector representations, chunking strategies, ChromaDB setup | — |
| 3.5 | Retrieval strategies: similarity, MMR, metadata filtering | 14 min |
| 3.6 | Hybrid search: combining vector similarity and keyword matching | 12 min |
| 3.7 | Evaluating retrieval quality: precision, recall, and why it matters | 10 min |
| 3.E | Exercise: Upgrade your summariser to answer questions from your own documents | — |
| 3.P | 🏆 **Project 1:** Personal knowledge assistant | — |
| 3.Q | Quiz: RAG architecture (8 questions) | — |

Key sources: Robertson & Walker (1994) original BM25 paper (SIGIR) · Gao et al. (2023) *RAG for LLMs: A Survey* (arXiv:2312.10997) · Es et al. (2023) *RAGAS* (arXiv:2309.15217) · LlamaIndex official retrieval/hybrid search docs.

---

## 🟢 Phase 2 · Building Agents (Sections 4–7)

### Section 4 · Single Agents — Tools, Memory, and the ReAct Loop
**Runtime:** 2h 30m · **Fast-track:** ✅

| # | Lecture | Duration |
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

### Section 5 · LangGraph — Stateful Agents and Graph-Based Control Flow — 🏆 Project 2
**Runtime:** 3h 14m · **Fast-track:** ✅

| # | Lecture | Duration |
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
| 5.P | 🏆 **Project 2:** Autonomous research assistant | — |
| 5.Q | Quiz: LangGraph (10 questions) | — |

**Production note (5.6):** Long-running graphs accumulate message history that eventually exceeds the model's context window. Teach `trim_messages` (non-destructive, pre-LLM-call) vs. `RemoveMessage` / `REMOVE_ALL_MESSAGES` (edits the persisted checkpoint permanently), plus the summarise-then-remove pattern as a dedicated compaction node. Caveat: surviving history must remain provider-valid after trimming. Sources: LangChain — Short-Term Memory docs · LangGraph Overview docs.

### Section 6 · Multi-Agent Systems — Orchestration and Specialisation — 🏆 Project 3
**Runtime:** 2h 59m · **Fast-track:** ✅

| # | Lecture | Duration |
|---|---|---|
| 6.1 | Why split into multiple agents? Separation of concerns in AI systems | 10 min |
| 6.2 | Supervisor pattern: one orchestrator, many specialists | 16 min |
| 6.3 | Agent handoffs: typed message passing between agents | 14 min |
| 6.4 | Parallel execution: `asyncio.gather` for concurrent agent dispatch | 14 min |
| 6.5 | Resilient concurrency: handling partial failures so one agent can't crash the batch | 14 min |
| 6.6 | Shared state vs. message passing — tradeoffs and when to use each | 12 min |
| 6.7 | Evidence aggregation: combining outputs from multiple agents coherently | 12 min |
| 6.8 | Designing for failure: what happens when one agent in a team breaks | 12 min |
| 6.P | 🏆 **Project 3:** Three-agent team | — |
| 6.Q | Quiz: Multi-agent patterns (8 questions) | — |

**Production note (6.5):** A bare `await asyncio.gather(*tasks)` cancels every sibling coroutine the instant one raises. Teach `asyncio.gather(*tasks, return_exceptions=True)` plus a reduction step separating successful results from exceptions. Ties to the retry/backoff pattern from 4.7 and the self-correction pattern from 5.8. Sources: Python `asyncio` docs (`gather`, timeouts) · LangGraph durable execution docs.

### Section 7 · Advanced RAG — Agentic Retrieval and Knowledge Graphs
**Runtime:** 2h 15m · **Fast-track:** ❌ (full path only)

| # | Lecture | Duration |
|---|---|---|
| 7.1 | Naive RAG vs. agentic RAG — what changes when retrieval is a reasoning step | 10 min |
| 7.2 | HyDE: generating hypothetical documents to improve recall | 12 min |
| 7.3 | Multi-query retrieval: reformulating queries to widen coverage | 12 min |
| 7.4 | Reranking with cross-encoders: getting the right 10 from 80 candidates | 14 min |
| 7.5 | Corrective RAG: detecting bad retrieval and re-querying | 12 min |
| 7.6 | Contradiction detection: what to do when sources disagree | 12 min |
| 7.E | Exercise: Upgrade Project 3's retrieval agent with HyDE and reranking | — |
| 7.Q | Quiz: Advanced retrieval (8 questions) | — |

---

## 🟠 Phase 3 · Production (Sections 8–10)

### Section 8 · APIs, Streaming, and Serving Your Agents — 🏆 Project 4
**Runtime:** 2h 00m · **Fast-track:** ❌

| # | Lecture | Duration |
|---|---|---|
| 8.1 | FastAPI fundamentals for AI engineers: routers, schemas, background tasks | 16 min |
| 8.2 | SSE streaming: push agent progress events to clients in real time | 14 min |
| 8.3 | REST API design for long-running jobs: submit → poll vs. submit → stream | 12 min |
| 8.4 | JWT authentication and API key management | 12 min |
| 8.5 | Rate limiting and graceful 429 handling | 10 min |
| 8.6 | OpenAPI documentation: auto-generate your API spec | 8 min |
| 8.P | 🏆 **Project 4:** REST API wrapper | — |
| 8.Q | Quiz: API design (6 questions) | — |

### Section 9 · Observability, Evaluation, and LangSmith
**Runtime:** 2h 00m · **Fast-track:** ✅

| # | Lecture | Duration |
|---|---|---|
| 9.1 | Why observability is not optional in production LLM systems | 8 min |
| 9.2 | LangSmith setup: wiring traces in two lines of code | 10 min |
| 9.3 | Reading a trace: what each span tells you about your agent's behaviour | 12 min |
| 9.4 | LLM evaluation: faithfulness, relevance, citation accuracy — automated | 14 min |
| 9.5 | LLM-as-judge: using a cheap model to evaluate your expensive model's output | 12 min |
| 9.6 | Building a golden dataset: curating test cases that catch regressions | 12 min |
| 9.7 | Cost tracking: attribution per agent, per run, per token | 10 min |
| 9.E | Exercise: Wire full tracing into your Project 4 API and run 3 evaluators | — |
| 9.Q | Quiz: Evaluation and observability (8 questions) | — |

### Section 10 · Security, Safety, and Responsible Agentic AI
**Runtime:** 1h 30m · **Fast-track:** ❌

| # | Lecture | Duration |
|---|---|---|
| 10.1 | Prompt injection: how attacks work and how to defend against them | 14 min |
| 10.2 | Tool permission scoping: least-privilege for AI agents | 10 min |
| 10.3 | PII handling: strip sensitive data before it reaches your agent or logs | 10 min |
| 10.4 | Hallucination mitigation: constrained generation and citation enforcement | 12 min |
| 10.5 | Dry-run mode: agents that ask before they act | 8 min |
| 10.6 | Audit logging: immutable records of every agent action | 8 min |
| 10.Q | Quiz: Security and safety (8 questions) | — |

---

## 🔴 Phase 4 · Deployment & Capstone (Sections 11–12)

### Section 11 · Docker, Deployment, and Making It Real
**Runtime:** 1h 45m · **Fast-track:** ✅

| # | Lecture | Duration |
|---|---|---|
| 11.1 | Docker for AI engineers: images, containers, compose stacks | 16 min |
| 11.2 | Containerising your FastAPI agent service | 12 min |
| 11.3 | Environment variable management: `.env` files, secrets, never in code | 8 min |
| 11.4 | Railway.app deployment: push to cloud in 15 minutes (zero cost) | 14 min |
| 11.5 | GitHub Actions: CI/CD pipeline for your agent — test, build, deploy | 16 min |
| 11.6 | Production upgrade path: ECS Fargate, Kubernetes — what scales and when | 10 min |
| 11.Q | Quiz: Deployment (6 questions) | — |

### Section 12 · Capstone — Build and Deploy a Full Five-Agent Research System — 🏆 Project 5
**Runtime:** 4h 00m · **Fast-track:** ✅ (summary walkthrough)

| # | Lecture | Duration |
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
| 12.P | 🏆 **Project 5 (Capstone):** Full multi-agent research system | — |

---

## 🏆 Project summary

| Project | Section | What you build | Key technologies |
|---|---|---|---|
| Project 1 | Sec 3 | Personal knowledge assistant | ChromaDB, LlamaIndex, Gemini Embeddings |
| Project 2 | Sec 5 | Autonomous research assistant | LangGraph, web search, RAG, HITL |
| Project 3 | Sec 6 | Three-agent team | Supervisor pattern, asyncio, multi-agent |
| Project 4 | Sec 8 | REST API + SSE streaming | FastAPI, JWT, SSE, OpenAPI |
| Project 5 | Sec 12 | Full five-agent system (deployed) | All of the above + Docker, CI/CD, Railway |

## Fast-track lecture list

For students who select the ~4-hour summary path:

`1.1, 1.2, 1.4, 1.7 · 3.1, 3.2, 3.4 · 4.1, 4.3, 4.4 · 5.1, 5.2, 5.4, 5.7 · 6.1, 6.2, 6.4 · 9.1, 9.2 · 11.1, 11.4 · 12.1, 12.9, 12.10`

All 5 projects are included in both paths.

---

*Course: Agentic AI Engineering: Build & Deploy Multi-Agent Systems · Instructor: Dr. Jody-Ann S. Jones · [drjodyannjones.com](https://www.drjodyannjones.com)*

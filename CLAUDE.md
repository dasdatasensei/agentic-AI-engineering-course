# CLAUDE.md — Agentic AI Engineering Course & ERA Platform

This repository is **both** the source code for the Udemy course _"Agentic AI
Engineering: Build & Deploy Multi-Agent Systems"_ **and** the production
portfolio project it teaches — the **ERA Platform** (Enterprise Research &
Analysis Platform), a five-agent multi-agent research system. There is no
separate platform repo. Course content and platform code live together, on
purpose, so that every learner is working in the same codebase an employer
would actually see.

See `README.md` for setup and quick-start instructions.
See `docs/ROADMAP.md` for the full section-by-section build plan.
See `docs/adr/` for the reasoning behind every major technology choice.

---

## Project Identity

| Field           | Value                                                                     |
| --------------- | ------------------------------------------------------------------------- |
| Course title    | Agentic AI Engineering: Build & Deploy Multi-Agent Systems                |
| Portfolio piece | ERA Platform (Enterprise Research & Analysis Platform)                    |
| Package         | `era_platform`                                                            |
| Python          | 3.12                                                                      |
| Repo            | https://github.com/dasdatasensei/agentic-AI-engineering-course            |
| Instructor      | Dr. Jody-Ann S. Jones, PhD — AWS Certified Machine Learning Specialist    |
| Brand           | The Data Sensei (drjodyannjones.com)                                      |
| Distribution    | Udemy · drjodyannjones.com · Kit (email/landing) · YouTube @TheDataSensei |
| License         | MIT                                                                       |

---

## Repository Architecture (READ THIS FIRST)

1. **One repo, not two.** `agentic-AI-engineering-course` is canonical. It houses:
   - `era_platform/` — the shared Python package. It does not exist fully-formed on
     day one; it **grows section by section** as the curriculum introduces each
     capability (state schema → single agent → orchestrator → RAG → API → security
     → deployment).
   - `sections/` — one folder per course section, each with its own lecture
     notes, exercises, and reference solutions.
   - Do **not** create a second repository (e.g. `era-platform`) for the
     "finished" platform. The finished platform _is_ `era_platform/` at
     Section 12.
2. **Never create versioned copies.** No `config_v2.py`, `orchestrator_new.py`,
   `agent_final.py`. If a section needs to extend something built in an
   earlier section, extend the existing file/class — don't fork it.
3. **Search before creating.** Before adding any new file, check whether a
   similar module already exists in `era_platform/` from a prior section.
4. **Honesty over polish.** Section READMEs and the top-level README must say
   plainly what has been verified end-to-end and what hasn't. Never mark a
   capability "done" or "working" without having actually run it.

---

## Course Structure Map

Four phases, twelve sections. Curriculum content and `era_platform/` code
grow in lockstep — nothing in the package should be more advanced than what
the corresponding section has taught.

| Phase                 | Sections | Focus                                                                                                       | What`era_platform/` gains                                                                                   |
| --------------------- | -------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Foundations           | 1–3      | Agentic landscape, environment setup, prompt engineering, structured outputs, RAG fundamentals              | `config.py`, `exceptions.py`, `state/schema.py` (v0), `rag/` (chunking, embeddings, ChromaDB)               |
| Building agents       | 4–7      | Single agents with tools/memory, ReAct loop, LangGraph`StateGraph`, multi-agent orchestration, advanced RAG | `agents/base.py`, `agents/orchestrator.py`, `agents/registry.py`, multi-agent handoff logic, HyDE/reranking |
| Production            | 8–10     | FastAPI for AI engineers, LangSmith tracing & evaluation, agent security                                    | `api/`, `evaluation/`, security middleware, audit logging                                                   |
| Deployment & capstone | 11–12    | Docker, Railway.app, CI/CD, full capstone                                                                   | `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, final five-agent assembly                         |

Two learner paths share the same five projects and the same codebase: a
25-hour full path and a 4-hour fast-track. Neither path gets separate code —
only separate lecture sequencing.

---

## Environments

**This repo implements exactly one running environment: dev, zero-cost,
local.** There is no staging or production deployment target inside this
repository beyond the Section 11–12 Railway.app deployment exercise.

The full enterprise/production architecture (AWS ECS Fargate, Pinecone,
Terraform, DynamoDB, etc.) is documented in `ERA_Platform_SOW_v1.docx` and
exists **only** as reference material for the "zero-cost → production
upgrade path" comparison lecture and the ADRs in `docs/adr/`. It is never
implemented as running infrastructure here. If you find yourself writing
code that talks to Pinecone, E2B, AWS Secrets Manager, or Claude Opus inside
`era_platform/` or `sections/`, stop — that belongs in the comparison
documentation, not the codebase.

- Never commit `.env` — only `.env.example`.
- Copy `.env.example` → `.env` and fill in free-tier keys before running anything.
- No AWS account, no Anthropic account, no credit card is ever required to
  complete any section.

---

## Tech Stack — Dev (Zero-Cost, What This Repo Actually Runs)

**Monthly cost: $0.**

| Layer                                 | Technology                                          | Notes                                                           |
| ------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------- |
| Orchestration                         | LangGraph 0.2                                       | `StateGraph`, typed state, conditional routing, checkpoints     |
| API                                   | FastAPI                                             | Introduced Section 8; runs on`localhost:8000`                   |
| LLM (synthesis)                       | Gemini 2.5 Flash                                    | Google AI Studio free tier — 1,500 req/day, 1M context          |
| LLM (routing / classification / eval) | Groq — Llama 3.3 70B                                | Free tier — 1,000 req/day, 30 RPM; OpenAI-compatible endpoint   |
| Embeddings                            | Gemini Embedding                                    | Same Google AI Studio key                                       |
| RAG framework                         | LlamaIndex                                          | Chunking, node parsing, query engines                           |
| Vector store                          | ChromaDB                                            | Runs in-process; persists to local disk via`CHROMA_PERSIST_DIR` |
| Reranking                             | HuggingFace cross-encoder (`sentence-transformers`) | Free substitute for Cohere Rerank v3                            |
| Web search (primary)                  | Tavily                                              | Free tier — 1,000 credits/month                                 |
| Web search (fallback, no key)         | DuckDuckGo (`duckduckgo-search`)                    | Used when Tavily quota is exhausted                             |
| Tracing / observability               | LangSmith                                           | Free tier — 5,000 traces/month                                  |
| Experiment tracking                   | MLflow                                              | Local SQLite backend, no external DB required                   |
| Containerization                      | Docker + Docker Compose                             | Local Redis / service orchestration                             |
| Deployment (capstone only)            | Railway.app                                         | Free tier, no credit card                                       |
| CI                                    | GitHub Actions                                      | Lint, type-check, unit + integration tests                      |

### Tech stack rationale (see `docs/adr/` for full write-ups)

- **LangGraph over CrewAI/AutoGen** — deterministic, typed-state orchestration
  is easier to reason about and teach than emergent multi-agent chat loops.
- **ChromaDB over Pinecone** — in-process, no account, no cost; same
  LlamaIndex interface as the production vector store, so the swap is a
  one-line config change, not a rewrite.
- **Gemini 2.5 Flash over Claude Opus** — free tier with 1M context is
  sufficient for course-scale synthesis; keeps the entire stack at $0.
- **Groq / Llama 3.3 70B over Claude Haiku** — free, fast routing/classification
  calls via an OpenAI-compatible API.
- **Railway.app over AWS ECS** — one command, free tier, no IAM/VPC setup
  required for a learner to get a real deployed URL.

---

## Production Reference Architecture (Documented Only — Do Not Implement Here)

This table exists solely to support the course's "what changes in
production" comparison lecture and the ADRs. **Nothing in this row should
ever appear as working code in `era_platform/` or `sections/`.**

| Layer                 | Production substitute             | Replaces                   |
| --------------------- | --------------------------------- | -------------------------- |
| LLM (synthesis)       | Claude Opus (`claude-opus-4-6`)   | Gemini 2.5 Flash           |
| LLM (routing/eval)    | Claude Haiku (`claude-haiku-4-5`) | Groq / Llama 3.3 70B       |
| Vector store          | Pinecone (dedicated pod)          | ChromaDB                   |
| Reranking             | Cohere Rerank v3                  | HuggingFace cross-encoder  |
| Code execution        | E2B Firecracker micro-VM sandbox  | —                          |
| Compute               | AWS ECS Fargate                   | Railway.app                |
| IaC                   | Terraform                         | —                          |
| Document/audit stores | DocumentDB, DynamoDB, S3          | —                          |
| Observability         | Prometheus + Grafana + PagerDuty  | LangSmith + MLflow (local) |

If a section needs to _teach_ one of these concepts, write it as a
documented comparison (markdown, ADR, or slide), not as importable code in
`era_platform/`.

---

## Zero-Hardcoding Rule (CRITICAL)

Nothing is hardcoded in application code. All configuration is externalized:

- **API keys, credentials** → `.env` → loaded by `era_platform/config.py`
  (`pydantic-settings` `BaseSettings`).
- **Model names** → `.env` vars `GEMINI_MODEL`, `GEMINI_EMBED_MODEL`,
  `GROQ_MODEL`.
- **All LLM prompts** → `era_platform/generation/prompt_templates.py` as
  frozen dataclasses. If you are writing a multi-line string destined for an
  LLM anywhere else, stop and move it.
- **Vector store paths / collection names** → `.env` vars
  `CHROMA_PERSIST_DIR`, `CHROMA_COLLECTION_NAME`.
- **Port numbers, hostnames, worker counts** → `.env` only (e.g.
  `ORCHESTRATOR_MAX_WORKERS`).

If you find yourself writing a string literal that looks like an API key, a
model name, a file path, or a prompt — move it to `config.py` or
`prompt_templates.py` before committing.

---

## Code Quality Standards (Non-Negotiable)

Apply every rule below to every file, every section, every time.

### 1. Type Hints

Full type hints on every function signature. No bare `dict`, `list`, or
`Any`. Use Pydantic v2 models or `TypedDict` for structured data.

```python
# WRONG
def extract_entities(text: str) -> dict:
    ...

# RIGHT
def extract_entities(text: str) -> list[ExtractedEntity]:
    ...
```

### 2. Logging

Use the standard library `logging` module — never `print()` in application
code (exercises and quick demos in Jupyter/notebooks are the only exception,
and even there, prefer `logging`).

```python
import logging

logger = logging.getLogger(__name__)
```

Log levels:

- `DEBUG` — internal state, loop iterations, intermediate agent reasoning
- `INFO` — pipeline milestones, successful operations, counts, token usage
- `WARNING` — retries, quota approaching limits, degraded fallbacks (e.g.
  Tavily → DuckDuckGo)
- `ERROR` — failures, exceptions caught at a boundary

### 3. Exceptions

Never raise a bare `Exception`. Use a specific, custom exception. The central
hierarchy in `era_platform/exceptions.py` is the target home; until it exists,
define custom exceptions per-module (`SummarizationError`, `AgentError`) — see
the Reconciliation notes under Repository Structure.

```python
# WRONG
raise Exception("Gemini call failed")

# RIGHT
raise LLMGenerationError(f"Gemini returned {status}: {body}")
```

### 4. Docstrings

Google-style docstrings on every public class and method. Module docstrings
include `Created: YYYY-MM-DD` and `Last updated: YYYY-MM-DD`.

```python
def embed_text(self, text: str) -> list[float]:
    """Embed a single text string using the Gemini Embedding API.

    Args:
        text: The input string to embed. Must be non-empty.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        EmbeddingError: If the API call fails after all retries.
    """
```

### 5. Retry Logic

Every external API call (Gemini, Groq, Tavily, LangSmith) must use a
`tenacity` decorator:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_external_api(...):
    ...
```

This matters more than usual here: every free-tier provider has a rate
limit, and a course full of learners running this code will hit them.

### 6. LLM Token Logging

Log token usage after every Gemini/Groq call so learners can see their free
quota consumption:

```python
logger.info(
    "LLM call complete | model=%s | prompt_tokens=%s | completion_tokens=%s",
    response.model,
    response.usage.prompt_tokens,
    response.usage.completion_tokens,
)
```

### 7. OOP

Organize logic into classes with clear single responsibilities. Every agent
implements the `BaseAgent` ABC (`era_platform/agents/base.py`). Avoid
module-level functions that hold state; prefer dependency injection.

### 8. No Inline Prompts

Every prompt's target home is `era_platform/generation/prompt_templates.py` as a
frozen dataclass. Until that module exists, keep prompts as named module-level
constants (not buried string literals) so the later migration is mechanical —
see the Reconciliation notes under Repository Structure.

---

## State Schema & Agent Contract

- `era_platform/state/schema.py` holds the versioned `ResearchState`
  Pydantic model — the **single source of truth** for a run. All inter-agent
  communication flows through it. No agent reads from or writes to any
  external store directly, and no unstructured string-passing between
  agents is permitted.
- `era_platform/agents/base.py` defines the `BaseAgent` ABC: every agent
  implements `run()` and `validate_output()`.
- Agents are registered in an `AgentRegistry` and instantiated by the
  orchestrator on demand — never imported and called ad hoc from elsewhere.
- Schema changes are versioned (`schema_version` field). If a section
  changes the shape of `ResearchState`, bump the version and note the
  migration in `docs/CHANGELOG.md`.

---

## RAG / Vector Store Rules

- ChromaDB persistence directory comes from `CHROMA_PERSIST_DIR` — never a
  hardcoded absolute path (learners run this on different machines/OSes).
- Embedding dimension is whatever `GEMINI_EMBED_MODEL` returns — read it
  from the API response or config, never hardcode a dimension count.
- Similarity search uses cosine distance consistently across dev and the
  documented production (Pinecone) path, so the ADR comparison stays valid.

---

## Curriculum Integrity Rules

These three production-engineering nuances are dedicated lectures, not
side notes. Any exercise or solution touching these areas must implement
them correctly — this is a differentiator versus beginner-level courses:

- **State compaction / message history trimming** — Section 5.6
- **Resilient async concurrency** via `asyncio.gather(return_exceptions=True)`
  — Section 6.5
- **Automated Pydantic self-correction** via `ValidationError` retry loops
  — Section 2.6

**Script-to-slide parity must be exact.** If a walkthrough's structure
changes (e.g. Thought→Action→Observation vs. Thought→Action→Thought→
Action→Synthesize), the script, the slide deck, and the code must all be
updated together. A mismatch here has previously shipped as a bug — treat
it as a release blocker, not a nitpick.

**Research sourcing standards.** Lecture citations and further-reading links
must come from peer-reviewed papers (arXiv, NeurIPS, ACL, SIGIR), official
framework docs, canonical textbooks (Jurafsky & Martin, Tunstall et al.), or
vetted videos from recognized academics/framework authors (Karpathy, Jay
Alammar, Stanford CS224N, LangChain Academy, DeepLearning.AI). Vendor blog
posts and lead-magnet articles are not acceptable sources.

---

## Repository Structure

### Current (what exists today)

The package grows section by section, so most target modules below are not
present yet. This is the actual on-disk state — keep it accurate as sections land.

```
agentic-AI-engineering-course/
├── era_platform/                     # Installed package (setuptools finds era_platform*)
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── base.py                   # BaseAgent ABC (async), AgentError — Section 4 contract
│   ├── generation/
│   │   ├── __init__.py
│   │   └── summarizer.py             # SummarizerAgent + ResearchSummary — Exercise 2.E
│   ├── state/
│   │   ├── __init__.py
│   │   └── schema.py                 # ResearchState / Evidence (versioned) — Section 5
│   ├── api/__init__.py               # scaffold (Section 8)
│   ├── evaluation/__init__.py        # scaffold (Section 9)
│   ├── rag/__init__.py               # scaffold (Section 3+)
│   └── security/__init__.py          # scaffold (Section 10)
│
├── sections/                         # KEBAB-case, numbered to match docs/curriculum.md
│   ├── 01-welcome-and-the-agentic-ai-landscape/          # README only
│   ├── 02-dev-environment-and-llm-fundamentals/
│   │   ├── README.md
│   │   └── exercise-2E-research-summariser/              # per-exercise folder (pilot pattern)
│   │       ├── README.md             # objective, acceptance criteria, lecture links
│   │       ├── starter/summariser.py # stubbed TODOs — the learner edits this
│   │       └── solution/summariser.py# runnable demo driving the packaged reference
│   ├── 03-rag-fundamentals/          # older flat pattern: exercise.py + solution.py
│   ├── 04-single-agents-tools-memory-react/             # exercise.py + solution.py
│   ├── 05-langgraph-stateful-agents/                    # exercise.py + solution.py
│   ├── 06-multi-agent-systems/                          # exercise.py + solution.py
│   ├── 07-advanced-rag/              # README only
│   ├── 08-apis-streaming-serving/                       # exercise.py + solution.py
│   ├── 09-observability-evaluation-langsmith/           # README only
│   ├── 10-security-safety-responsible-ai/              # README only
│   ├── 11-docker-deployment/         # README only
│   └── 12-capstone/                  # README only
│
├── tests/
│   ├── unit/                         # No external I/O; imports from era_platform
│   │   ├── test_state_schema.py
│   │   └── test_research_summariser.py
│   └── integration/                  # External APIs mocked (no real keys in CI)
│
├── docs/
│   ├── curriculum.md                 # source of truth: sections, lectures, status
│   ├── production.md
│   ├── ERA_Platform_SOW_v1.md
│   └── adr/
│
├── .github/workflows/ci.yml          # ruff (whole tree) + mypy (package+tests) + pytest
├── docker-compose.yml
├── pyproject.toml                    # PEP 621 metadata + deps
├── .env.example
├── README.md
└── CLAUDE.md                         # This file
```

**Two exercise patterns coexist.** Sections 03–08 use a flat
`exercise.py`/`solution.py` pair. **Exercise 2.E introduced the pilot pattern**
for new exercises: a per-exercise folder (`README.md` + `starter/` + `solution/`),
with the reusable logic packaged in `era_platform/` (type-checked + unit-tested)
and tests in repo-root `tests/unit/`. New exercises follow 2.E; older ones may be
retrofitted over time.

### Reconciliation notes (2.E pilot — read before "fixing" apparent gaps)

The rules below describe the **target** standard. These items are deliberately
deferred (YAGNI) until a section needs them, consistent with existing package
code (`agents/base.py` already keeps `AgentError` inline; there is no
`prompt_templates.py` yet). Do **not** treat their absence as a bug:

- **`era_platform/exceptions.py`** — not created yet. Custom exceptions currently
  live per-module (`SummarizationError`, `AgentError`). Introduce the central
  hierarchy when enough modules share one.
- **`era_platform/config.py` (`pydantic-settings`)** — not created yet. Add it
  when a section first needs externalized settings.
- **`era_platform/generation/prompt_templates.py`** — not created yet. Section 2
  prompts are module-level constants in `summarizer.py`; migrate them here once
  it exists.
- **Section folder naming** — kebab-case (e.g. `02-dev-environment-and-llm-fundamentals`),
  matching `docs/curriculum.md`, not `section_NN_snake`.
- **`Dockerfile`, `docs/ROADMAP.md`, `docs/CHANGELOG.md`** — planned; not present yet.

### Target (built incrementally — modules appear as their section introduces them)

```
era_platform/
├── config.py                     # pydantic-settings BaseSettings
├── exceptions.py                 # Custom exception hierarchy
├── agents/
│   ├── base.py                   # BaseAgent ABC: run(), validate_output()
│   ├── registry.py               # AgentRegistry
│   └── orchestrator.py           # LangGraph StateGraph (Section 6)
├── state/schema.py               # ResearchState (versioned)
├── generation/
│   ├── summarizer.py             # Exercise 2.E
│   └── prompt_templates.py       # All LLM prompts, frozen dataclasses
├── rag/{chunking,embeddings,retrieval}.py
├── evaluation/                   # Section 9
└── api/main.py                   # FastAPI entrypoint (Section 8)
```

---

## Environment Variables

Copy `.env.example` → `.env`. Course-standard keys:

| Variable                   | Purpose                             | Free tier                             |
| -------------------------- | ----------------------------------- | ------------------------------------- |
| `GOOGLE_API_KEY`           | Gemini 2.5 Flash + Gemini Embedding | aistudio.google.com                   |
| `GROQ_API_KEY`             | Groq / Llama 3.3 70B                | console.groq.com                      |
| `TAVILY_API_KEY`           | Primary web search                  | app.tavily.com — 1,000 credits/mo     |
| `LANGSMITH_API_KEY`        | Tracing                             | smith.langchain.com — 5,000 traces/mo |
| `LANGSMITH_PROJECT`        | Trace project name                  | —                                     |
| `CHROMA_PERSIST_DIR`       | Local vector store path             | —                                     |
| `GEMINI_MODEL`             | Model name override                 | —                                     |
| `GEMINI_EMBED_MODEL`       | Embedding model override            | —                                     |
| `GROQ_MODEL`               | Model name override                 | —                                     |
| `ORCHESTRATOR_MAX_WORKERS` | Max concurrent agent dispatch       | —                                     |

No key here ever requires a credit card.

---

## Environment Setup

```bash
# 1. Clone
git clone https://github.com/dasdatasensei/agentic-AI-engineering-course.git
cd agentic-AI-engineering-course

# 2. Virtual environment
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install (dev extras)
pip install -e ".[dev]"
# Key packages: langchain-google-genai chromadb tavily-python sentence-transformers
# duckduckgo-search langchain-groq langgraph langsmith mlflow fastapi uvicorn

# 4. Configure
cp .env.example .env
# fill in GOOGLE_API_KEY, GROQ_API_KEY, TAVILY_API_KEY, LANGSMITH_API_KEY
```

---

## Testing

```bash
# All tests
pytest

# Unit only — fast, no external I/O
pytest tests/unit/ -v

# Integration — mocked LLM and tool calls
pytest tests/integration/ -v

# Coverage
pytest --cov=era_platform --cov-report=term-missing
```

- Every new section's reference solution ships with at least one test.
- Every bug fix gets a regression test.
- Mock all external APIs (Gemini, Groq, Tavily) in unit tests.
- Integration tests may hit local ChromaDB but never external paid/rate-limited APIs.
- Use `pytest-asyncio` for async test functions (agent dispatch, `asyncio.gather`).

---

## Code Style & Commits

```bash
ruff format .                      # whole tree
ruff check .                       # whole tree
mypy era_platform tests --strict   # package + tests only — NOT `mypy .`
pytest tests/unit/ tests/integration/
```

> **Why not `mypy .`?** Scripts under `sections/` reuse filenames
> (`exercise.py`, `solution.py`, `summariser.py`), which mypy rejects as
> duplicate modules. Type-checking is scoped to the importable package and the
> tests; `sections/` is still covered by `ruff`. This matches
> `.github/workflows/ci.yml` — do not revert it to `mypy .`.

- Python: PEP 8 enforced by `ruff`; type annotations required on all public
  functions, enforced by `mypy --strict`.
- Commits: [Conventional Commits](https://www.conventionalcommits.org/) —
  `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.

```
feat(section-06): add LangGraph StateGraph with conditional routing
fix(rag): handle ChromaDB collection-not-found on first run
refactor(agents): extract retry logic into BaseAgent
test(section-04): add unit tests for tool-calling agent
docs(roadmap): mark Section 3 complete
chore(deps): pin langgraph to 0.2.x
```

- Branch naming: `feat/`, `fix/`, `docs/`, `chore/` prefixes.
- No secrets, credentials, or PII in any committed file.

---

## Documentation Policy

Only these docs files are permitted. Update existing files — do not create
new ones:

- `README.md`
- `CLAUDE.md` (this file)
- `docs/ROADMAP.md`
- `docs/CHANGELOG.md`
- `docs/adr/*.md` (one ADR per major technology decision)
- Per-section `README.md` under `sections/NN-kebab-title/` (and a per-exercise
  `README.md` inside each exercise folder — see the 2.E pilot pattern)

Do not create ad hoc summary reports, migration guides, or per-feature
markdown files scattered outside this list.

**Notion** is used for internal tracking only and is never student-facing
content delivery — this was deliberately decided to avoid content
cannibalization/leakage risk. Nothing written to Notion should be treated
as a canonical source when generating course material.

---

## Known Constraints

- **Free-tier ceilings are real limits, not edge cases.** Gemini: 1,500
  req/day. Groq: 1,000 req/day / 30 RPM. Tavily: 1,000 credits/month.
  LangSmith: 5,000 traces/month. Code must degrade gracefully (backoff,
  fallback to DuckDuckGo, queue) — never assume unlimited quota, since
  learners running this course will hit these ceilings routinely.
- **Production-stack code must never leak into course material.** If a PR
  or exercise references Pinecone, E2B, AWS Secrets Manager, or
  `claude-opus-4-6` outside of `docs/adr/` or the comparison lecture, that's
  a signal something drifted from the zero-cost dev stack — flag it.
- **No machine-specific paths.** `CHROMA_PERSIST_DIR` and similar must be
  relative or environment-driven; learners run this on Windows, macOS, and
  Linux.

---

## Issue Templates

Use `.github/ISSUE_TEMPLATE/`:

- `bug_report.md` — unexpected behaviour with reproduction steps
- `feature_request.md` — proposed enhancement with use case
- `content_issue.md` — lecture/exercise/solution quality issues, including
  script-to-slide mismatches or sourcing standard violations

---

## License

MIT License — Copyright (c) 2026 Dr. Jody-Ann S. Jones / The Data Sensei.

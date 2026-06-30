<div align="center">

<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12"/>
<img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/LangGraph-0.2-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangGraph"/>
<img src="https://img.shields.io/badge/Pinecone-Vector_DB-6366F1?style=for-the-badge" alt="Pinecone"/>
<img src="https://img.shields.io/badge/AWS-ECS_Fargate-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="AWS ECS"/>
<img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" alt="MIT License"/>

<br/><br/>

# ERA Platform
### Enterprise Research & Analysis Agent Platform

**A production-grade, multi-agent AI system that transforms unstructured research briefs into auditable, citation-backed intelligence reports — in under 90 minutes.**

[Business Case](#-business-case) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Deployment](#-deployment) · [Contributing](#-contributing)

</div>

---

> 🎓 **This is the full architecture, business case, and production deployment reference for the ERA Platform** — the system built incrementally throughout the [_Agentic AI Engineering_ course](#). If you're working through the course, start at the [root README](../README.md); come back here when you want the complete picture of where this system goes in production, or when the capstone (Section 12) points you here for the upgrade-path discussion.

---

## Table of Contents

- [Business Case](#-business-case)
- [What It Does](#-what-it-does)
- [Architecture](#-architecture)
  - [System Context](#system-context-c4-level-1)
  - [Agent Orchestration](#agent-orchestration)
  - [Data Flow](#data-flow)
- [Tech Stack](#-tech-stack)
  - [Development (zero-cost)](#development-zero-cost)
  - [Production](#production)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
  - [Development — zero-cost setup](#development--zero-cost-setup)
    - [Prerequisites](#prerequisites-development)
    - [Local development](#local-development-1)
    - [Environment variables](#environment-variables-development)
  - [Production setup](#production-setup)
    - [Prerequisites](#prerequisites-production)
    - [Local development](#local-development-2)
    - [Environment variables](#environment-variables-production)
- [API Reference](#-api-reference)
- [Agent Specifications](#-agent-specifications)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
  - [Docker Compose (Local)](#docker-compose-local)
  - [AWS ECS Fargate (Production)](#aws-ecs-fargate-production)
- [Observability](#-observability)
- [Testing](#-testing)
- [Security](#-security)
- [Cost Model](#-cost-model)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 💼 Business Case

### The Problem

Knowledge workers in financial services, private equity, and consulting spend **40–60 hours per engagement** on rote research: scouring hundreds of sources, extracting and reconciling data from documents, cross-referencing contradictory claims, and producing structured synthesis reports. This work is expensive, slow, and inconsistently rigorous.

| Pain Point | Current State | Business Impact |
|---|---|---|
| Research cycle time | 40–60 hours per engagement | Limits throughput per analyst |
| Cost per research cycle | \$500–\$2,000 (analyst billable time) | Compresses margins on mid-market clients |
| Source coverage | 15–25 sources per report | Gaps in evidence lead to missed risk |
| Provenance & auditability | Ad hoc; inconsistently documented | Compliance and litigation exposure |
| Scalability | Linear with headcount | Cannot absorb demand spikes without hiring |

Existing solutions fall into two unsatisfactory camps:

1. **Single-LLM summarization tools** (e.g., ChatGPT, Perplexity): fast but sacrifice quality, depth, and source provenance. Hallucination rates are unacceptable for financial and legal use cases.
2. **Traditional research workflows**: rigorous but slow, expensive, and impossible to scale.

### The Solution

The ERA Platform deploys **five specialized AI agents**, coordinated by a stateful LangGraph orchestrator, to automate the full research lifecycle — from brief ingestion to final structured report — while maintaining the rigor, citation discipline, and auditability required for enterprise use.

A **human-in-the-loop (HITL) checkpoint** gates every report before delivery, preserving final human judgment without reintroducing the bottleneck.

### The Business Case, Defended

**Return on investment is structural, not speculative:**

```
Manual research (conservative):     $500 per engagement × 100 engagements/year = $50,000/year
ERA Platform (at scale):            $0.80 per report × 100 reports + $238/mo infra = ~$2,956/year

Net annual savings (100 reports):   $47,044
Cost reduction per report:          99.8%
Payback period:                     < 1 month at 10 reports/month
```

**This is not a cost-reduction story alone.** The more important business case is **throughput expansion**: a team of 5 analysts constrained to 2 research cycles per week per analyst (10/week) can expand to 50+ research cycles per week with the same headcount — opening market segments that were previously uneconomical to serve.

**Competitive moat:**

- Source coverage (50–150 sources vs. 15–25 manual) produces demonstrably more complete intelligence
- Every claim is traceable to a source — a capability no analyst-led process delivers consistently
- The HITL gate and audit log satisfy emerging AI governance and compliance requirements (EU AI Act, FINRA 17a-4)
- Runs in < 90 minutes vs. 40–60 hours — enabling same-day turnaround on time-sensitive deals

**Target market:** Financial services firms, consulting practices, private equity due diligence teams, and corporate strategy functions processing 10+ research engagements per month.

---

## ✅ What It Does

The ERA Platform receives a natural-language **research brief** and autonomously:

1. **Decomposes** the brief into a parallel workplan across specialized agents
2. **Searches** 50–150 live web sources, scores them for credibility, and deduplicates
3. **Retrieves** relevant chunks from an internal document corpus (RAG) with hybrid dense/sparse search and reranking
4. **Analyzes** quantitative data by generating and executing Python scripts in an isolated sandbox
5. **Calls external tools** (CRM, ERP, databases) in dry-run mode pending approval
6. **Synthesizes** all evidence into a structured report with Vancouver-style citations and confidence scores
7. **Gates** the report through a human reviewer before delivery
8. **Delivers** the final report as JSON, Markdown, PDF, or DOCX

### Key Metrics

| Metric | Target |
|---|---|
| Report generation time (P95) | < 90 minutes |
| Source coverage per report | 50–150 sources |
| Hallucination rate | < 0.5% |
| Cost per report | ~\$0.80 |
| API uptime | > 99.5% |
| HITL review time (P90) | < 15 minutes |

---

## 🏗️ Architecture

### System Context (C4 Level 1)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL ACTORS                              │
│                                                                      │
│   [Analyst]          [Human Reviewer]        [API Consumer / B2B]   │
│  Submits brief       Approves HITL gate       Calls REST API         │
└────────────┬─────────────────┬───────────────────────┬──────────────┘
             │                 │                       │
             ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│              ERA PLATFORM  (FastAPI + LangGraph Engine)              │
│                                                                      │
└────────┬────────────┬──────────────┬─────────────────┬──────────────┘
         │            │              │                 │
         ▼            ▼              ▼                 ▼
  [Pinecone      [Tavily /       [E2B Code         [Redis +
   Vector DB]    SerpAPI]         Sandbox]          AWS S3]
  Doc retrieval  Live web data   Python exec        State + Reports
```

### Agent Orchestration

The platform orchestrates **five specialized agents** through a LangGraph `StateGraph`. All agents communicate exclusively through a typed `ResearchState` Pydantic model — no unstructured string passing.

```
[START]
   │
   ▼
parse_brief ──► route_tasks ──┬──► web_intelligence ──┐
                              ├──► rag_retrieval      ├──► aggregate_evidence
                              └──► tool_execution ────┘
                                                            │
                                                            ▼
                                                     quant_analysis
                                                            │
                                                            ▼
                                                     synthesis_draft
                                                            │
                                                            ▼
                                                  ┌── HITL GATE ──┐
                                                  │ approve │ reject│
                                                  ▼         ▼      │
                                           finalize   revision ─────┘
                                                  │
                                                  ▼
                                               [END]
```

| Agent | Role | Primary Tool |
|---|---|---|
| **Orchestrator** | State machine, routing, retry logic | LangGraph StateGraph |
| **Web Intelligence** | Live web search, credibility scoring, dedup | Tavily API + custom scraper |
| **Knowledge Retrieval** | Hybrid RAG with reranking, contradiction detection | Pinecone + LlamaIndex + Cohere Rerank |
| **Quantitative Analyst** | Code generation + execution, chart production | E2B sandbox + pandas / matplotlib |
| **Synthesis & Report** | Evidence synthesis, citation, structured output | Claude claude-opus-4-6 (primary) |

### Data Flow

```
User                  API Gateway          Orchestrator             Agents
────                  ───────────          ────────────             ──────
 │── POST /submit ───────────► │                 │                    │
 │   {brief, config}           │── validate ────►│                    │
 │                             │                 │── decompose task   │
 │◄── 202 {run_id} ───────────│                 │── emit START trace │
 │                             │                 │                    │
 │── GET /stream/{id} ────────►│── SSE open ────►│                    │
 │                             │                 │── dispatch ───────►│
 │◄── agent:started ──────────│◄── SSE event ───│◄─── progress ──────│
 │◄── evidence:N_sources ─────│◄── SSE event ───│◄─── evidence ──────│
 │◄── hitl:review_needed ─────│◄── SSE event ───│                    │
 │── POST /hitl/approve ──────►│── approve ─────►│                    │
 │◄── report:ready ───────────│◄── SSE event ───│◄─── final report ──│
 │── GET /reports/{id} ───────►│── fetch S3 ─────►│                   │
 │◄── {pdf, json, md} ────────│                 │                    │
```

---

## 🛠️ Tech Stack

The platform ships two configurations: a **zero-cost development stack** for building, iterating, and running the course capstone, and a **production stack** for live enterprise workloads. The agent code, `ResearchState` schema, LangGraph graph structure, and FastAPI surface area are identical between both — only the backend services swap.

### Development (zero-cost)

All services below are free tier or open source with no credit card required. Designed to get you running in under an hour today.

**Monthly cost: $0**

#### Core

| Layer | Technology | Free Tier / Cost | Notes |
|---|---|---|---|
| Orchestration | [LangGraph 0.2](https://github.com/langchain-ai/langgraph) | Free — MIT license | No change from production |
| API | [FastAPI 0.111](https://fastapi.tiangolo.com/) | Free — open source | Runs on `localhost:8000` |
| LLM (synthesis) | [Gemini 2.5 Flash](https://aistudio.google.com) | Free — 1,500 req/day, 1M context | Replaces Claude Opus; same LangChain interface via `ChatGoogleGenerativeAI` |
| LLM (routing/eval) | [Groq / Llama 3.3 70B](https://console.groq.com) | Free — 1,000 req/day, 30 RPM | OpenAI-compatible API; replaces Claude Haiku |
| Embeddings | [Gemini Embedding](https://aistudio.google.com) | Free — 10M tokens/min | Same Google AI Studio key; replaces `text-embedding-3-large` via `GoogleGenerativeAIEmbeddings` |
| RAG Framework | [LlamaIndex](https://www.llamaindex.ai/) | Free — open source | No change from production |
| Vector DB | [ChromaDB](https://docs.trychroma.com) | Free — runs in-process | `pip install chromadb`; persists to local disk; replaces Pinecone |
| Reranking | Cross-encoder (HuggingFace) | Free — `cross-encoder/ms-marco-MiniLM-L-6-v2` | Replaces Cohere Rerank; runs locally via `sentence-transformers` |
| Web Search (primary) | [Tavily](https://app.tavily.com) | Free — 1,000 credits/month | No API key change needed vs production |
| Web Search (fallback) | [DuckDuckGo](https://pypi.org/project/duckduckgo-search/) | Free — no key, no limit | `from langchain_community.tools import DuckDuckGoSearchRun`; zero signup |
| Code execution | Python subprocess + RestrictedPython | Free — stdlib | Replaces E2B sandbox; AST check before exec; sufficient for course demo |
| Task queue | `asyncio` (stdlib) | Free — no deps | Replaces Celery; agents dispatched via `asyncio.gather` in FastAPI background tasks |

#### Data & Storage

| Store | Technology | Free Tier / Cost | Notes |
|---|---|---|---|
| Hot state | Redis (Docker) | Free — `docker compose up` | Runs locally; same interface as ElastiCache |
| Vector store | ChromaDB (`PersistentClient`) | Free — unlimited local storage | Persists to `./chroma_db/`; migration to Pinecone is one line |
| Document store | SQLite (via SQLAlchemy) | Free — stdlib | Replaces DocumentDB for chunk metadata |
| Artifact store | Local filesystem (`./artifacts/`) | Free | Replaces S3; swap path prefix to `s3://` when ready |
| Audit log | SQLite append-only table | Free | Replaces DynamoDB; same schema |
| Experiment tracking | [MLflow](https://mlflow.org) (`localhost:5000`, SQLite backend) | Free — open source | `mlflow ui` — no RDS needed |
| LLM tracing | [LangSmith](https://smith.langchain.com) | Free — 5,000 traces/month | Same key and `LANGCHAIN_PROJECT` as production |

#### Infrastructure

| Component | Technology | Free Tier / Cost |
|---|---|---|
| Local runtime | Docker Compose | Free |
| Frontend hosting | [Vercel](https://vercel.com) Hobby plan | Free forever |
| API hosting (optional public demo) | [Railway.app](https://railway.app) | Free — \$5/month credit |
| CI/CD | GitHub Actions | Free — 2,000 min/month on public repos |
| Ingestion pipeline | Manual script (replaces ZenML) | Free |
| Monitoring | MLflow UI + LangSmith dashboard | Free |
| Secrets | `.env` file (local only) | Free |

> **Data privacy notice:** Google AI Studio's free tier terms permit using inputs to improve their models. Never send real client data through the development stack. Use synthetic or publicly available documents only.

> **Quality note:** Gemini 2.5 Flash produces strong results but is not equivalent to Claude Opus 4.6 for dense, long-context financial synthesis. Expect noticeable differences in citation discipline and cross-document reasoning at 100+ sources. The development stack is appropriate for building, testing, and demoing — not for delivering client-facing intelligence reports.

---

### Production

Enterprise-grade configuration for live workloads. All services are managed, SLA-backed, and horizontally scalable.

**Monthly base cost: ~\$238 (see [Cost Model](#-cost-model))**

#### Core

| Layer | Technology | Rationale |
|---|---|---|
| Orchestration | [LangGraph 0.2](https://github.com/langchain-ai/langgraph) | Deterministic stateful graph; native HITL checkpoint support; LangSmith native |
| API | [FastAPI 0.111](https://fastapi.tiangolo.com/) | Async-first; OpenAPI auto-generation; SSE support |
| LLM (synthesis) | [Claude claude-opus-4-6](https://www.anthropic.com/claude) | Best long-context reasoning; lowest hallucination rate in financial benchmarks |
| LLM (routing/eval) | [Claude claude-haiku-4-5](https://www.anthropic.com/claude) | 10× cheaper; sufficient for classification and intent tasks |
| Embeddings | [text-embedding-3-large](https://platform.openai.com/docs/guides/embeddings) | 3072-dim; top MTEB benchmark for financial text retrieval |
| RAG Framework | [LlamaIndex](https://www.llamaindex.ai/) | SentenceWindowNodeParser; HyDE query expansion; context budget management |
| Vector DB | [Pinecone](https://www.pinecone.io/) | Managed; namespace isolation per org; native hybrid search |
| Reranking | [Cohere Rerank v3](https://cohere.com/rerank) | State-of-the-art cross-encoder reranking; reduces top-80 to top-20 |
| Web Search | [Tavily](https://tavily.com/) | Research-optimized; returns raw content; credibility metadata |
| Code Sandbox | [E2B](https://e2b.dev/) | Firecracker micro-VM isolation; pre-installed scientific Python stack |
| Task Queue | [Celery + Redis](https://docs.celeryq.dev/) | Distributed async task execution; retry primitives |

#### Data & Storage

| Store | Technology | Purpose |
|---|---|---|
| Hot state | AWS ElastiCache (Redis) | Run state, SSE queues, rate limit counters |
| Vector store | Pinecone (p2.x1 pod) | 3.18M+ embedded document chunks |
| Document store | AWS DocumentDB | Raw document records + chunk metadata |
| Artifact store | AWS S3 (versioned) | Charts, PDFs, DOCX reports |
| Audit log | AWS DynamoDB (append-only) | Tool actions, HITL events, API calls |
| Experiment tracking | MLflow (RDS backend) | Cost attribution, eval metrics, model versions |
| LLM tracing | LangSmith | Agent traces, prompt I/O, latency profiling |

#### Infrastructure

| Component | Technology |
|---|---|
| Container runtime | Docker + AWS ECS Fargate |
| IaC | Terraform (modules: VPC, ECS, ElastiCache, S3, DynamoDB) |
| CI/CD | GitHub Actions |
| Ingestion pipeline | ZenML |
| Monitoring | Prometheus + Grafana |
| Alerting | PagerDuty (P0) + Slack (P1/P2) |
| Secrets | AWS Secrets Manager |

---

## 📁 Project Structure

This repo's structure reflects how the system actually gets built across the course: a single shared `era_platform/` package that grows section by section, plus a `sections/` folder holding the lecture-aligned exercises and solutions that build it.

```
agentic-AI-engineering-course/
├── era_platform/                # the shared package — what Project Structure (production)
│   │                            # below describes, fully assembled, lives here
│   ├── api/                     # FastAPI app — arrives Section 8
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── middleware/
│   │   └── schemas/
│   ├── agents/                  # arrives incrementally: Sections 5, 6, 12
│   │   ├── base.py
│   │   ├── orchestrator.py
│   │   ├── web_intelligence.py
│   │   ├── rag_retrieval.py
│   │   ├── quant_analyst.py
│   │   ├── synthesis.py
│   │   └── tool_execution.py
│   ├── rag/                     # arrives Section 3, extended Section 7
│   ├── state/                   # ResearchState schema — arrives Section 5
│   ├── evaluation/               # arrives Section 9
│   └── security/                 # arrives Section 10
│
├── sections/                    # one folder per course section, 01–12
│   ├── 01-welcome-to-agentic-ai/
│   ├── 03-rag-fundamentals/      # Project 1
│   ├── 05-langgraph/             # Project 2
│   ├── 06-multi-agent-systems/   # Project 3
│   ├── 08-apis-streaming/        # Project 4
│   ├── 12-capstone/              # Project 5 — full assembly
│   └── ...                      # each with README.md, exercise.py, solution.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── docs/
│   ├── curriculum.md            # full lecture-by-lecture breakdown
│   ├── SOW.docx                 # full Scope of Work
│   ├── adr/                     # Architecture Decision Records
│   └── diagrams/
│
├── docker-compose.yml           # local dev stack (Redis only for course use)
├── pyproject.toml
├── .env.example
└── README.md
```

### Production target shape

The structure above is what you'll have in this repo. For reference, here is the fully production-hardened version of `era_platform/` — what the package looks like once Terraform IaC, a ZenML ingestion pipeline, and ECS deployment configs are added on top of it for a real client deployment (covered conceptually in the capstone, not built section-by-section in the course):

```
era_platform/
├── api/                        # FastAPI application
│   ├── main.py                 # App factory, lifespan hooks
│   ├── routers/
│   │   ├── research.py         # POST /submit, GET /stream, GET /status
│   │   ├── hitl.py             # POST /approve, POST /reject
│   │   ├── reports.py          # GET /reports/{id}, GET /citations
│   │   └── ingest.py           # POST /ingest/documents
│   ├── middleware/
│   │   ├── auth.py             # JWT + API key validation
│   │   ├── rate_limit.py       # Token bucket per org
│   │   └── logging.py          # Structured JSON logging
│   └── schemas/
│       ├── research.py         # ResearchBrief, RunStatus, ReportResponse
│       └── events.py           # SSE event schemas
│
├── agents/                     # Agent implementations
│   ├── base.py                 # BaseAgent ABC: run(), validate_output()
│   ├── orchestrator.py         # LangGraph StateGraph definition
│   ├── web_intelligence.py     # Tavily + scraper + dedup
│   ├── rag_retrieval.py        # Pinecone + LlamaIndex + Cohere rerank
│   ├── quant_analyst.py        # E2B sandbox + chart generation
│   ├── synthesis.py            # Claude claude-opus-4-6 + ReportSchema output
│   └── tool_execution.py       # External integrations + dry-run mode
│
├── state/
│   ├── schema.py               # ResearchState Pydantic model (versioned)
│   ├── store.py                # Redis state read/write layer
│   └── checkpoint.py           # S3 checkpoint on major transitions
│
├── pipelines/                  # ZenML ingestion pipeline (production only)
│   ├── ingest_pipeline.py
│   └── steps/
│       ├── extract.py          # Unstructured.io text extraction
│       ├── clean.py            # PII removal, dedup
│       ├── chunk.py            # SentenceWindowNodeParser
│       ├── embed.py            # Batch embedding with text-embedding-3-large
│       └── index.py            # Pinecone + DocumentDB upsert
│
├── evaluation/                 # LLM eval framework
│   ├── evaluators/
│   │   ├── faithfulness.py
│   │   ├── relevance.py
│   │   ├── citation_accuracy.py
│   │   └── completeness.py
│   └── regression/
│       └── golden_dataset/
│
└── infra/                      # Terraform IaC (production only)
    ├── modules/
    │   ├── vpc/
    │   ├── ecs/
    │   ├── elasticache/
    │   ├── s3/
    │   └── dynamodb/
    └── environments/
        ├── staging/
        └── production/
```



---

## ⚡ Quick Start

---

### Development — zero-cost setup

Get the full five-agent pipeline running locally in under an hour with no paid accounts and no credit card.

#### Prerequisites (development)

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.12 | Use `pyenv` or system install |
| Docker + Docker Compose | ≥ 24.0 | Required for local Redis |
| Google AI Studio key | — | Free — [aistudio.google.com](https://aistudio.google.com) — covers Gemini Flash + embeddings |
| Groq API key | — | Free — [console.groq.com](https://console.groq.com) — covers routing/classification agents |
| Tavily API key | — | Free — 1,000 credits/month — [app.tavily.com](https://app.tavily.com) |
| LangSmith API key | — | Free — 5,000 traces/month — [smith.langchain.com](https://smith.langchain.com) |

No AWS account, no Anthropic account, no Pinecone account, no credit card.

#### Local development (development)

```bash
# 1. Clone the repository
git clone https://github.com/dasdatasensei/era-platform.git
cd era-platform

# 2. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install the development dependency set (zero-cost providers)
pip install -e ".[dev]"
# Key packages: langchain-google-genai chromadb tavily-python sentence-transformers
# duckduckgo-search langchain-groq langgraph langsmith mlflow fastapi uvicorn

# 4. Copy and populate the development environment file
cp .env.dev.example .env
# Edit .env — you only need 4 keys (see Environment Variables below)

# 5. Start local Redis (the only Docker service needed for dev)
docker compose up -d redis

# 6. Start the MLflow tracking server (SQLite backend, no database required)
mlflow server --backend-store-uri sqlite:///mlflow.db --host 0.0.0.0 --port 5000 &

# 7. Start the API server with hot reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`. MLflow UI at `http://localhost:5000`. Interactive API docs at `http://localhost:8000/docs`.

To run your first research brief against the dev stack:

```bash
curl -X POST http://localhost:8000/v1/research/submit \
  -H "Content-Type: application/json" \
  -d '{"brief": "Summarise the current state of the Caribbean fintech market.", "config": {"max_sources": 10}}'
```

#### Environment variables (development)

Copy `.env.dev.example` to `.env`. Four keys get the full system running.

```bash
# ── LLM: Gemini (synthesis + embeddings) ──────────────────────────────────────
GOOGLE_API_KEY=AIza...                # aistudio.google.com — free, no credit card

# ── LLM: Groq (routing + classification) ──────────────────────────────────────
GROQ_API_KEY=gsk_...                  # console.groq.com — free, no credit card

# ── Web Search ────────────────────────────────────────────────────────────────
TAVILY_API_KEY=tvly-...               # app.tavily.com — 1,000 free credits/month
# DuckDuckGo fallback requires no key — enabled automatically when Tavily credits run out

# ── Observability ─────────────────────────────────────────────────────────────
LANGCHAIN_API_KEY=ls__...             # smith.langchain.com — 5,000 traces/month free
LANGCHAIN_PROJECT=era-platform-dev
MLFLOW_TRACKING_URI=sqlite:///mlflow.db

# ── Local services (no cloud accounts needed) ─────────────────────────────────
REDIS_URL=redis://localhost:6379/0
CHROMA_PERSIST_DIR=./chroma_db
ARTIFACT_STORE_PATH=./artifacts
AUDIT_LOG_DB=sqlite:///audit.db

# ── Application ───────────────────────────────────────────────────────────────
APP_ENV=development
SECRET_KEY=dev-only-change-before-staging   # any string works locally
ALLOWED_ORIGINS=http://localhost:3000
ORCHESTRATOR_MAX_WORKERS=2           # lower concurrency suits free tier rate limits
HITL_APPROVAL_TIMEOUT_HOURS=2
LOG_LEVEL=INFO

# ── Feature flags: dev-stack providers ────────────────────────────────────────
SYNTHESIS_MODEL=gemini/gemini-2.5-flash
ROUTING_MODEL=groq/llama-3.3-70b-versatile
EMBEDDING_MODEL=models/gemini-embedding-001
VECTOR_STORE=chroma                  # chroma | pinecone
CODE_SANDBOX=subprocess              # subprocess | e2b
RERANKER=local                       # local | cohere
```

> **Rate limit awareness:** The dev stack is bounded by Gemini's 1,500 req/day and Groq's 1,000 req/day. For a full-depth report with 100 sources, budget approximately 15–20 Gemini calls (synthesis + eval) and 8–10 Groq calls (routing). You can comfortably run 50–60 test reports per day before hitting free-tier ceilings.

---

### Production setup

Full enterprise configuration with managed cloud services, horizontal scaling, and SLA-backed infrastructure.

#### Prerequisites (production)

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.12 | Use `pyenv` or system install |
| Docker + Docker Compose | ≥ 24.0 | Required for local stack and CI builds |
| AWS CLI | ≥ 2.0 | Required for ECS, S3, Secrets Manager |
| Terraform | ≥ 1.7 | Required for IaC provisioning |
| Anthropic API key | — | [console.anthropic.com](https://console.anthropic.com) — Claude claude-opus-4-6 + claude-haiku-4-5 |
| OpenAI API key | — | [platform.openai.com](https://platform.openai.com) — text-embedding-3-large |
| Pinecone API key | — | [pinecone.io](https://www.pinecone.io/) — dedicated p2.x1 pod |
| Tavily API key | — | [tavily.com](https://tavily.com/) — advanced tier |
| E2B API key | — | [e2b.dev](https://e2b.dev/) — Firecracker sandbox |
| Cohere API key | — | [cohere.com](https://cohere.com) — Rerank v3 |

#### Local development (production)

Run the production service configuration locally before deploying to AWS.

```bash
# 1. Clone the repository
git clone https://github.com/dasdatasensei/era-platform.git
cd era-platform

# 2. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install all dependencies
pip install -e ".[dev]"

# 4. Copy and populate the production environment file
cp .env.example .env
# Edit .env with all API keys (see Environment Variables below)

# 5. Start the full local infrastructure stack
docker compose up -d             # Starts Redis, PostgreSQL (MLflow), and LocalStack

# 6. Run database migrations
alembic upgrade head

# 7. Start the API server (with hot reload)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 8. Start a Celery worker for background agent tasks
celery -A agents.worker worker --loglevel=info --concurrency=4
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

#### Environment variables (production)

Copy `.env.example` to `.env`. **Never commit secrets to version control.**

```bash
# ── LLM Providers ─────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...           # Claude claude-opus-4-6 + claude-haiku-4-5
OPENAI_API_KEY=sk-...                  # text-embedding-3-large

# ── Vector & Document Stores ──────────────────────────────────────────────────
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws     # Your Pinecone region
PINECONE_INDEX_NAME=era-research

# ── Web Search & Code Execution ───────────────────────────────────────────────
TAVILY_API_KEY=tvly-...
SERPAPI_API_KEY=...                    # Fallback web search
E2B_API_KEY=e2b_...                    # Quantitative analyst sandbox

# ── Reranking ─────────────────────────────────────────────────────────────────
COHERE_API_KEY=...

# ── AWS ───────────────────────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_ARTIFACTS=era-artifacts-{env}
DYNAMODB_AUDIT_TABLE=era-audit-log

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── Observability ─────────────────────────────────────────────────────────────
LANGCHAIN_API_KEY=ls__...             # LangSmith tracing
LANGCHAIN_PROJECT=era-platform
MLFLOW_TRACKING_URI=postgresql://...

# ── Application ───────────────────────────────────────────────────────────────
APP_ENV=development                   # development | staging | production
SECRET_KEY=...                        # JWT signing key (generate: openssl rand -hex 32)
ALLOWED_ORIGINS=http://localhost:3000
ORCHESTRATOR_MAX_WORKERS=4
HITL_APPROVAL_TIMEOUT_HOURS=2
LOG_LEVEL=INFO

# ── Provider flags: production stack ──────────────────────────────────────────
SYNTHESIS_MODEL=claude-opus-4-6-20250514
ROUTING_MODEL=claude-haiku-4-5-20251001
EMBEDDING_MODEL=text-embedding-3-large
VECTOR_STORE=pinecone
CODE_SANDBOX=e2b
RERANKER=cohere
```

> **Production secret management:** In production, all secrets are stored in AWS Secrets Manager and injected at ECS task startup. The `.env` file is for local development only.

---

## 📡 API Reference

Base URL: `https://api.era-platform.com/v1`

All endpoints require authentication via `Authorization: Bearer <token>` (JWT) or `X-API-Key: <key>` header, except `/health`.

### Endpoints

| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `POST` | `/research/submit` | Submit a research brief | analyst |
| `GET` | `/research/{id}/stream` | SSE stream of agent progress | analyst |
| `GET` | `/research/{id}/status` | Polling fallback for run status | analyst |
| `POST` | `/hitl/{id}/approve` | Approve HITL gate | reviewer |
| `POST` | `/hitl/{id}/reject` | Reject with revision instructions | reviewer |
| `GET` | `/reports/{id}` | Retrieve final report | analyst |
| `GET` | `/reports/{id}/citations` | Retrieve structured citations | analyst |
| `POST` | `/ingest/documents` | Upload documents for RAG indexing | admin |
| `GET` | `/ingest/{job_id}/status` | Ingestion pipeline status | admin |
| `GET` | `/health` | Health check | none |

### Submit a Research Brief

```bash
curl -X POST https://api.era-platform.com/v1/research/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Provide a comprehensive competitive analysis of NVIDIA in the AI chip market, covering market share, key competitors, supply chain risks, and 12-month forward outlook.",
    "config": {
      "max_sources": 100,
      "include_quantitative": true,
      "output_formats": ["json", "pdf"],
      "hitl_required": true,
      "domain_hint": "financial_services"
    }
  }'
```

**Response:**

```json
{
  "run_id": "era_01J3K8M2N4P6Q8R0S2T4U6V8",
  "status": "accepted",
  "estimated_completion_minutes": 75,
  "stream_url": "https://api.era-platform.com/v1/research/era_01J3K8M2N4P6Q8R0S2T4U6V8/stream",
  "created_at": "2026-06-24T09:15:00Z"
}
```

### Stream Agent Progress (SSE)

```bash
curl -N -H "Authorization: Bearer $TOKEN" \
  https://api.era-platform.com/v1/research/era_01J3.../stream
```

**Event types:**

```
event: agent:started
data: {"agent": "web_intelligence", "run_id": "era_01J3...", "timestamp": "..."}

event: agent:progress
data: {"agent": "rag_retrieval", "message": "Retrieved 43 chunks", "pct": 60}

event: hitl:review_needed
data: {"run_id": "era_01J3...", "draft_url": "...", "reviewer_url": "...", "expires_at": "..."}

event: report:ready
data: {"run_id": "era_01J3...", "report_url": "...", "pdf_url": "...", "citation_count": 67}

event: error
data: {"run_id": "era_01J3...", "agent": "web_intelligence", "code": "RATE_LIMITED", "retrying": true}
```

### Retrieve a Report

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.era-platform.com/v1/reports/era_01J3...?format=json"
```

Full OpenAPI 3.1 specification: [`docs/openapi.yaml`](docs/openapi.yaml)

---

## 🤖 Agent Specifications

### Orchestrator

- **Framework:** LangGraph `StateGraph` with typed `ResearchState` (Pydantic v2)
- **Routing:** LLM-based conditional routing at `parse_brief → route_tasks`
- **Parallelism:** `asyncio.gather` for web / RAG / tool agents; serial for quant → synthesis
- **State persistence:** Redis (TTL 24h) + S3 checkpoint on every major transition
- **Retry policy:** Exponential backoff — 3 attempts per agent at 2s / 8s / 32s delays
- **HITL gate:** Native LangGraph `interrupt_before`; waits up to 2h for approval webhook

### Web Intelligence Agent

- **Primary tool:** Tavily Search API (`include_raw_content: true`, `search_depth: advanced`)
- **Fallback:** SerpAPI + async custom scraper (`httpx` + `BeautifulSoup4`)
- **Source limit:** 150 crawled; top 50 by credibility score returned to state
- **Credibility scoring:** Domain authority heuristic (gov > edu > established news > commercial)
- **Deduplication:** URL canonicalization + MinHash LSH (Jaccard threshold 0.85)
- **Safety:** PII patterns stripped before writing to state; no raw content persisted to logs

### Knowledge Retrieval Agent (Agentic RAG)

- **Retrieval strategy:** Hybrid — dense cosine (top-k=40) + sparse BM25 (top-k=40) → Reciprocal Rank Fusion → Cohere Rerank v3 (top-20)
- **Query expansion:** HyDE (Hypothetical Document Embeddings) for domain-specific queries
- **Context budget:** 16K tokens per agent turn (LlamaIndex `SentenceWindowNodeParser`)
- **Contradiction detection:** Same-claim extraction → NLI entailment check (DeBERTa-v3-large)
- **Provenance:** Every chunk tagged with `doc_id`, `page`, `section`, `ingest_timestamp`

### Quantitative Analyst Agent

- **Execution:** E2B cloud sandbox (Firecracker micro-VM, Python 3.12, 5-min timeout)
- **Code safety:** AST static analysis; blocklist: `os.system`, `subprocess`, `__import__`, `socket`, `open` in write mode
- **Available libraries:** `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `plotly`
- **Outputs:** PNG charts (300 DPI) + JSON data tables + LaTeX equation strings → S3

### Synthesis & Report Agent

- **Primary LLM:** `claude-opus-4-6` (200K context; primary for long-context synthesis)
- **Fallback LLM:** `gpt-4.1` (on Anthropic rate-limit or outage; same output schema enforced via `instructor`)
- **Output schema:** `ReportSchema` (Pydantic): `title`, `executive_summary`, `sections[]`, `citations[]`, `confidence_per_claim`
- **Hallucination mitigation:** Constrained generation — every factual claim must map to ≥1 source in the evidence store; unmapped claims are flagged, not included

---

## ⚙️ Configuration

Runtime behaviour is controlled via `config/settings.py` using `pydantic-settings`. All values can be overridden via environment variables.

```python
# config/settings.py (excerpt)
class Settings(BaseSettings):
    # Orchestrator
    orchestrator_max_workers: int = 4
    agent_retry_attempts: int = 3
    hitl_approval_timeout_hours: int = 2

    # Retrieval
    pinecone_top_k_dense: int = 40
    pinecone_top_k_sparse: int = 40
    cohere_rerank_top_n: int = 20
    rag_context_budget_tokens: int = 16_000

    # Web search
    tavily_max_sources: int = 150
    tavily_returned_sources: int = 50
    minhash_jaccard_threshold: float = 0.85

    # LLMs
    synthesis_model: str = "claude-opus-4-6-20250514"
    routing_model: str = "claude-haiku-4-5-20251001"
    synthesis_max_output_tokens: int = 12_000

    # Cost guard
    max_cost_per_report_usd: float = 15.0   # Circuit breaker
```

---

## 🚀 Deployment

### Docker Compose (Local)

```bash
# Start the full local stack
docker compose up -d

# Services started:
#   era-api        → localhost:8000
#   era-worker     → Celery worker (4 concurrency)
#   redis          → localhost:6379
#   postgres       → localhost:5432  (MLflow backend)
#   mlflow         → localhost:5000
#   prometheus     → localhost:9090
#   grafana        → localhost:3001  (admin / admin)

# View logs
docker compose logs -f era-api era-worker

# Tear down
docker compose down -v
```

### AWS ECS Fargate (Production)

```bash
# 1. Configure AWS credentials
aws configure

# 2. Initialise Terraform
cd infra/environments/production
terraform init

# 3. Plan the deployment
terraform plan -var-file="production.tfvars"

# 4. Apply (creates VPC, ECS cluster, ElastiCache, S3 buckets, DynamoDB)
terraform apply -var-file="production.tfvars"

# 5. Push the Docker image (CI/CD handles this on merge to main)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

docker build -t era-platform .
docker tag era-platform:latest $ECR_REGISTRY/era-platform:latest
docker push $ECR_REGISTRY/era-platform:latest

# 6. Force a new ECS deployment
aws ecs update-service \
  --cluster era-production \
  --service era-api \
  --force-new-deployment
```

### CI/CD Pipeline

Every pull request triggers:

```
push → lint (ruff) → type-check (mypy) → unit tests → integration tests → build Docker image
                                                                              │
merge to main ────────────────────────────────────────────────────────────────►
                                                                              │
                                                                    LLM eval regression
                                                                    (golden dataset)
                                                                              │
                                                                    ECS deploy (staging)
                                                                              │
                                                                    Smoke tests
                                                                              │
                                                                    ECS deploy (production)
```

Deployment to production requires: all tests pass + eval regression score ≥ baseline − 5 points + manual approval gate in GitHub Actions.

---

## 📊 Observability

### Metrics (Prometheus + Grafana)

| Metric | Type | Description |
|---|---|---|
| `era_report_duration_seconds` | Histogram | Wall-clock time per report (P50/P95/P99) |
| `era_agent_invocations_total` | Counter | Agent invocations by agent name and status |
| `era_hitl_review_duration_seconds` | Histogram | Time from `review_needed` to decision |
| `era_cost_per_report_usd` | Gauge | Aggregated cost per run (LLM + infra + tools) |
| `era_hallucination_rate` | Gauge | Rolling % of flagged claims (eval sample) |
| `era_rag_retrieval_precision` | Gauge | Precision@20 from LangSmith eval |
| `era_api_requests_total` | Counter | API requests by endpoint, method, status |

Grafana dashboard: `infra/dashboards/era-overview.json`

### Tracing (LangSmith)

Every agent invocation emits a LangSmith trace capturing: prompt, model, token counts, latency, and any tool calls. Traces are queryable by `run_id`, `org_id`, `agent_name`, and date range.

### Alerting

| Alert | Severity | Channel |
|---|---|---|
| `P95 report duration > 120 min` | P1 | PagerDuty |
| `Agent error rate > 5%` | P1 | PagerDuty |
| `Hallucination rate > 1%` | P1 | Slack `#ml-alerts` |
| `Cost per report > $15` | P2 | Slack `#cost-alerts` |
| `API error rate > 1%` | P1 | PagerDuty |
| `HITL queue depth > 10` | P2 | Slack `#ops-alerts` |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Unit tests only (fast; no external I/O)
pytest tests/unit/ -v

# Integration tests (mocked LLM and tool calls)
pytest tests/integration/ -v

# End-to-end tests (requires staging environment)
ERA_ENV=staging pytest tests/e2e/ -v --timeout=600

# LLM eval regression suite (requires LangSmith + Anthropic API)
pytest evaluation/regression/ -v --eval-run-name="ci-$(git rev-parse --short HEAD)"

# Coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Test Strategy

| Layer | Scope | Mock Strategy | Target Coverage |
|---|---|---|---|
| Unit | Pure functions, Pydantic schemas, utility modules | No mocks needed | > 90% |
| Integration | Agent logic, orchestrator routing, state transitions | Mock LLM responses + tool calls | > 80% |
| End-to-end | Full brief → report pipeline | Live staging environment | 10 golden brief scenarios |
| LLM Eval | Report quality (faithfulness, relevance, citation accuracy) | No mocking — real LLM output | 50 golden report pairs |

---

## 🔒 Security

### Authentication & Authorization

- **User sessions:** JWT (RS256), 1-hour expiry, refresh token rotation
- **B2B API consumers:** SHA-256 hashed API keys stored in DynamoDB; never logged in plaintext
- **RBAC roles:** `viewer` · `analyst` · `reviewer` · `admin` — enforced per endpoint via FastAPI dependency injection

### Data Security

- All data encrypted at rest (S3 SSE-KMS, DynamoDB encryption, Pinecone encryption enabled)
- All data encrypted in transit (TLS 1.3 minimum; mutual TLS between internal services)
- Multi-tenant data isolation: Pinecone namespace, DocumentDB `org_id` filter, S3 key prefix, DynamoDB partition key — enforced at the data access layer, not the application layer
- PII stripped from web scrape outputs before writing to agent state; never persisted to LangSmith traces

### Agent Security

- **Prompt injection defense:** Brief content sanitized before LLM inclusion; system/user role separation strictly enforced
- **Tool permission scoping:** Each agent operates with an explicit allowlist of tool names; orchestrator enforces at dispatch time
- **Code execution safety:** E2B Firecracker micro-VM (hypervisor-level isolation); AST static analysis + blocklist before execution
- **Secrets:** Zero secrets in environment variables in production; all credentials in AWS Secrets Manager

### Vulnerability Reporting

Please report security vulnerabilities to **security@era-platform.com** — do not open a public GitHub issue for security concerns. We follow a 90-day coordinated disclosure policy.

---

## 💰 Cost Model

The platform operates in two cost modes that correspond directly to the two stack configurations in [Tech Stack](#-tech-stack).

### Development cost (zero-cost stack)

| Component | Dev substitute | Cost |
|---|---|---|
| LLM synthesis | Gemini 2.5 Flash (free tier) | \$0 |
| LLM routing | Groq / Llama 3.3 70B (free tier) | \$0 |
| Embeddings | Gemini Embedding (free tier) | \$0 |
| Vector store | ChromaDB (local) | \$0 |
| Web search | Tavily (1,000 free credits/mo) | \$0 |
| Code execution | Python subprocess | \$0 |
| Observability | LangSmith (5K traces free) + MLflow local | \$0 |
| Infrastructure | localhost + Docker | \$0 |
| **Total** | | **\$0 / month** |

Practical daily ceiling: ~50–60 full research runs before hitting Gemini's 1,500 req/day free-tier limit. More than sufficient for course development and portfolio demos.

---

### Production cost per report (moderate-complexity brief, ~100 sources)

| Component | Usage | Unit Cost | Cost |
|---|---|---|---|
| Claude claude-opus-4-6 (16K context input) | ~16,000 tokens | \$0.000015/token | ~\$0.24 |
| Claude claude-haiku-4-5 (routing + evals) | ~8,000 tokens | \$0.0000008/token | ~\$0.006 |
| text-embedding-3-large | ~5,000 tokens | \$0.00000013/token | ~\$0.001 |
| Tavily Search (advanced tier) | 50 queries | \$0.01/query | ~\$0.50 |
| E2B sandbox | ~60 seconds | \$0.00025/second | ~\$0.015 |
| ECS Fargate compute (amortized) | ~30 min × 0.5 vCPU | \$0.04048/vCPU-hr | ~\$0.034 |
| Pinecone + Redis + S3 (amortized) | Per-run ops | Shared infra | ~\$0.008 |
| **Total** | | | **~\$0.80/report** |

### Production monthly infrastructure base cost (v1)

| Resource | Configuration | Monthly |
|---|---|---|
| ECS Fargate (API + 4 workers) | 0.5 vCPU / 1 GB × 5 tasks | ~\$35 |
| ElastiCache Redis | `cache.t3.small` | ~\$25 |
| Pinecone dedicated pod | `p2.x1` | ~\$70 |
| DocumentDB | `db.t3.medium` | ~\$55 |
| RDS PostgreSQL (MLflow) | `db.t3.micro` | ~\$15 |
| S3 + DynamoDB + CloudWatch | Standard usage | ~\$18 |
| ALB + data transfer | Standard config | ~\$20 |
| **Total base infra** | | **~\$238/month** |

Break-even: **< 30 reports/month** at \$10 manual cost savings per report. At 100 reports/month, net savings exceed \$47,000/year.

---

## 🗺️ Roadmap

### v1.0 — MVP (Current)
- [x] Five-agent orchestration with LangGraph
- [x] Hybrid RAG with Pinecone + Cohere reranking
- [x] HITL checkpoint + review UI
- [x] FastAPI + SSE streaming
- [x] ECS Fargate deployment + Terraform IaC
- [x] LangSmith tracing + MLflow cost attribution
- [x] JWT + RBAC authentication

### v1.1 — Quality & Reliability (Q3 2026)
- [ ] Citation accuracy evaluator integrated into CI gate
- [ ] Grafana SLO dashboard with burn-rate alerts
- [ ] Multi-language brief support (Spanish, Portuguese, French)
- [ ] DOCX report template customization per org
- [ ] Slack / Teams notification integration for HITL events

### v2.0 — Scale & Enterprise (Q1 2027)
- [ ] EKS migration (> 500 concurrent runs)
- [ ] On-premise LLM option (Llama 3 / Mistral via vLLM)
- [ ] Knowledge graph layer for cross-report entity linking
- [ ] SOC 2 Type II audit completion
- [ ] Self-serve org onboarding + billing integration (Stripe)
- [ ] Voice brief input (Whisper transcription)

---

## 🤝 Contributing

Contributions are welcome. Please read this section before opening a PR.

### Development Setup

Follow the [Quick Start](#-quick-start) guide above. All code must pass the following before opening a PR:

```bash
# Format
ruff format .

# Lint
ruff check .

# Type checking
mypy . --strict

# Tests (unit + integration)
pytest tests/unit/ tests/integration/
```

### Pull Request Process

1. Fork the repository and create a feature branch from `main`: `git checkout -b feat/your-feature-name`
2. Write tests for new functionality — unit tests for pure logic, integration tests for agent behaviour
3. Ensure `pytest tests/unit/ tests/integration/` passes with no failures
4. Update documentation: `README.md`, docstrings, and any affected ADRs in `docs/adr/`
5. Open a PR against `main` with a description covering: **what**, **why**, and **how you tested it**
6. A maintainer will review within 3 business days

### Code Style

- Python: [PEP 8](https://peps.python.org/pep-0008/) enforced by `ruff`; type annotations required on all public functions (enforced by `mypy --strict`)
- Commits: [Conventional Commits](https://www.conventionalcommits.org/) — e.g., `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Branch naming: `feat/`, `fix/`, `docs/`, `chore/` prefixes
- No secrets, credentials, or PII in any committed file

### Issue Templates

Use the issue templates in `.github/ISSUE_TEMPLATE/`:

- `bug_report.md` — unexpected behaviour with reproduction steps
- `feature_request.md` — proposed enhancement with use case
- `agent_quality.md` — report quality issues with example brief + output

---

## 📄 License

```
MIT License

Copyright (c) 2026 Dr. Jody-Ann S. Jones / The Data Sensei

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">

Built by **[Dr. Jody-Ann S. Jones](https://www.drjodyannjones.com)** · [The Data Sensei](https://www.drjodyannjones.com) · [LinkedIn](https://www.linkedin.com/in/drjodyannjones) · [GitHub](https://github.com/dasdatasensei)

*AWS Certified Machine Learning – Specialty · PhD, International Political Economy*

</div>

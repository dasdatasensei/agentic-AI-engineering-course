# Section 8 · APIs, Streaming, and Serving Your Agents — 🏆 Project 4

**Estimated runtime:** 2h 00m · **Fast-track:** ❌ No · **Phase:** 🟠 Production

`era_platform/api/` is born here. Your Section 6 three-agent team stops being something you run from a script and becomes a real HTTP service other people (or your own frontend) can call.

## What you'll build

**Project 4 — REST API:** your three-agent team exposed via FastAPI with SSE streaming, JWT authentication, and an auto-generated OpenAPI 3.1 spec.

## Lectures

| # | Title | Duration |
|---|---|---|
| 8.1 | FastAPI fundamentals for AI engineers: routers, schemas, background tasks | 16 min |
| 8.2 | SSE streaming: push agent progress events to clients in real time | 14 min |
| 8.3 | REST API design for long-running jobs: submit → poll vs. submit → stream | 12 min |
| 8.4 | JWT authentication and API key management | 12 min |
| 8.5 | Rate limiting and graceful 429 handling | 10 min |
| 8.6 | OpenAPI documentation: auto-generate your API spec | 8 min |
| 8.P | 🏆 **Project 4** | — |
| 8.Q | Quiz: API design (6 questions) | — |

## Files in this folder

```
08-apis-streaming-serving/
├── README.md
├── exercise.py          # starter: wrap your Section 6 agent team in FastAPI
└── solution.py           # becomes era_platform/api/main.py + routers/
```

## Additional setup for this section

No new free-tier keys needed — this section is pure application code on top of what you already have. You will, however, want a local Redis instance for SSE event propagation:

```bash
docker compose up -d redis
```

## Where this code goes next

`solution.py` becomes `era_platform/api/main.py`, `routers/research.py`, and the auth/rate-limit middleware. Section 9 adds LangSmith tracing on top of every request this service handles. Section 11 containerizes it. Section 12 is this same service with two more agents wired in.

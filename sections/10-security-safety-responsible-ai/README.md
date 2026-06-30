# Section 10 · Security, Safety, and Responsible Agentic AI

**Estimated runtime:** 1h 30m · **Fast-track:** ❌ No (full path only) · **Phase:** 🟠 Production

`era_platform/security/` is born here. Covers the failure modes that don't show up in a demo but absolutely show up in production: prompt injection, over-privileged tools, PII leaking into logs, and agents that act before anyone reviews what they're about to do.

## Lectures

| # | Title | Duration |
|---|---|---|
| 10.1 | Prompt injection: how attacks work and how to defend against them | 14 min |
| 10.2 | Tool permission scoping: least-privilege for AI agents | 10 min |
| 10.3 | PII handling: strip sensitive data before it reaches your agent or logs | 10 min |
| 10.4 | Hallucination mitigation: constrained generation and citation enforcement | 12 min |
| 10.5 | Dry-run mode: agents that ask before they act | 8 min |
| 10.6 | Audit logging: immutable records of every agent action | 8 min |
| 10.Q | Quiz: Security and safety (8 questions) | — |

## Files in this folder

```
10-security-safety-responsible-ai/
├── README.md
├── exercise.py
└── solution.py          # becomes era_platform/security/*
```

## Where this code goes next

Tool permission scoping and dry-run mode get applied directly to `era_platform/agents/tool_execution.py` (introduced in Section 12). Audit logging wraps every agent action across the whole system.

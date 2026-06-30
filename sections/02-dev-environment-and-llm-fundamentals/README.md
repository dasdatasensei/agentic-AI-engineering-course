# Section 2 · Development Environment & LLM Fundamentals

**Estimated runtime:** 1h 57m · **Fast-track:** ❌ No (full path only) · **Phase:** 🔵 Foundations

Gets your machine ready: Python 3.12, a virtual environment, and your four free-tier API keys. No agent code yet — this section is about making your first raw LLM call and understanding what you're actually paying for (in tokens, not dollars) when you do.

## Lectures

| # | Title | Duration |
|---|---|---|
| 2.1 | Setting up Python 3.12, virtual environment, VS Code / Cursor | 10 min |
| 2.2 | Free-tier API keys: Google AI Studio, Groq, Tavily, LangSmith (zero spend) | 12 min |
| 2.3 | Your first LLM call in Python — tokens, context windows, and cost | 10 min |
| 2.4 | Prompt engineering that actually matters: system roles, few-shot, chain-of-thought | 15 min |
| ... | (remaining lectures — see [`docs/curriculum.md`](../../docs/curriculum.md#section-2)) | |

## Files in this folder

```
02-dev-environment-and-llm-fundamentals/
├── README.md
├── exercise.py          # your first LLM call, with logging and error handling
└── solution.py
```

## Setup checklist

- [ ] Python ≥ 3.12 installed
- [ ] Virtual environment created and activated (`python3.12 -m venv .venv`)
- [ ] Google AI Studio key obtained — [aistudio.google.com](https://aistudio.google.com)
- [ ] Groq key obtained — [console.groq.com](https://console.groq.com)
- [ ] Tavily key obtained — [app.tavily.com](https://app.tavily.com)
- [ ] LangSmith key obtained — [smith.langchain.com](https://smith.langchain.com)
- [ ] `.env` populated from `.env.example` at repo root

This checklist mirrors the root [Quick Start](../../README.md#-quick-start) — if you've already done that, you're done here too.

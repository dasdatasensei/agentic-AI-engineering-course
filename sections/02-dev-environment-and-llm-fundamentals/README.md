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
| 2.5 | Structured outputs with Pydantic — making LLMs return reliable JSON | 14 min |
| 2.6 | Self-correcting structured outputs: catching ValidationError and re-asking the model | 12 min |
| 2.7 | Streaming responses and Server-Sent Events (SSE) basics | 10 min |
| 2.8 | Multi-provider switching: same code, different LLMs | 12 min |
| 2.E | Exercise: Build a structured research summariser in 30 lines | — |
| 2.Q | Quiz: LLM fundamentals (8 questions) | — |

Full lecture details and reading lists: [`docs/curriculum.md`](../../docs/curriculum.md#section-2).

## Files in this folder

```
02-dev-environment-and-llm-fundamentals/
├── README.md
├── demo_2_1_setup_check.py              # 2.1 — Python 3.12 + virtual environment check
├── demo_2_2_env_check.py                # 2.2 — required API keys present in .env (never prints values)
├── demo_2_3_first_llm_call.py           # 2.3 — one Gemini call: tokens, context window, cost
├── demo_2_4_prompt_engineering.py       # 2.4 — baseline vs system role vs few-shot vs chain-of-thought
├── demo_2_7_streaming_responses.py      # 2.7 — .stream(), SSE framing, merging chunks for usage
└── exercise-2E-research-summariser/     # Exercise 2.E (per-exercise pilot pattern)
    ├── README.md                        # objective, acceptance criteria, lecture links
    ├── starter/summariser.py            # stubbed TODOs — the learner edits this
    └── solution/summariser.py           # runnable demo driving the packaged reference
```

The reusable logic lives in the installed package at
[`era_platform/generation/summarizer.py`](../../era_platform/generation/summarizer.py)
(type-checked + unit-tested), driven by the `solution/` script — the pilot
pattern later exercises follow.

## Verification status

Last checked 2026-11-08 by running each script against the free-tier stack.

| Script | Status |
|---|---|
| `demo_2_1_setup_check.py` | ✅ Runs clean |
| `demo_2_2_env_check.py` | ✅ Runs; correctly fails and names any missing keys |
| `demo_2_3_first_llm_call.py` | ✅ Runs. Known issue: with `langchain-google-genai` 4.x the response logs as a list of content blocks (`[{'type': 'text', ...}]`) rather than plain text. Kept as recorded; 2.7 uses `.text` instead. |
| `demo_2_4_prompt_engineering.py` | ✅ Runs all four prompt variants |
| 2.5 / 2.6 demos | ❌ Not in the repo yet (`demo_2_5_structured_outputs.py`, `demo_2_6_self_correcting_outputs.py`) |
| `demo_2_7_streaming_responses.py` | ✅ Runs; ruff + `mypy --strict` clean |
| 2.8 demo | ❌ Not written yet |

All demos read `GOOGLE_API_KEY` from `.env`; 2.2 also needs `GROQ_API_KEY`, `TAVILY_API_KEY` and `LANGSMITH_API_KEY`.

## Setup checklist

- [ ] Python ≥ 3.12 installed
- [ ] Virtual environment created and activated (`python3.12 -m venv .venv`)
- [ ] Google AI Studio key obtained — [aistudio.google.com](https://aistudio.google.com)
- [ ] Groq key obtained — [console.groq.com](https://console.groq.com)
- [ ] Tavily key obtained — [app.tavily.com](https://app.tavily.com)
- [ ] LangSmith key obtained — [smith.langchain.com](https://smith.langchain.com)
- [ ] `.env` populated from `.env.example` at repo root

This checklist mirrors the root [Quick Start](../../README.md#-quick-start) — if you've already done that, you're done here too.

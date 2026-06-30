# Section 9 · Observability, Evaluation, and LangSmith

**Estimated runtime:** 2h 00m · **Fast-track:** ✅ Yes · **Phase:** 🟠 Production

`era_platform/evaluation/` is born here. This is the section that turns "it seems to work" into "here's the faithfulness score, the citation accuracy, and the cost per report, measured automatically on every run."

## Lectures

| # | Title | Duration |
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

## Files in this folder

```
09-observability-evaluation-langsmith/
├── README.md
├── exercise.py
└── solution.py          # becomes era_platform/evaluation/evaluators/*
```

## Where this code goes next

The evaluators built here wrap every agent call made by the API from Section 8. By Section 12 these run automatically on every capstone request.

# Exercise 2.E · Build a structured research summariser

**Section:** 2 · Development Environment & LLM Fundamentals
**Type:** Coding exercise · **Applies:** Lectures 2.4, 2.5, 2.6

---

## Learning objective

Turn a block of source text into a **structured, validated summary** using a
single LLM call that self-corrects when its output doesn't fit the contract. By
the end you'll have written the pattern every later agent in this course reuses:
*ask the model → validate against a Pydantic model → re-ask with the error if it
fails.*

## What "structured" means here

Not prettily formatted text. **Structured means a Pydantic model** — an object
your downstream code can rely on, with fields that are guaranteed to be present
and valid. The contract for this exercise is:

```python
class ResearchSummary(BaseModel):
    topic: str            # the main subject
    summary: str          # a 2-3 sentence abstract
    key_points: list[str] # the 3-5 most important takeaways (validated)
    entities: list[str]   # orgs / people / technologies named (may be empty)
```

The `key_points` bound (3–5 items) is deliberate: an LLM will occasionally
return two points or seven, and that raised `ValidationError` is exactly what
your self-correction loop catches and re-asks on. Without a validator that can
*fail*, there's nothing for 2.6's pattern to do.

## The "30 lines" is a design goal, not a rule

The title says "in 30 lines." Treat that as a **target that forces good
decisions**, not a limit anyone enforces. The reference implementation is a bit
longer than 30 once you add docstrings, logging, and explicit exception
handling — and that's the point. The *core logic* (build prompt → call → parse →
validate → retry) really is about 30 lines; everything else is the production
hygiene that makes it trustworthy. If your solution is 25 lines with no error
handling, or 200 lines with a class hierarchy, you've missed the target in
opposite directions. Aim for "as small as it can be while still being honest."

## Which provider?

**Gemini (Google AI Studio)** is the default — per `.env.example`, Gemini is the
course's synthesis/summarisation provider (Groq is reserved for routing and
classification). But note the design: the summariser depends only on a tiny
`LLMClient` protocol (`invoke(prompt) -> str`), so it is *provider-agnostic*. The
solution wires in Gemini; the tests wire in a fake. Swapping to Groq later
(lecture 2.8) is a one-line change with no edit to the summariser itself.

## Where the code lives

| Path | What it is |
|---|---|
| `starter/summariser.py` | Stubbed module with `TODO`s — **start here.** |
| `solution/summariser.py` | Runnable demo that drives the reference impl (real Gemini, with an offline fallback). |
| `era_platform/generation/summarizer.py` | The reference implementation, packaged so it's type-checked and importable by later sections. |
| `tests/unit/test_research_summariser.py` | The unit tests your starter must satisfy (repo-root `tests/`). |

> **Note on structure:** the reusable logic lives in the `era_platform` package
> (not duplicated in `solution/`) so it's covered by `mypy --strict` and the test
> suite. The `solution/` script shows how to *use* it. This is the pattern the
> rest of the course's exercises follow.

## Your task

1. Open `starter/summariser.py` and implement every `TODO`.
2. Make the tests pass:
   ```bash
   pytest tests/unit/test_research_summariser.py -v
   ```
   The tests drive your code with a **fake LLM** — no API key, no network, no
   spend. That's the payoff of coding against the `LLMClient` protocol.
3. When they're green, run the demo to see it against a (canned or real) model:
   ```bash
   python sections/02-dev-environment-and-llm-fundamentals/exercise-2E-research-summariser/solution/summariser.py
   ```
   With `GOOGLE_API_KEY` set in your `.env` it calls Gemini; without one it uses
   an offline canned response so you can still see the end-to-end shape.

## Acceptance criteria

- [ ] `ResearchSummary` has the four fields above with correct type hints.
- [ ] `key_points` rejects fewer than 3 or more than 5 items with a
      `ValidationError`.
- [ ] `SummarizerAgent.summarize()` returns a validated `ResearchSummary` on a
      well-formed response.
- [ ] On a `ValidationError`, it **re-asks the model with the error fed back in**,
      up to `max_retries` times (the 2.6 pattern).
- [ ] A failure of the LLM *call itself* is wrapped in `SummarizationError` and
      **not** retried (re-asking can't fix a broken connection).
- [ ] Empty input raises `SummarizationError` before any LLM call.
- [ ] Uses the standard `logging` module (not `print`) and full type hints.
- [ ] All tests in `tests/unit/test_research_summariser.py` pass.

## Concepts this applies

- **2.4 — Prompt engineering:** a system role plus explicit output-format
  instructions in the prompt.
- **2.5 — Structured outputs with Pydantic:** the model must return JSON that
  validates against `ResearchSummary`.
- **2.6 — Self-correcting outputs:** catch `ValidationError` and re-ask with the
  error message included in the follow-up prompt.

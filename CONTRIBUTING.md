# Contributing

This repo serves two audiences: students working through the course, and anyone fixing a bug or improving the shared `era_platform/` package. Both are welcome.

## If you're a student with a question about the material

Use [Discussions](../../discussions), not Issues. Questions about a lecture, confusion about an exercise, or "is this expected behaviour" belong there — Issues are reserved for actual bugs in the repo's code.

## If you found a bug in the code

1. Check [existing issues](../../issues) first — it may already be reported
2. Open a new issue using the `bug_report.md` template
3. Include: what you expected, what happened instead, and the minimal steps to reproduce

## If you want to submit a fix

```bash
# Fork, then:
git clone https://github.com/<your-username>/agentic-AI-engineering-course.git
cd agentic-AI-engineering-course
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

`pre-commit install` is a one-time step per clone — it wires up the `gitleaks`
secret scan defined in `.pre-commit-config.yaml` so a commit containing
anything key-shaped is blocked before it reaches git history.

Before opening a PR, all of these must pass:

```bash
ruff format .
ruff check .
mypy . --strict
pytest tests/unit/ tests/integration/
```

### Process

1. Branch from `main`: `git checkout -b fix/short-description` (or `feat/`, `docs/`)
2. Write or update tests for any code change — unit tests for pure logic, integration tests for agent behaviour
3. Confirm the full test suite passes
4. Open a PR against `main`. Describe **what** changed, **why**, and **how you tested it**
5. A maintainer will review within a few days

### Code style

- Python: [PEP 8](https://peps.python.org/pep-0008/) via `ruff`; type annotations required on all public functions (`mypy --strict`)
- Commits: [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- No secrets, credentials, or real document data in any committed file — `.env` is gitignored for a reason

### A note on section folders

If you're proposing a change to a `sections/XX-*/solution.py`, make sure it stays consistent with what the corresponding lecture teaches — these files are reference implementations students compare their own work against, not just working code. If your fix changes the approach being taught (not just fixes a bug), open a discussion first.

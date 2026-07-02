"""Code-execution tool — a safe(-ish) local Python sandbox (lecture 4.6).

Created: 2026-07-02
Last updated: 2026-07-02

Lecture 4.6 is "safe Python sandbox patterns", *not* "wire up a real sandbox
provider". The production ERA Platform runs untrusted code in an E2B Firecracker
micro-VM (see ``docs/ERA_Platform_SOW_v1.md`` §3.4 Quantitative Analyst Agent);
the zero-cost course substitute, per ``docs/production.md``, is a two-layer guard
built from the standard library only:

1. **A static AST safety check *before* execution.** The snippet is parsed and
   walked; imports, ``exec``/``eval``/``compile``/``__import__``, dunder attribute
   access (the usual sandbox-escape vector, e.g. ``().__class__.__bases__``), and a
   blocklist of dangerous names (``os``, ``subprocess``, ``socket``, ``open`` …)
   are rejected. Nothing that fails this check ever runs.
2. **Execution in a separate, short-lived subprocess** with a stripped-down
   ``__builtins__`` and a wall-clock timeout, so an infinite loop or a runaway
   allocation is bounded and cannot block the agent.

**This is a teaching sandbox, and the honest caveat belongs in the lecture: a
determined attacker can still find gaps in a blocklist-based, same-host guard.**
It is sufficient for a course demo where the "untrusted" code is the agent's own
generated arithmetic/data-wrangling — it is not a substitute for real OS-level
isolation, which is exactly why the production path uses E2B.
"""

from __future__ import annotations

import ast
import logging
import subprocess
import sys
from typing import Final

from era_platform.agents.tools.base import Tool, ToolError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 5

# Bare names the snippet may not reference. These are the usual routes to the
# filesystem, the network, other processes, and dynamic code loading.
DEFAULT_BLOCKED_NAMES: Final[frozenset[str]] = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "socket",
        "shutil",
        "pathlib",
        "open",
        "eval",
        "exec",
        "compile",
        "__import__",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "input",
        "breakpoint",
        "memoryview",
    }
)

# The only builtins the executed snippet is given. Small on purpose: enough for
# arithmetic, data shaping, and printing a result; nothing that touches the host.
_SAFE_BUILTIN_NAMES: Final[tuple[str, ...]] = (
    "abs",
    "all",
    "any",
    "bool",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "int",
    "len",
    "list",
    "map",
    "max",
    "min",
    "pow",
    "print",
    "range",
    "reversed",
    "round",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
    "zip",
)


class CodeSafetyError(ToolError):
    """Raised when a snippet fails the static AST safety check.

    A subclass of :class:`~era_platform.agents.tools.base.ToolError` so the agent
    treats it like any other tool failure — but distinct so callers (and tests)
    can tell "rejected before running" apart from "ran and failed".
    """


def assert_code_is_safe(
    code: str, *, blocked_names: frozenset[str] = DEFAULT_BLOCKED_NAMES
) -> None:
    """Statically reject a snippet that could escape the sandbox, before it runs.

    Parses ``code`` and walks its AST, raising :class:`CodeSafetyError` on the
    first violation found:

    * any ``import`` / ``from ... import`` statement,
    * any attribute access to a dunder (``__class__``, ``__globals__``, …),
    * any reference to a name in ``blocked_names``.

    Args:
        code: The Python source to vet.
        blocked_names: Bare names to forbid. Defaults to
            :data:`DEFAULT_BLOCKED_NAMES`.

    Raises:
        CodeSafetyError: If ``code`` does not parse, or contains a forbidden
            construct.
    """
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise CodeSafetyError(f"code does not parse: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise CodeSafetyError("imports are not allowed in the sandbox")
        if (
            isinstance(node, ast.Attribute)
            and node.attr.startswith("__")
            and node.attr.endswith("__")
        ):
            raise CodeSafetyError(f"dunder attribute access is not allowed: {node.attr!r}")
        if isinstance(node, ast.Name) and node.id in blocked_names:
            raise CodeSafetyError(f"use of blocked name is not allowed: {node.id!r}")


class CodeExecutionTool(Tool):
    """Run a short, self-contained Python snippet and return what it prints.

    The snippet is vetted by :func:`assert_code_is_safe`, then executed in a fresh
    subprocess with a restricted ``__builtins__`` and a wall-clock timeout. The
    tool's observation is the snippet's captured stdout (or the error, so the
    agent can react to a bug in its own code).
    """

    def __init__(self, *, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        """Build the code-execution tool.

        Args:
            timeout_seconds: Wall-clock limit for a single snippet. Must be
                positive.

        Raises:
            ValueError: If ``timeout_seconds`` is not positive.
        """
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        super().__init__(
            name="execute_python",
            description=(
                "Run a short, self-contained Python snippet to calculate or "
                "transform data. No imports, file, network, or OS access; print "
                "the result you want back."
            ),
            parameters={"code": "a self-contained Python snippet that prints its result"},
        )
        self._timeout = timeout_seconds

    def run(self, **kwargs: object) -> str:
        """Vet then execute ``code``, returning its stdout.

        Raises:
            CodeSafetyError: If ``code`` fails the static safety check.
            ToolError: If ``code`` is missing/blank, times out, or the subprocess
                cannot be run.
        """
        code = kwargs.get("code")
        if not isinstance(code, str) or not code.strip():
            raise ToolError("execute_python requires a non-empty 'code' string")

        assert_code_is_safe(code)  # raises CodeSafetyError; nothing unsafe runs
        return self._run_in_subprocess(code)

    def _run_in_subprocess(self, code: str) -> str:
        runner = self._build_runner(code)
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-c", runner],
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self._logger.warning("code execution timed out after %ss", self._timeout)
            raise ToolError(f"code execution timed out after {self._timeout}s") from exc
        except OSError as exc:  # pragma: no cover - environment-dependent
            raise ToolError(f"could not start the sandbox subprocess: {exc}") from exc

        if completed.returncode != 0:
            error = completed.stderr.strip() or "unknown error"
            self._logger.info("sandboxed code raised: %s", error)
            raise ToolError(f"code raised an error: {error}")

        output = completed.stdout.strip()
        self._logger.info("code executed cleanly (%d chars of output)", len(output))
        return output or "(the snippet produced no output; did you forget to print?)"

    @staticmethod
    def _build_runner(code: str) -> str:
        """Wrap ``code`` so the subprocess execs it with only the safe builtins.

        Runs under ``python -I`` (isolated: ignores env vars and the user site
        dir). The wrapper rebinds ``__builtins__`` to a whitelist before exec, so
        even though the AST check already ran in-process, the executing code has
        no second path to the dangerous builtins at runtime.
        """
        allowed = ", ".join(repr(name) for name in _SAFE_BUILTIN_NAMES)
        # ``code`` is embedded as a repr'd literal, never interpolated as source,
        # so it cannot break out of the wrapper's string.
        return (
            "import builtins as _b\n"
            f"_allowed = ({allowed},)\n"
            "_safe = {name: getattr(_b, name) for name in _allowed}\n"
            "_ns = {'__builtins__': _safe}\n"
            f"_source = {code!r}\n"
            "exec(compile(_source, '<sandbox>', 'exec'), _ns)\n"
        )

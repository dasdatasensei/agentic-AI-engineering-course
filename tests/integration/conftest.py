"""Integration-test configuration.

The integration suite is populated section by section as the course introduces
real external surfaces to test against (ChromaDB in Section 3, web search in
Section 4, the FastAPI service in Section 8, ...). Until then it is legitimately
empty: Section 2's summariser is pure dependency-injection and is already fully
covered by ``tests/unit`` with injected fakes — adding "integration" tests now
would only duplicate those.

pytest returns exit code 5 ("no tests collected") for an empty selection, which
CI treats as a failure. We remap *only* that code to success, so an empty
integration suite is green while genuine problems still fail the build:

    exit 5  -> no tests collected      -> treated as success (suite not ready yet)
    exit 1  -> tests ran and failed    -> still fails CI
    exit 2  -> collection/import error -> still fails CI

Once the first real integration test lands, collection is non-empty and this
hook becomes a no-op.
"""

from __future__ import annotations

import pytest

_NO_TESTS_COLLECTED = 5


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if exitstatus == _NO_TESTS_COLLECTED:
        session.exitstatus = 0

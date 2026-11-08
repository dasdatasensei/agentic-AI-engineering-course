"""Shared pytest configuration for the whole test suite.

Adds the ``--impl`` option, which lets exercise tests run against a learner's
starter file instead of the reference implementation in ``era_platform``.

Created: 2026-11-08
Last updated: 2026-11-08
"""

import pytest

from tests import exercise_impl


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the --impl option."""
    parser.addoption(
        "--impl",
        choices=exercise_impl.IMPL_CHOICES,
        default="reference",
        help=(
            "Which implementation exercise tests run against: 'reference' "
            "(era_platform, the default) or 'starter' (your exercise's starter file)."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Record the chosen implementation before test modules are imported."""
    exercise_impl.selected_impl = str(config.getoption("--impl"))

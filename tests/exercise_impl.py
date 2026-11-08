"""Choose which implementation an exercise's tests run against.

By default the tests exercise the reference implementation in ``era_platform``
(what CI checks). Learners run the same tests against their own starter file
with ``pytest <test file> --impl=starter``.

Created: 2026-11-08
Last updated: 2026-11-08
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parent.parent

IMPL_CHOICES = ("reference", "starter")

# Set from the --impl command-line option by tests/conftest.py.
selected_impl = "reference"


class StarterLoadError(ImportError):
    """Raised when a learner's starter file can't be found or imported."""


def load_exercise_module(reference: str, starter_path: str) -> ModuleType:
    """Return the module an exercise's tests should run against.

    Args:
        reference: Dotted import path of the reference implementation,
            e.g. ``"era_platform.generation.summarizer"``.
        starter_path: Path to the learner's starter file, relative to the
            repo root.

    Returns:
        The reference module, or the learner's starter module when pytest
        was run with ``--impl=starter``.

    Raises:
        StarterLoadError: If ``--impl=starter`` was given but the starter
            file can't be loaded.
    """
    if selected_impl == "reference":
        return importlib.import_module(reference)

    path = REPO_ROOT / starter_path
    if not path.is_file():
        raise StarterLoadError(f"Starter file not found: {path}")
    module_name = f"_starter_{path.parent.parent.name.replace('-', '_')}_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise StarterLoadError(f"Could not load starter file: {path}")
    module = importlib.util.module_from_spec(spec)
    # Registered before execution so Pydantic can resolve the module's annotations.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

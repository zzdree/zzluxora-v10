"""Run the whole ZZLUXORA test suite with every modal dialog neutralised.

Usage:
    cd <repo> && PYTHONPATH=<repo>/tools python3 tools/run_tests_guarded.py

Two runners are used because the suite is mixed:
  * unittest discovery covers tests/test_*.py written with unittest.TestCase
  * pytest covers the newer pytest-style modules (function-based tests)

The dialog guard is installed before anything imports the UI, so no QMessageBox,
QFileDialog or QInputDialog can appear on screen or block the run.
"""

from __future__ import annotations

import sys
import unittest

import _autodialog_guard  # noqa: F401  (installs the dialog stubs)

if not _autodialog_guard.GUARDED:
    print("warning: dialog guard could not be installed", file=sys.stderr)


def run_unittest_suite() -> bool:
    suite = unittest.TestLoader().discover("tests", pattern="test_*.py")
    return unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful()


def run_pytest_suite() -> bool:
    """Run pytest-style modules, if pytest is available.

    Only the modules written for pytest are listed, so the unittest-style
    modules are not executed twice.
    """
    pytest_modules = []
    from pathlib import Path

    for path in sorted(Path("tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "import pytest" in text:
            pytest_modules.append(str(path))

    if not pytest_modules:
        return True

    try:
        import pytest
    except ImportError:
        print("note: pytest not installed, skipping", pytest_modules, file=sys.stderr)
        return True

    return pytest.main(["-q", *pytest_modules]) == 0


def main() -> int:
    unittest_ok = run_unittest_suite()
    pytest_ok = run_pytest_suite()
    return 0 if (unittest_ok and pytest_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())

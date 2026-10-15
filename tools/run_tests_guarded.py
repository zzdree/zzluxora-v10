"""Run the ZZLUXORA test suite with every modal dialog neutralised.

Usage:
    cd <repo> && PYTHONPATH=<repo>/tools python3 tools/run_tests_guarded.py

The guard is imported before unittest discovery so no QMessageBox, QFileDialog
or QInputDialog can appear on screen or block the run.
"""

from __future__ import annotations

import sys
import unittest

import _autodialog_guard  # noqa: F401  (installs the dialog stubs)

if not _autodialog_guard.GUARDED:
    print("warning: dialog guard could not be installed", file=sys.stderr)


def main() -> int:
    suite = unittest.TestLoader().discover("tests", pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

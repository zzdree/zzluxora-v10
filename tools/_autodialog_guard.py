"""Neutralise every modal dialog before any UI module is imported.

Import this FIRST so that probes, audits and the test suite never block on a
popup and never steal focus from whoever is at the machine:

    PYTHONPATH=<repo>/tools:<repo> python3 -c "import _autodialog_guard; ..."

QMessageBox, QFileDialog and QInputDialog are replaced with non-blocking stubs.
The UI still runs its normal code path; only the visible dialog is suppressed,
so behaviour under test is unchanged apart from the missing window.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "*=false")

# Make the repository importable regardless of the current directory.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _install() -> bool:
    try:
        from ui.qt_compat import QFileDialog, QInputDialog, QMessageBox
    except Exception:
        return False  # UI stack unavailable; nothing to guard

    QMessageBox.information = staticmethod(lambda *a, **k: None)
    QMessageBox.warning = staticmethod(lambda *a, **k: None)
    QMessageBox.critical = staticmethod(lambda *a, **k: None)
    QMessageBox.about = staticmethod(lambda *a, **k: None)
    QMessageBox.question = staticmethod(
        lambda *a, **k: QMessageBox.StandardButton.No
    )
    QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: ("", ""))
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("", ""))
    QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: "")
    QInputDialog.getInt = staticmethod(lambda *a, **k: (0, False))
    QInputDialog.getText = staticmethod(lambda *a, **k: ("", False))
    QInputDialog.getItem = staticmethod(lambda *a, **k: ("", False))
    return True


GUARDED = _install()

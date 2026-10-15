"""Regression tests for Fixture Editor defects found in the 16 Oct 2026 audit.

Covers three reproduced defects:
  FE-01  cell widgets leaked on every channel-count change (24 grew to 264)
  FE-02  save dropped id/model/type, rewriting a shipped .zfx lossily
  FE-03  changing the channel count destroyed typed labels and types
"""

import json
from pathlib import Path

import pytest

from ui.qt_compat import HAS_QT, QApplication, QComboBox, QLineEdit

pytestmark = pytest.mark.skipif(not HAS_QT, reason="Qt binding unavailable")

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _label(win, row):
    widget = win.table.cellWidget(row, 1)
    return widget.text() if isinstance(widget, QLineEdit) else None


def _type(win, row):
    widget = win.table.cellWidget(row, 2)
    return widget.currentText() if isinstance(widget, QComboBox) else None


def test_channel_count_change_preserves_typed_labels(app):
    """FE-03: resizing must not revert labels the operator typed."""
    from ui.panels.fixture_editor import FixtureEditorWindow

    win = FixtureEditorWindow()
    win._populate_table_rows(8)
    win.table.cellWidget(0, 1).setText("HandTyped")
    win.table.cellWidget(1, 1).setText("MyGreen")
    win.table.cellWidget(2, 2).setCurrentText("Strobe")

    win._on_channel_count_changed(20)
    assert _label(win, 0) == "HandTyped", "growing must keep existing labels"
    assert _type(win, 2) == "Strobe", "growing must keep existing types"

    win._on_channel_count_changed(8)
    assert _label(win, 0) == "HandTyped", "shrinking back must keep existing labels"
    assert _label(win, 1) == "MyGreen"
    assert _type(win, 2) == "Strobe"


def test_new_rows_get_defaults_when_growing(app):
    """Only genuinely new rows should receive generated defaults."""
    from ui.panels.fixture_editor import FixtureEditorWindow

    win = FixtureEditorWindow()
    win._populate_table_rows(4)
    win.table.cellWidget(0, 1).setText("KeepMe")
    win._on_channel_count_changed(12)

    assert _label(win, 0) == "KeepMe"
    assert _label(win, 4) not in (None, ""), "new rows still get a default label"


def test_save_preserves_document_keys(app, tmp_path):
    """FE-02: saving an opened .zfx must not drop id/model/type."""
    from ui.panels.fixture_editor import FixtureEditorWindow

    source = REPO_ROOT / "fixtures" / "Alien-AL36.zfx"
    original = json.loads(source.read_text(encoding="utf-8"))

    win = FixtureEditorWindow()
    win._loaded_document = dict(original)
    win.txt_model.setText(original.get("name", ""))
    win.txt_maker.setText(original.get("manufacturer", ""))
    channels = original.get("channels", [])
    win.spin_channels.setValue(len(channels))
    win._populate_table_rows(len(channels))

    target = tmp_path / "roundtrip.zfx"
    win._write_file(str(target))
    saved = json.loads(target.read_text(encoding="utf-8"))

    for key in ("id", "model", "type"):
        assert key in saved, f"save must preserve '{key}'"
    assert set(original).issubset(set(saved)), "no original key may be dropped"
    assert saved["channel_count"] == original["channel_count"]


def test_new_fixture_still_gets_identity_fields(app, tmp_path):
    """A brand new fixture must still produce a complete document."""
    from ui.panels.fixture_editor import FixtureEditorWindow

    win = FixtureEditorWindow()
    win._on_new_fixture()
    win.txt_model.setText("My Custom PAR")
    win.txt_maker.setText("Generic")
    win._populate_table_rows(4)

    target = tmp_path / "new.zfx"
    win._write_file(str(target))
    saved = json.loads(target.read_text(encoding="utf-8"))

    assert saved["id"], "a new fixture needs an id"
    assert saved["model"] == "My Custom PAR"
    assert saved["type"]
    assert saved["channel_count"] == 4


def test_cell_widgets_do_not_leak_on_resize(app):
    """FE-01: the widget tree must stay proportional to the row count."""
    from ui.panels.fixture_editor import FixtureEditorWindow

    win = FixtureEditorWindow()
    win._populate_table_rows(8)
    baseline = (
        len(win.table.viewport().findChildren(QLineEdit))
        + len(win.table.viewport().findChildren(QComboBox))
    )

    for _ in range(6):
        win._populate_table_rows(4)
        win._populate_table_rows(16)

    after = (
        len(win.table.viewport().findChildren(QLineEdit))
        + len(win.table.viewport().findChildren(QComboBox))
    )
    # 16 rows -> 2 widgets per row, with a small margin.
    assert after <= 40, f"cell widgets leaked: {baseline} grew to {after}"

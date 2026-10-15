"""
fixture_editor.py | QLC+ Inspired Standalone Fixture Definition Editor Window
Provides an independent windowed tool with its own menubar (Open, Save, Save As)
for authoring and managing .zfx / .json fixture definitions.
"""

from __future__ import annotations
import json
import os
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
    QComboBox, QFileDialog, QMessageBox, QHeaderView,
    Qt, QAction, QKeySequence, QFont, QColor, QIcon
)
from core.paths import fixtures_dir as project_fixtures_dir
from ui.styles import Theme, CONSOLE_QSS


CHANNEL_TYPES = [
    "Dimmer",
    "Red",
    "Green",
    "Blue",
    "White",
    "Amber",
    "UV",
    "Cyan",
    "Magenta",
    "Yellow",
    "Strobe",
    "Shutter",
    "Pan",
    "Tilt",
    "Color Macro",
    "Gobo",
    "Prism",
    "Program",
    "Speed",
    "Effect",
    "Maintenance",
    "Empty",
]


class FixtureEditorWindow(QMainWindow if HAS_QT else object):
    """
    Standalone QLC+ inspired Fixture Definition Editor.
    Has its own independent menubar (Open, Save, Save As) and operates on .zfx / .json profiles.
    """
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Fixture Editor")
        self.resize(680, 560)
        self.setStyleSheet(CONSOLE_QSS)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_zz.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self.current_file_path: Path | None = None
        # The document as loaded from disk. _get_fixture_dict starts from this so
        # saving keeps every field the editor does not manage (id, model, type,
        # and any future key) instead of dropping them.
        self._loaded_document: dict | None = None
        # Bottom bar carrying the document's changed/unchanged statement and the
        # discard action. Built before the menu so the menu actions can drive it.
        self._build_status_bar()
        self._init_menu_bar()
        self._init_ui()
        self._mark_clean()
        self._connect_dirty_signals()

    def _init_menu_bar(self) -> None:
        mb = self.menuBar()
        menu_file = mb.addMenu("File")

        act_new = QAction("New Fixture", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self._on_new_fixture)
        menu_file.addAction(act_new)

        act_open = QAction("Open Fixture", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._on_open_file)
        menu_file.addAction(act_open)

        menu_file.addSeparator()

        act_save = QAction("Save Fixture", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._on_save_file)
        menu_file.addAction(act_save)

        act_save_as = QAction("Save As Fixture", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._on_save_as_file)
        menu_file.addAction(act_save_as)

        menu_file.addSeparator()

        act_close = QAction("Close", self)
        act_close.setShortcut(QKeySequence("Alt+F5"))
        act_close.triggered.connect(self.close)
        menu_file.addAction(act_close)

    def _build_status_bar(self) -> None:
        """Document state text plus the discard action, in a native status bar.

        The editor kept no record of whether it had been changed, and it is a
        reused instance: closing it and reopening it from Fixture > Fixture
        Editor brought back the previous document, its path, and its edits, so a
        later Ctrl+S pressed for an unrelated reason rewrote the file the
        operator had never reopened.
        """
        self.lbl_state = QLabel("NEW")
        self.lbl_state.setStyleSheet(
            f"color: {Theme.TEXT_SECONDARY}; font-family: monospace; font-weight: 700;"
        )
        self.btn_discard = QPushButton("Discard Changes")
        self.btn_discard.setStyleSheet("min-width: 110px; padding: 2px 10px; border-radius: 3px;")
        self.btn_discard.clicked.connect(self._on_discard_changes)
        self.statusBar().addWidget(self.lbl_state)
        self.statusBar().addPermanentWidget(self.btn_discard)

    def _connect_dirty_signals(self) -> None:
        """Mark the document changed on every edit the editor owns.

        Each row's label field and type combo is new on every repopulate, so the
        wiring is re-applied from _populate_table_rows after the rows exist.
        """
        self.txt_model.textEdited.connect(self._mark_dirty)
        self.txt_maker.textEdited.connect(self._mark_dirty)
        self.spin_channels.valueChanged.connect(self._mark_dirty)
        self._connect_row_signals()

    def _connect_row_signals(self) -> None:
        for row in range(self.table.rowCount()):
            edit = self.table.cellWidget(row, 1)
            combo = self.table.cellWidget(row, 2)
            if isinstance(edit, QLineEdit):
                edit.textEdited.connect(self._mark_dirty)
            if isinstance(combo, QComboBox):
                combo.currentTextChanged.connect(self._mark_dirty)

    def _mark_dirty(self, *_args) -> None:
        self.modified = True
        self._refresh_modified_state()

    def _mark_clean(self, *_args) -> None:
        self.modified = False
        self._refresh_modified_state()

    def _refresh_modified_state(self) -> None:
        if self.modified:
            self.lbl_state.setText("MODIFIED, NOT SAVED")
            self.lbl_state.setStyleSheet(
                f"color: {Theme.ACCENT_AMBER}; font-family: monospace; font-weight: 700;"
            )
            self.btn_discard.setEnabled(True)
        else:
            self.lbl_state.setText(
                "SAVED" if self.current_file_path and not self._is_new_document() else "NEW"
            )
            self.lbl_state.setStyleSheet(
                f"color: {Theme.TEXT_SECONDARY}; font-family: monospace; font-weight: 700;"
            )
            self.btn_discard.setEnabled(False)

    def _is_new_document(self) -> bool:
        """A document that was never opened from disk and carries no editor text."""
        if self._loaded_document is not None:
            return False
        if self.current_file_path is not None:
            return False
        return not self.txt_model.text().strip()

    def _confirm_discard(self, reason: str) -> bool:
        """True when the operator agrees to throw the unsaved edits away."""
        reply = QMessageBox.question(
            self,
            "Unsaved Fixture Changes",
            f"{reason}\n\n"
            f"'{self.txt_model.text().strip() or 'this fixture'}' has unsaved changes.\n"
            "Close the editor and discard them?",
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return reply == QMessageBox.StandardButton.Discard

    def _on_discard_changes(self) -> None:
        """Throw the edits away and restore the document that is actually on disk."""
        if self._loaded_document is not None:
            self._apply_document(self._loaded_document, self.current_file_path)
        else:
            self._reset_document()
        self._mark_clean()

    def closeEvent(self, event) -> None:
        """Never let a hidden window carry unsaved edits back from the dead.

        Closing used to leave the edits, the loaded document, and the file path
        in place; the same instance is reused by Fixture > Fixture Editor, so
        reopening it restored the discarded document and a later Ctrl+S rewrote
        the file unasked. The window still hides instead of being destroyed, so
        the reopening stays instant, but the document is made clean first.
        """
        if self.modified and self.isVisible():
            if not self._confirm_discard("Closing the editor discards the edits."):
                event.ignore()
                return
        if self._loaded_document is not None:
            self._apply_document(self._loaded_document, self.current_file_path)
        else:
            self._reset_document()
        self._mark_clean()
        super().closeEvent(event)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # Form Model, Manufacture, Channel (No decorative box title)
        form_layout = QHBoxLayout()
        form_layout.setSpacing(12)

        lbl_model = QLabel("Model:")
        lbl_model.setStyleSheet(f"font-weight: 700; color: {Theme.TEXT_SECONDARY};")
        self.txt_model = QLineEdit("")
        self.txt_model.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; border: 1px solid {Theme.BORDER_STRONG}; color: {Theme.TEXT_PRIMARY}; border-radius: 3px; padding: 4px;")
        form_layout.addWidget(lbl_model)
        form_layout.addWidget(self.txt_model, 2)

        lbl_maker = QLabel("Manufacture:")
        lbl_maker.setStyleSheet(f"font-weight: 700; color: {Theme.TEXT_SECONDARY};")
        self.txt_maker = QLineEdit("")
        self.txt_maker.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; border: 1px solid {Theme.BORDER_STRONG}; color: {Theme.TEXT_PRIMARY}; border-radius: 3px; padding: 4px;")
        form_layout.addWidget(lbl_maker)
        form_layout.addWidget(self.txt_maker, 2)

        lbl_ch = QLabel("Channel:")
        lbl_ch.setStyleSheet(f"font-weight: 700; color: {Theme.TEXT_SECONDARY};")
        self.spin_channels = QSpinBox()
        self.spin_channels.setRange(1, 512)
        self.spin_channels.setValue(4)
        self.spin_channels.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; border: 1px solid {Theme.BORDER_STRONG}; color: {Theme.TEXT_PRIMARY}; border-radius: 3px; padding: 4px;")
        self.spin_channels.valueChanged.connect(self._on_channel_count_changed)
        form_layout.addWidget(lbl_ch)
        form_layout.addWidget(self.spin_channels, 1)

        main_layout.addLayout(form_layout)

        # Channel Mapping Table (Directly displayed without groupbox header)
        self.table = QTableWidget(4, 3)
        self.table.setHorizontalHeaderLabels(["Channel", "Label", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                gridline-color: {Theme.BORDER_SUBTLE};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_ELEVATED};
                color: {Theme.TEXT_PRIMARY};
                font-weight: 700;
                padding: 6px;
                border: 1px solid {Theme.BORDER_SUBTLE};
            }}
        """)
        main_layout.addWidget(self.table, 1)

        # Bottom Action Bar: Save and Close only
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet(f"background-color: {Theme.COLOR_SUCCESS}; color: {Theme.BG_ROOT}; font-weight: bold; min-width: 90px; padding: 6px 14px; border-radius: 4px; border: none;")
        self.btn_save.clicked.connect(self._on_save_file)
        btn_bar.addWidget(self.btn_save)

        self.btn_close = QPushButton("Close")
        self.btn_close.setStyleSheet("min-width: 90px; padding: 6px 14px; border-radius: 4px;")
        self.btn_close.clicked.connect(self.close)
        btn_bar.addWidget(self.btn_close)

        main_layout.addLayout(btn_bar)

        self._populate_table_rows(4)

    def _populate_table_rows(self, count: int, preserve: bool = False) -> None:
        """Fill the channel table with `count` rows.

        preserve=True carries over the label and type the operator has already
        entered for the first min(old, new) rows, and only generates defaults
        for genuinely new rows. Without this, changing the channel count wiped
        every typed label and reverted each type to a name-derived guess.

        Cell widgets of discarded rows are removed explicitly. setRowCount()
        alone orphans them, and the editor leaked without bound (24 cell widgets
        grew to 264 over a dozen count changes).
        """
        previous = self._read_rows() if preserve else []

        # Release the cell widgets explicitly. setRowCount()/clearContents()
        # only drop the model data; the QLineEdit and QComboBox stay parented to
        # the viewport and accumulate, so the editor leaked without bound
        # (24 cell widgets grew to 264 over a dozen channel-count changes).
        for row in range(self.table.rowCount()):
            for column in (1, 2):
                widget = self.table.cellWidget(row, column)
                if widget is not None:
                    self.table.removeCellWidget(row, column)
                    widget.setParent(None)
                    widget.deleteLater()
        self.table.clearContents()
        self.table.setRowCount(count)
        default_names = ["Red", "Green", "Blue", "White", "Dimmer", "Strobe", "Amber", "Macro"]

        for i in range(count):
            item_no = QTableWidgetItem(f"{i+1:02d}")
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setFlags(Qt.ItemIsEnabled)
            item_no.setForeground(QColor(Theme.TEXT_SECONDARY))
            item_no.setFont(QFont("monospace", 10, QFont.Bold))
            self.table.setItem(i, 0, item_no)

            if i < len(previous):
                init_label = previous[i]["label"]
                init_type = previous[i]["type"]
            else:
                init_label = default_names[i] if i < len(default_names) else f"Channel {i+1}"
                init_type = "Empty"
                for t in CHANNEL_TYPES:
                    if t.lower() in init_label.lower():
                        init_type = t
                        break

            edit_label = QLineEdit(init_label)
            edit_label.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_SUBTLE}; padding: 3px;")
            self.table.setCellWidget(i, 1, edit_label)

            combo = QComboBox()
            combo.addItems(CHANNEL_TYPES)
            combo.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_SUBTLE}; padding: 3px;")
            combo.setCurrentText(init_type if init_type in CHANNEL_TYPES else "Empty")
            self.table.setCellWidget(i, 2, combo)

        # The row widgets were just recreated, so their dirty wiring goes with them.
        self._connect_row_signals()

    @staticmethod
    def _describe_document_problem(data: object) -> str:
        """Return a human-readable reason the document cannot be edited, or "".

        Kept separate from loading so both the open path and any future caller
        apply the same rules, and so the reason can be shown verbatim.
        """
        if not isinstance(data, dict):
            return "the file does not contain a JSON object"
        if data.get("app") not in (None, "ZZLUXORA") and "channels" not in data:
            return "the file is not a ZZLUXORA fixture profile"
        channels = data.get("channels")
        if channels is None:
            return "the file has no 'channels' list"
        if not isinstance(channels, list):
            return "'channels' is not a list"
        if len(channels) == 0:
            return "the file declares 0 channels"
        for index, channel in enumerate(channels, start=1):
            if not isinstance(channel, dict):
                return f"channel {index} is not an object"
            if "type" not in channel:
                return f"channel {index} has no 'type'"
        declared = data.get("channel_count")
        if declared is not None and declared != len(channels):
            return (f"'channel_count' says {declared} but the file lists "
                    f"{len(channels)} channels")
        return ""

    def _read_rows(self) -> list[dict]:
        """Current label/type of every populated row, in order."""
        rows: list[dict] = []
        for i in range(self.table.rowCount()):
            edit = self.table.cellWidget(i, 1)
            combo = self.table.cellWidget(i, 2)
            if edit is None and combo is None:
                continue
            rows.append({
                "label": edit.text() if isinstance(edit, QLineEdit) else "",
                "type": combo.currentText() if isinstance(combo, QComboBox) else "",
            })
        return rows

    def _on_channel_count_changed(self, new_count: int) -> None:
        if new_count == self.table.rowCount():
            return
        # Preserve what the operator already typed; only new rows get defaults.
        self._populate_table_rows(new_count, preserve=True)

    def _get_fixture_dict(self) -> dict:
        ch_list = []
        for i in range(self.table.rowCount()):
            edit = self.table.cellWidget(i, 1)
            combo = self.table.cellWidget(i, 2)
            label = edit.text().strip() if isinstance(edit, QLineEdit) else f"Ch {i+1}"
            ctype = combo.currentText().lower() if isinstance(combo, QComboBox) else "dimmer"
            ch_list.append({
                "index": i + 1,
                "label": label,
                "type": ctype,
                "default_value": 255 if ctype == "dimmer" else 0,
            })

        # Start from the document that was opened and overwrite only the fields
        # this editor owns. Rebuilding the dict from scratch dropped id, model
        # and type, so opening a shipped .zfx and saving it rewrote the file in
        # a schema the fixture tests and the fixture list no longer recognised.
        document = dict(self._loaded_document) if self._loaded_document else {}
        name = self.txt_model.text().strip()
        document.update({
            "name": name,
            "manufacturer": self.txt_maker.text().strip(),
            "channel_count": len(ch_list),
            "channels": ch_list,
        })
        # Back-fill identity fields that the file format expects.
        document.setdefault("id", name or "custom_fixture")
        document.setdefault("model", name)
        document.setdefault("type", "Color Changer")
        return document

    def _reset_document(self) -> None:
        """Return the editor to the empty 4-channel start state."""
        self.current_file_path = None
        self._loaded_document = None
        self.txt_model.setText("")
        self.txt_maker.setText("")
        self.spin_channels.setValue(4)
        self._populate_table_rows(4)
        self.setWindowTitle("Fixture Editor")

    def _apply_document(self, data: dict, path: Path | None) -> None:
        """Populate the form from a parsed fixture document.

        Shared by New, Open and Discard so all three land in exactly the same
        state, and so a reused window can never show a mix of two documents.
        """
        self._loaded_document = data
        self.current_file_path = Path(path) if path else None
        self.txt_model.setText(data.get("name", Path(path).stem if path else ""))
        self.txt_maker.setText(data.get("manufacturer", "Generic"))

        channels = data.get("channels", [])
        self.spin_channels.setValue(max(1, len(channels)))
        self._populate_table_rows(max(1, len(channels)))
        for i, ch in enumerate(channels):
            edit = self.table.cellWidget(i, 1)
            combo = self.table.cellWidget(i, 2)
            if isinstance(edit, QLineEdit):
                edit.setText(ch.get("label", ""))
            if isinstance(combo, QComboBox):
                declared = str(ch.get("type", "")).lower()
                matched = next((t for t in CHANNEL_TYPES if t.lower() == declared), None)
                combo.setCurrentText(matched or "Empty")

        self.setWindowTitle(
            f"Fixture Editor [{self.current_file_path.name}]"
            if self.current_file_path else "Fixture Editor"
        )

    def _on_new_fixture(self) -> None:
        self._reset_document()
        self._mark_clean()

    def _on_open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Fixture Profile",
            str(project_fixtures_dir()),
            "ZZLUXORA Fixture (*.zfx)",
        )
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            # Validate before touching the editor. Loading a structurally broken
            # file used to populate the form anyway and then silently rewrite it
            # on save, and a 0-channel file was clamped to 1 channel by the spin
            # box minimum, so the editor invented a channel the file never had.
            problem = self._describe_document_problem(data)
            if problem:
                QMessageBox.warning(
                    self,
                    "Invalid Fixture Profile",
                    f"{Path(path).name} was not opened: {problem}\n\n"
                    "A fixture needs at least one channel, each with a label and a type.",
                )
                return

            self._apply_document(data, Path(path))
            self._mark_clean()
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Failed to open fixture profile:\n{e}")

    def _on_save_file(self) -> None:
        if self.current_file_path:
            self._write_file(self.current_file_path)
        else:
            self._on_save_as_file()

    def _on_save_as_file(self) -> None:
        default_dir = project_fixtures_dir()
        default_dir.mkdir(parents=True, exist_ok=True)
        model_name = self.txt_model.text().strip() or "new_fixture"
        default_name = f"{model_name.lower().replace(' ', '_')}.zfx"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Fixture Profile",
            str(default_dir / default_name),
            "ZZLUXORA Fixture (*.zfx)",
        )
        if path:
            if not path.endswith(".zfx"):
                path += ".zfx"
            self._write_file(Path(path))

    def _write_file(self, target_path: Path) -> None:
        """Write the fixture profile, atomically.

        The previous implementation opened the destination directly, so an error
        part-way through truncated an existing profile to a partial file. The
        document is now written to a temporary sibling and moved into place,
        which is atomic on the same filesystem.
        """
        try:
            data = self._get_fixture_dict()

            name = str(data.get("name", "")).strip()
            if not name:
                QMessageBox.warning(
                    self, "Missing Name",
                    "Give the fixture a model name before saving.",
                )
                return
            if any(sep in name for sep in ("/", "\\")) or name in (".", ".."):
                QMessageBox.warning(
                    self, "Invalid Name",
                    "The model name cannot contain path separators ('/' or '\\') "
                    "or be '.' or '..'.",
                )
                return

            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = target_path.with_name(target_path.name + ".tmp")
            with open(temporary, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
                fp.flush()
                os.fsync(fp.fileno())
            os.replace(temporary, target_path)

            self.current_file_path = target_path
            self.setWindowTitle(f"Fixture Editor [{target_path.name}]")
            self._mark_clean()
            QMessageBox.information(self, "Saved", f"Fixture profile successfully saved to:\n{target_path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save fixture profile:\n{e}")

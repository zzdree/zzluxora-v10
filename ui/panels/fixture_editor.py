"""
fixture_editor.py | QLC+ Inspired Standalone Fixture Definition Editor Window
Provides an independent windowed tool with its own menubar (Open, Save, Save As)
for authoring and managing .zfx / .json fixture definitions.
"""

from __future__ import annotations
import json
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
    QComboBox, QFileDialog, QMessageBox, QHeaderView,
    Qt, QAction, QKeySequence, QFont, QColor, QIcon
)
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
        self._init_menu_bar()
        self._init_ui()

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

    def _populate_table_rows(self, count: int) -> None:
        self.table.setRowCount(count)
        default_names = ["Red", "Green", "Blue", "White", "Dimmer", "Strobe", "Amber", "Macro"]
        for i in range(count):
            item_no = QTableWidgetItem(f"{i+1:02d}")
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setFlags(Qt.ItemIsEnabled)
            item_no.setForeground(QColor(Theme.TEXT_SECONDARY))
            item_no.setFont(QFont("monospace", 10, QFont.Bold))
            self.table.setItem(i, 0, item_no)

            init_label = default_names[i] if i < len(default_names) else f"Channel {i+1}"
            edit_label = QLineEdit(init_label)
            edit_label.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_SUBTLE}; padding: 3px;")
            self.table.setCellWidget(i, 1, edit_label)

            combo = QComboBox()
            combo.addItems(CHANNEL_TYPES)
            combo.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_SUBTLE}; padding: 3px;")
            matched = "Empty"
            for t in CHANNEL_TYPES:
                if t.lower() in init_label.lower():
                    matched = t
                    break
            combo.setCurrentText(matched)
            self.table.setCellWidget(i, 2, combo)

    def _on_channel_count_changed(self, new_count: int) -> None:
        old_count = self.table.rowCount()
        if new_count == old_count: return
        self._populate_table_rows(new_count)

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

        return {
            "name": self.txt_model.text().strip(),
            "manufacturer": self.txt_maker.text().strip(),
            "channel_count": len(ch_list),
            "channels": ch_list,
        }

    def _on_new_fixture(self) -> None:
        self.current_file_path = None
        self.txt_model.setText("")
        self.txt_maker.setText("")
        self.spin_channels.setValue(4)
        self._populate_table_rows(4)
        self.setWindowTitle("Fixture Editor")

    def _on_open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Fixture Profile",
            str(Path.home() / "ANDREAS" / "zzluxora_v10" / "fixtures"),
            "ZZLUXORA Fixture (*.zfx)",
        )
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                self.txt_model.setText(data.get("name", Path(path).stem))
                self.txt_maker.setText(data.get("manufacturer", "Generic"))
                channels = data.get("channels", [])
                self.spin_channels.setValue(len(channels))
                self._populate_table_rows(len(channels))

                for i, ch in enumerate(channels):
                    edit = self.table.cellWidget(i, 1)
                    combo = self.table.cellWidget(i, 2)
                    if isinstance(edit, QLineEdit): edit.setText(ch.get("label", ""))
                    if isinstance(combo, QComboBox):
                        t = ch.get("type", "dimmer").title()
                        if t in CHANNEL_TYPES:
                            combo.setCurrentText(t)
                        else:
                            for ct in CHANNEL_TYPES:
                                if ct.lower() == ch.get("type", "").lower():
                                    combo.setCurrentText(ct)
                                    break

                self.current_file_path = Path(path)
                self.setWindowTitle(f"Fixture Editor [{self.current_file_path.name}]")
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Failed to open fixture profile:\n{e}")

    def _on_save_file(self) -> None:
        if self.current_file_path:
            self._write_file(self.current_file_path)
        else:
            self._on_save_as_file()

    def _on_save_as_file(self) -> None:
        default_dir = Path.home() / "ANDREAS" / "zzluxora_v10" / "fixtures"
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
        try:
            data = self._get_fixture_dict()
            with open(target_path, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
            self.current_file_path = target_path
            self.setWindowTitle(f"Fixture Editor [{target_path.name}]")
            QMessageBox.information(self, "Saved", f"Fixture profile successfully saved to:\n{target_path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save fixture profile:\n{e}")

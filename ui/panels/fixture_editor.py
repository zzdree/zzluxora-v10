"""
fixture_editor.py — QLC+ Inspired Standalone Fixture Definition Editor Window
Provides an independent windowed tool with its own menubar (Open, Save, Save As)
for authoring and managing .zfx / .json fixture definitions.
"""

from __future__ import annotations
import json
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
    QComboBox, QFileDialog, QMessageBox, QGroupBox, QHeaderView, QMenuBar, QMenu,
    Qt, QAction, QKeySequence, QFont
)
from ui.styles import Theme, CONSOLE_QSS


CHANNEL_TYPES = [
    "Dimmer",
    "Red",
    "Green",
    "Blue",
    "White",
    "Amber",
    "Strobe",
    "Pan",
    "Tilt",
    "Color Macro",
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
        self.setWindowTitle("Fixture Definition Editor — ZZLUXORA")
        self.resize(680, 560)
        self.setStyleSheet(CONSOLE_QSS)

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

        act_open = QAction("Open Fixture...", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._on_open_file)
        menu_file.addAction(act_open)

        menu_file.addSeparator()

        act_save = QAction("Save Fixture", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._on_save_file)
        menu_file.addAction(act_save)

        act_save_as = QAction("Save As...", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._on_save_as_file)
        menu_file.addAction(act_save_as)

        menu_file.addSeparator()
        act_close = QAction("Close Editor", self)
        act_close.triggered.connect(self.close)
        menu_file.addAction(act_close)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # Top Header Form
        form_group = QGroupBox("Spesifikasi Model & Pabrikan Lampu")
        form_group.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        form_layout = QGridLayout(form_group)
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Nama Model:"), 0, 0)
        self.txt_model = QLineEdit("Generic PAR LED RGBW 4CH")
        form_layout.addWidget(self.txt_model, 0, 1)

        form_layout.addWidget(QLabel("Manufaktur:"), 0, 2)
        self.txt_maker = QLineEdit("Generic")
        form_layout.addWidget(self.txt_maker, 0, 3)

        form_layout.addWidget(QLabel("Jumlah Kanal DMX:"), 1, 0)
        self.spin_channels = QSpinBox()
        self.spin_channels.setRange(1, 64)
        self.spin_channels.setValue(4)
        self.spin_channels.valueChanged.connect(self._on_channel_count_changed)
        form_layout.addWidget(self.spin_channels, 1, 1)

        main_layout.addWidget(form_group)

        # Channel Mapping Table
        tbl_box = QGroupBox("Tabel Pemetaan Kanal DMX (Channel Footprint)")
        tbl_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        tbl_layout = QVBoxLayout(tbl_box)

        self.table = QTableWidget(4, 3)
        self.table.setHorizontalHeaderLabels(["Kanal", "Label / Deskripsi", "Tipe Fungsi"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        tbl_layout.addWidget(self.table)

        main_layout.addWidget(tbl_box, 1)

        # Bottom Action Bar
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.btn_save = QPushButton("SAVE FIXTURE (.zfx)")
        self.btn_save.setStyleSheet(f"background-color: #1e3a5f; border-color: {Theme.ACCENT_CYAN}; font-weight: bold;")
        self.btn_save.clicked.connect(self._on_save_file)
        btn_bar.addWidget(self.btn_save)

        self.btn_close = QPushButton("CLOSE")
        self.btn_close.clicked.connect(self.close)
        btn_bar.addWidget(self.btn_close)

        main_layout.addLayout(btn_bar)

        self._populate_table_rows(4)

    def _populate_table_rows(self, count: int) -> None:
        self.table.setRowCount(count)
        default_names = ["Red", "Green", "Blue", "White", "Dimmer", "Strobe", "Amber", "Macro"]
        for i in range(count):
            item_no = QTableWidgetItem(f"Ch {i+1:02d}")
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setFlags(Qt.ItemIsEnabled)
            item_no.setForeground(Theme.TEXT_SECONDARY)
            self.table.setItem(i, 0, item_no)

            init_label = default_names[i] if i < len(default_names) else f"Channel {i+1}"
            edit_label = QLineEdit(init_label)
            self.table.setCellWidget(i, 1, edit_label)

            combo = QComboBox()
            combo.addItems(CHANNEL_TYPES)
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
        self.txt_model.setText("New PAR LED RGBW")
        self.txt_maker.setText("Generic")
        self.spin_channels.setValue(4)
        self.setWindowTitle("Fixture Definition Editor — [New Fixture]")

    def _on_open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Buka Berkas Profil Fixture",
            str(Path.home() / "ANDREAS" / "zzluxora_v10" / "fixtures"),
            "ZZLUXORA Fixtures (*.zfx *.json);;All Files (*.*)",
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
                        # capitalize
                        t = ch.get("type", "dimmer").capitalize()
                        if t in CHANNEL_TYPES: combo.setCurrentText(t)

                self.current_file_path = Path(path)
                self.setWindowTitle(f"Fixture Definition Editor — [{self.current_file_path.name}]")
        except Exception as e:
            QMessageBox.critical(self, "Error Buka Berkas", f"Gagal membaca profil fixture:\n{e}")

    def _on_save_file(self) -> None:
        if self.current_file_path:
            self._write_file(self.current_file_path)
        else:
            self._on_save_as_file()

    def _on_save_as_file(self) -> None:
        default_dir = Path.home() / "ANDREAS" / "zzluxora_v10" / "fixtures"
        default_dir.mkdir(parents=True, exist_ok=True)
        default_name = f"{self.txt_model.text().lower().replace(' ', '_')}.zfx"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Profil Fixture",
            str(default_dir / default_name),
            "ZZLUXORA Fixture (*.zfx);;JSON Fixture (*.json)",
        )
        if path:
            self._write_file(Path(path))

    def _write_file(self, target_path: Path) -> None:
        try:
            data = self._get_fixture_dict()
            with open(target_path, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
            self.current_file_path = target_path
            self.setWindowTitle(f"Fixture Definition Editor — [{target_path.name}]")
            QMessageBox.information(self, "Berhasil Disimpan", f"Profil fixture berhasil disimpan ke:\n{target_path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Error Simpan", f"Gagal menyimpan profil fixture:\n{e}")

"""
fixture_editor.py — Fixture Profile JSON Editor Panel
Enables operators to define, customize, and save multi-channel DMX fixture profiles (RGBW, Dimmer, Strobe).
"""

import json
try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
        QComboBox, QFileDialog, QMessageBox, QGroupBox, QHeaderView
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

class FixtureEditor(QWidget):
    """Fixture Profile Creator and Editor."""
    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Title
        title_box = QVBoxLayout()
        title = QLabel("DMX FIXTURE PROFILE EDITOR")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        desc = QLabel("Penyunting profil lampu DMX512 (RGBW, Dimmer, Strobe) ke berkas definisi .json.")
        desc.setStyleSheet("color: #abb2bf; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        main_layout.addLayout(title_box)

        # Form Metadata
        form_group = QGroupBox("Spesifikasi Fixture Lampu")
        form_layout = QHBoxLayout(form_group)

        form_layout.addWidget(QLabel("Nama Fixture:"))
        self.txt_name = QLineEdit("Generic PAR LED RGBW 4CH")
        form_layout.addWidget(self.txt_name)

        form_layout.addWidget(QLabel("Manufaktur:"))
        self.txt_maker = QLineEdit("Generic")
        form_layout.addWidget(self.txt_maker)

        form_layout.addWidget(QLabel("Jumlah Kanal:"))
        self.spin_channels = QSpinBox()
        self.spin_channels.setRange(1, 64)
        self.spin_channels.setValue(4)
        self.spin_channels.valueChanged.connect(self._on_channel_count_changed)
        form_layout.addWidget(self.spin_channels)

        main_layout.addWidget(form_group)

        # Channel mapping table
        self.table = QTableWidget(4, 3)
        self.table.setHorizontalHeaderLabels(["No. Kanal", "Nama / Label", "Tipe Kanal"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        default_types = ["Red", "Green", "Blue", "White"]
        for i in range(4):
            item_no = QTableWidgetItem(f"Kanal {i+1}")
            item_no.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, item_no)

            item_label = QLineEdit(default_types[i])
            self.table.setCellWidget(i, 1, item_label)

            combo_type = QComboBox()
            combo_type.addItems(["Dimmer", "Red", "Green", "Blue", "White", "Amber", "Strobe", "Pan", "Tilt", "Empty"])
            combo_type.setCurrentText(default_types[i])
            self.table.setCellWidget(i, 2, combo_type)

        main_layout.addWidget(self.table)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_open = QPushButton("Buka Profil (.json)")
        self.btn_open.clicked.connect(self._on_open_json)
        btn_layout.addWidget(self.btn_open)

        self.btn_save = QPushButton("Simpan Profil Fixture")
        self.btn_save.setStyleSheet("background-color: #0b3d36; border-color: #00e5ff; color: #00e5ff; font-weight: bold;")
        self.btn_save.clicked.connect(self._on_save_json)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

    def _on_channel_count_changed(self, count: int):
        self.table.setRowCount(count)
        types = ["Dimmer", "Red", "Green", "Blue", "White", "Amber", "Strobe", "Empty"]
        for i in range(count):
            if not self.table.item(i, 0):
                item_no = QTableWidgetItem(f"Kanal {i+1}")
                item_no.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 0, item_no)
            if not self.table.cellWidget(i, 1):
                self.table.setCellWidget(i, 1, QLineEdit(f"Channel {i+1}"))
            if not self.table.cellWidget(i, 2):
                combo = QComboBox()
                combo.addItems(types)
                self.table.setCellWidget(i, 2, combo)

    def _on_open_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Buka Fixture JSON", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.txt_name.setText(data.get("name", ""))
            self.txt_maker.setText(data.get("manufacturer", ""))
            channels = data.get("channels", [])
            self.spin_channels.setValue(len(channels))
            for i, ch in enumerate(channels):
                widget_label = self.table.cellWidget(i, 1)
                widget_type = self.table.cellWidget(i, 2)
                if widget_label: widget_label.setText(ch.get("label", ""))
                if widget_type: widget_type.setCurrentText(ch.get("type", "Dimmer"))

    def _on_save_json(self):
        data = {
            "name": self.txt_name.text(),
            "manufacturer": self.txt_maker.text(),
            "channels": []
        }
        for i in range(self.table.rowCount()):
            lbl = self.table.cellWidget(i, 1).text() if self.table.cellWidget(i, 1) else f"CH {i+1}"
            ctype = self.table.cellWidget(i, 2).currentText() if self.table.cellWidget(i, 2) else "Dimmer"
            data["channels"].append({"channel": i+1, "label": lbl, "type": ctype})

        file_path, _ = QFileDialog.getSaveFileName(self, "Simpan Fixture JSON", f"{self.txt_name.text().lower().replace(' ', '_')}.json", "JSON Files (*.json)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Disimpan", f"Profil fixture tersimpan di {file_path}")

"""
help_panel.py — Application Help & Keyboard Shortcuts Reference Dialog
Displays the comprehensive console shortcuts table and live operational instructions.
"""

from __future__ import annotations

from ui.qt_compat import (
    HAS_QT, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, Qt, QColor, QFont
)
from ui.styles import Theme, CONSOLE_QSS


class HelpDialog(QDialog if HAS_QT else object):
    """Help & Keyboard Shortcuts Dialog."""
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setWindowTitle("Panduan & Keyboard Shortcuts — ZZLUXORA")
        self.setFixedSize(580, 520)
        self.setStyleSheet(CONSOLE_QSS)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(12)

        # Header Title
        title_box = QVBoxLayout()
        title = QLabel("TABEL SHORTCUT KEYBOARD KONSOL")
        title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        desc = QLabel("Gunakan tombol pintas berikut untuk mempercepat pengoperasian pencahayaan panggung.")
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        main_layout.addLayout(title_box)

        # Table
        grp = QGroupBox("Daftar Shortcut Global & Workspace")
        grp.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        grp_layout = QVBoxLayout(grp)

        self.table = QTableWidget(11, 2)
        self.table.setHorizontalHeaderLabels(["Fungsi / Aksi", "Tombol Pintas"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        shortcuts = [
            ("Buka File Project (.zlx)", "Ctrl + O"),
            ("Simpan Project", "Ctrl + S"),
            ("Simpan Sebagai (Save As)", "Ctrl + Shift + S"),
            ("Toggle Play / Stop Art-Net Stream", "Space"),
            ("Instant Grand Master Blackout", "Escape / B"),
            ("Global Undo (Batal Aksi)", "Ctrl + Z"),
            ("Global Redo (Ulang Aksi)", "Ctrl + Shift + Z / Ctrl + Y"),
            ("Workspace: Address Tab", "F1"),
            ("Workspace: Analyze Tab", "F2"),
            ("Workspace: Result Tab", "F3"),
            ("Workspace: Mixer Desk (257 Faders)", "F6"),
        ]

        for row, (action_text, key_text) in enumerate(shortcuts):
            it1 = QTableWidgetItem(action_text)
            it2 = QTableWidgetItem(key_text)
            it1.setFont(QFont("Inter", 9))
            it2.setFont(QFont("JetBrains Mono", 9, QFont.Bold))
            it1.setForeground(QColor(Theme.TEXT_PRIMARY))
            it2.setForeground(QColor(Theme.ACCENT_CYAN))
            it2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, it1)
            self.table.setItem(row, 1, it2)

        grp_layout.addWidget(self.table)
        main_layout.addWidget(grp, 1)

        # Bottom Close Button
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        btn_close = QPushButton("Tutup")
        btn_close.clicked.connect(self.close)
        btn_bar.addWidget(btn_close)
        main_layout.addLayout(btn_bar)

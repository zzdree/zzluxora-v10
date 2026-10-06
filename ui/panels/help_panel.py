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
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Keyboard Shortcuts Reference — ZZLUXORA")
        self.resize(580, 520)
        self.setStyleSheet(CONSOLE_QSS)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(12)

        # Header Title
        title_box = QVBoxLayout()
        title = QLabel("CONSOLE KEYBOARD SHORTCUTS")
        title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        desc = QLabel("Use the following hotkeys for rapid live stage lighting operations.")
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        main_layout.addLayout(title_box)

        # Table
        grp = QGroupBox("Global & Tool Shortcuts")
        grp.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        grp_layout = QVBoxLayout(grp)

        self.table = QTableWidget(11, 2)
        self.table.setHorizontalHeaderLabels(["Action / Function", "Shortcut Key"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        shortcuts = [
            ("Open Project (.zlx)", "Ctrl + O"),
            ("Save Project", "Ctrl + S"),
            ("Save As Project", "Ctrl + Shift + S"),
            ("Toggle Play / Stop Art-Net Stream", "Space"),
            ("Instant Grand Master Blackout", "Escape / B"),
            ("Global Undo", "Ctrl + Z"),
            ("Global Redo", "Ctrl + Shift + Z / Ctrl + Y"),
            ("Open Fixture Library", "Ctrl + F"),
            ("Open Fixture Definition Editor", "Ctrl + E"),
            ("Open Stage Lighting Visualizer", "Ctrl + P"),
            ("Open Network & Art-Net Settings", "Ctrl + Shift + P"),
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
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_bar.addWidget(btn_close)
        main_layout.addLayout(btn_bar)

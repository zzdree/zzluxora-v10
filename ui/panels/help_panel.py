"""
help_panel.py | Application Help & Keyboard Shortcuts Reference Dialog
Displays the comprehensive console shortcuts table.
"""

from __future__ import annotations
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, Qt, QColor, QFont, QIcon
)
from ui.styles import Theme, CONSOLE_QSS


class HelpDialog(QDialog if HAS_QT else object):
    """Help & Keyboard Shortcuts Dialog."""
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Help")
        self.resize(580, 480)
        self.setStyleSheet(CONSOLE_QSS)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_zz.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # Table Box: Shortcuts directly without redundant headers
        grp = QGroupBox("Shortcuts")
        grp.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        grp_layout = QVBoxLayout(grp)

        self.table = QTableWidget(11, 2)
        self.table.setHorizontalHeaderLabels(["Action / Function", "Key"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        try:
            self.table.setEditTriggers(getattr(getattr(QTableWidget, "EditTrigger", QTableWidget), "NoEditTriggers", 0))
        except Exception:
            pass
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_ELEVATED};
                color: {Theme.TEXT_PRIMARY};
                font-weight: 700;
                padding: 4px;
                border: 1px solid {Theme.BORDER_SUBTLE};
            }}
        """)

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
            it1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            it2.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 0, it1)
            self.table.setItem(row, 1, it2)

        grp_layout.addWidget(self.table)
        main_layout.addWidget(grp, 1)

        # Bottom Close Button
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("min-width: 80px; padding: 6px 14px; border-radius: 4px;")
        btn_close.clicked.connect(self.close)
        btn_bar.addWidget(btn_close)
        main_layout.addLayout(btn_bar)

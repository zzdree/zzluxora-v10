"""
sidebar.py — Collapsible Navigation Sidebar with Active Indicators
Provides responsive view switching with grandMA-styled industrial aesthetics.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
    )
    from PySide6.QtCore import Qt, Signal
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

from ui.styles import Theme

class Sidebar(QWidget):
    """Collapsible Left Navigation Sidebar."""
    view_changed = Signal(str) if HAS_QT else None

    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {Theme.BG_SURFACE};
                border-right: 1px solid {Theme.BORDER_SUBTLE};
            }}
            QPushButton {{
                text-align: left;
                padding: 10px 14px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid transparent;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_PANEL};
                border-color: {Theme.BORDER_STRONG};
            }}
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(6)

        lbl_menu = QLabel("NAVIGATION")
        lbl_menu.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: bold; margin-left: 8px; letter-spacing: 1px;")
        layout.addWidget(lbl_menu)

        self.buttons = {}
        items = [
            ("program", "▶  Program"),
            ("fixture_list", "📋  Fixture List"),
            ("fixture_editor", "🛠  Fixture Editor"),
            ("settings", "⚙  Settings"),
            ("about", "ℹ  About")
        ]

        for key, text in items:
            btn = QPushButton(text, self)
            btn.clicked.connect(lambda checked=False, k=key: self._on_btn_clicked(k))
            self.buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Watermark/footer
        lbl_brand = QLabel("ZZLUXORA v10.0\nFT UNNES")
        lbl_brand.setAlignment(Qt.AlignCenter)
        lbl_brand.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px; opacity: 0.6;")
        layout.addWidget(lbl_brand)

        self.set_active("program")

    def _on_btn_clicked(self, key: str):
        self.set_active(key)
        if HAS_QT and self.view_changed:
            self.view_changed.emit(key)

    def set_active(self, active_key: str):
        for key, btn in self.buttons.items():
            if key == active_key:
                btn.setStyleSheet(f"""
                    background-color: {Theme.BG_PANEL};
                    color: {Theme.ACCENT_CYAN};
                    border-left: 3px solid {Theme.ACCENT_CYAN};
                    font-weight: bold;
                """)
            else:
                btn.setStyleSheet(f"""
                    background-color: transparent;
                    color: {Theme.TEXT_SECONDARY};
                    border: none;
                """)

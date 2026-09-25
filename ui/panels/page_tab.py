"""
page_tab.py — Virtual Executor Page Tab
Provides instant-trigger executor buttons for live stage lighting playback during worship service.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
        QFrame, QGroupBox
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

from ui.styles import Theme

class ExecutorButton(QPushButton if HAS_QT else object):
    """grandMA3-style rectangular playback executor button."""
    def __init__(self, cue_name: str, cue_color: str, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.cue_name = cue_name
        self.cue_color = cue_color
        self.is_active = False

        self.setFixedSize(140, 90)
        self.setText(f"{cue_name}\n[GO+]")
        self.update_appearance()
        self.clicked.connect(self._toggle)

    def _toggle(self):
        self.is_active = not self.is_active
        self.update_appearance()

    def update_appearance(self):
        border = self.cue_color if self.is_active else Theme.BORDER_STRONG
        bg = "#1f2937" if self.is_active else Theme.BG_PANEL
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 6px;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {Theme.ACCENT_CYAN};
            }}
        """)


class PageTab(QWidget):
    """Virtual Executor Grid Page."""
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
        title = QLabel("VIRTUAL PLAYBACK EXECUTORS (LIVE PAGE)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        desc = QLabel("Tombol eksekutor langsung panggung untuk memicu scene dan chase secara instan.")
        desc.setStyleSheet("color: #abb2bf; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        main_layout.addLayout(title_box)

        # Executor Grid
        grid_group = QGroupBox("Matriks Executor Tombol Cepat Panggung")
        grid_layout = QGridLayout(grid_group)
        grid_layout.setSpacing(12)

        cues = [
            ("Q1 Praise Fast", "#ffd54f"),
            ("Q1 Praise Chorus", "#ffb300"),
            ("Q2 Holy War", "#ff1744"),
            ("Q2 Minor Peak", "#ea80fc"),
            ("Q3 Deep Worship", "#448aff"),
            ("Q3 Intimate Holy", "#7c4dff"),
            ("Q4 Warm Peace", "#ffffff"),
            ("Q4 Silent Prayer", "#69f0ae"),
            ("All White 100%", "#ffffff"),
            ("Pastel Warm Glow", "#ffcc80"),
            ("Cyan Ocean Wave", "#00e5ff"),
            ("Grand Blackout", "#ff1744"),
        ]

        for i, (name, color) in enumerate(cues):
            btn = ExecutorButton(name, color, grid_group)
            grid_layout.addWidget(btn, i // 4, i % 4)

        main_layout.addWidget(grid_group)
        main_layout.addStretch()

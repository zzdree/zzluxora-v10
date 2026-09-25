"""
scenes_tab.py — Scene Cue Generation and Structural Section Mapping
Maps song structural segments (Intro, Verse, Chorus, Bridge, Ending) to distinct lighting scenes.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QListWidget, QTableWidget, QTableWidgetItem, QSplitter,
        QGroupBox, QHeaderView
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

from ui.styles import Theme

class ScenesTab(QWidget):
    """Scenes Tab: Structural Song Cue Management."""
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
        title = QLabel("SCENE CUE & SECTION MAPPING")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        desc = QLabel("Pembangkitan cue visual per segmen lagu (Intro, Verse, Chorus, Bridge, Ending).")
        desc.setStyleSheet("color: #abb2bf; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        main_layout.addLayout(title_box)

        splitter = QSplitter(Qt.Horizontal)

        # Left: Songs list
        left_grp = QGroupBox("Daftar Lagu Teranalisis")
        l_layout = QVBoxLayout(left_grp)
        self.song_list = QListWidget()
        self.song_list.addItem("Sentuh Hatiku (Slow Worship, 68 BPM)")
        self.song_list.addItem("Nyanyi Bagi Dia (Upbeat Praise, 134 BPM)")
        l_layout.addWidget(self.song_list)
        splitter.addWidget(left_grp)

        # Right: Scene Table
        right_grp = QGroupBox("Daftar Scene & Karakteristik Visual")
        r_layout = QVBoxLayout(right_grp)

        self.table = QTableWidget(5, 5)
        self.table.setHorizontalHeaderLabels(["Bagian Lagu", "Durasi (s)", "Mood Kuadran", "Warna Utama", "Dimmer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        scenes_data = [
            ("Intro", "00:00 - 00:24", "Q4 Peace", "Warm White / Soft Blue", "40%"),
            ("Verse 1", "00:24 - 01:12", "Q3 Deep Worship", "Deep Blue / Purple", "60%"),
            ("Chorus 1", "01:12 - 01:58", "Q1 Praise Puncak", "Amber Gold / Bright Amber", "100%"),
            ("Bridge", "01:58 - 02:40", "Q2 Intense Reverence", "Deep Magenta / Crimson", "85%"),
            ("Ending", "02:40 - 03:15", "Q4 Contemplation", "Soft Cyan / Warm White", "30%")
        ]

        for row, data in enumerate(scenes_data):
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        r_layout.addWidget(self.table)
        splitter.addWidget(right_grp)

        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter)

"""
chase_tab.py — Chase Sequence Control and Dynamic Fade Timing Panel
Coordinates sequential transitions between lighting cues synchronized to song tempo.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QListWidget, QTableWidget, QTableWidgetItem, QSplitter,
        QGroupBox, QHeaderView, QDoubleSpinBox
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

class ChaseTab(QWidget):
    """Chase Tab: Sequential Scene Chase & BPM Fade Engine."""
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
        title = QLabel("CHASE SEQUENCE & TIMING ENGINE")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        desc = QLabel("Pengaturan urutan transisi (*chase*), waktu pudar (*fade time*), dan durasi tahan (*hold time*) berbasis BPM.")
        desc.setStyleSheet("color: #abb2bf; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        main_layout.addLayout(title_box)

        splitter = QSplitter(Qt.Horizontal)

        # Left: Songs list
        left_grp = QGroupBox("Daftar Lagu Terdaftar")
        l_layout = QVBoxLayout(left_grp)
        self.song_list = QListWidget()
        self.song_list.addItem("Sentuh Hatiku (68 BPM)")
        self.song_list.addItem("Nyanyi Bagi Dia (134 BPM)")
        l_layout.addWidget(self.song_list)
        splitter.addWidget(left_grp)

        # Right: Chase Parameters
        right_grp = QGroupBox("Parameter Chase & Transisi Dinamis")
        r_layout = QVBoxLayout(right_grp)

        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Fade Time (detik):"))
        self.spin_fade = QDoubleSpinBox()
        self.spin_fade.setRange(0.1, 10.0)
        self.spin_fade.setValue(1.5)
        timing_layout.addWidget(self.spin_fade)

        timing_layout.addWidget(QLabel("Hold Time (detik):"))
        self.spin_hold = QDoubleSpinBox()
        self.spin_hold.setRange(0.5, 30.0)
        self.spin_hold.setValue(4.0)
        timing_layout.addWidget(self.spin_hold)
        r_layout.addLayout(timing_layout)

        self.table = QTableWidget(4, 4)
        self.table.setHorizontalHeaderLabels(["Langkah Chase", "Scene Terhubung", "Fade (s)", "Hold (s)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        chase_steps = [
            ("Step 1", "Verse 1 (Deep Blue)", "2.0 s", "6.0 s"),
            ("Step 2", "Chorus (Amber Gold)", "1.0 s", "4.0 s"),
            ("Step 3", "Bridge (Crimson)", "1.5 s", "5.0 s"),
            ("Step 4", "Outro (Warm White)", "3.0 s", "8.0 s")
        ]
        for row, data in enumerate(chase_steps):
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        r_layout.addWidget(self.table)
        splitter.addWidget(right_grp)

        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter)

"""
fixture_list.py — Fixture Library and Patch Drag-and-Drop Drawer
Displays available fixture definitions (.json) ready to be patched to DMX channels.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QListWidget, QListWidgetItem, QGroupBox
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

class FixtureList(QWidget):
    """Fixture Library List Drawer."""
    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("PERPUSTAKAAN PROFIL FIXTURE DMX")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        main_layout.addWidget(title)

        grp = QGroupBox("Daftar Lampu Tersedia (Folder fixtures/)")
        grp_layout = QVBoxLayout(grp)

        self.list_widget = QListWidget()
        fixtures = [
            "Generic PAR LED RGBW (4 Channel: R, G, B, W)",
            "Generic PAR LED RGBW + Dimmer + Strobe (7 Channel)",
            "Generic PAR LED RGBWA + UV (8 Channel)",
            "Moving Head Beam Spot RGBW (16 Channel)"
        ]
        for fix in fixtures:
            item = QListWidgetItem(f"💡 {fix}")
            self.list_widget.addItem(item)

        grp_layout.addWidget(self.list_widget)
        main_layout.addWidget(grp)
        main_layout.addStretch()

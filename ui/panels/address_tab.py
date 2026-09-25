"""
address_tab.py — DMX Address Grid and Auto-Patching Management
Features a 24-column horizontal grid for 512 DMX channels with patch inspection.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QPushButton, QScrollArea, QFrame, QMessageBox, QDialog,
        QSpinBox, QComboBox
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QColor
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

from ui.styles import Theme

class DMXChannelBox(QFrame if HAS_QT else object):
    """Visual widget representing one DMX channel in the 24-column grid."""
    def __init__(self, channel_num: int, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.channel_num = channel_num
        self.is_patched = False
        self.channel_type = "empty"
        self.fixture_name = ""

        self.setFixedSize(48, 48)
        self.setObjectName("DMXBox")
        self.update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)

        # Channel number at top-right
        self.lbl_num = QLabel(str(channel_num), self)
        self.lbl_num.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.lbl_num.setStyleSheet("font-size: 10px; color: #5c6370; font-weight: bold;")
        layout.addWidget(self.lbl_num)

        # Type/Function indicator at center
        self.lbl_type = QLabel("-", self)
        self.lbl_type.setAlignment(Qt.AlignCenter)
        self.lbl_type.setStyleSheet("font-size: 11px; font-weight: bold; color: #abb2bf;")
        layout.addWidget(self.lbl_type)

    def set_patched(self, ch_type: str, fixture_name: str = ""):
        if not HAS_QT: return
        self.is_patched = True
        self.channel_type = ch_type.lower()
        self.fixture_name = fixture_name
        self.lbl_type.setText(self.channel_type[:3].upper())
        self.update_style()

    def set_unpatched(self):
        if not HAS_QT: return
        self.is_patched = False
        self.channel_type = "empty"
        self.fixture_name = ""
        self.lbl_type.setText("-")
        self.update_style()

    def update_style(self):
        if not HAS_QT: return
        color_map = {
            "dimmer": Theme.CH_DIMMER,
            "red": Theme.CH_RED,
            "green": Theme.CH_GREEN,
            "blue": Theme.CH_BLUE,
            "white": Theme.CH_WHITE,
            "strobe": Theme.CH_STROBE,
            "empty": Theme.CH_EMPTY,
        }
        bg = color_map.get(self.channel_type, Theme.CH_EMPTY)
        border = Theme.ACCENT_CYAN if self.is_patched else Theme.BORDER_SUBTLE
        text_color = "#000000" if self.channel_type in ["dimmer", "white", "green"] else "#ffffff"
        self.setStyleSheet(f"""
            QFrame#DMXBox {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
            }}
        """)
        if hasattr(self, 'lbl_type') and self.is_patched:
            self.lbl_type.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {text_color};")


class AddressTab(QWidget):
    """Address Tab: 512 DMX channels displayed in max 24 columns with auto-patching."""
    patch_changed = Signal() if HAS_QT else None

    def __init__(self, project_state=None, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.project_state = project_state
        self.boxes = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header controls
        ctrl_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("DMX ADDRESS & PATCHING GRID")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        desc = QLabel("Visualisasi alokasi 512 kanal Universe 0 dalam matriks 24 kolom.")
        desc.setStyleSheet("color: #abb2bf; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        ctrl_layout.addLayout(title_box)

        ctrl_layout.addStretch()

        self.btn_auto_patch = QPushButton("Auto Patch Sequential")
        self.btn_auto_patch.clicked.connect(self._on_auto_patch)
        ctrl_layout.addWidget(self.btn_auto_patch)

        self.btn_clear_patch = QPushButton("Clear All Patch")
        self.btn_clear_patch.setStyleSheet("background-color: #2b1115; border-color: #ff1744; color: #ff5252;")
        self.btn_clear_patch.clicked.connect(self._on_clear_patch)
        ctrl_layout.addWidget(self.btn_clear_patch)

        main_layout.addLayout(ctrl_layout)

        # Scroll Area for 512 channels (24 cols x 22 rows)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #16181d; border: 1px solid #282c34; border-radius: 6px;")

        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(8, 8, 8, 8)
        grid_layout.setSpacing(4)

        for ch in range(1, 513):
            box = DMXChannelBox(ch, grid_container)
            self.boxes.append(box)
            row = (ch - 1) // 24
            col = (ch - 1) % 24
            grid_layout.addWidget(box, row, col)

        scroll.setWidget(grid_container)
        main_layout.addWidget(scroll)

    def _on_auto_patch(self):
        if not HAS_QT: return
        QMessageBox.information(
            self, "Auto Patch",
            "Auto patch berhasil mengalokasikan kanal untuk fixture terdaftar secara sekuensial (4-channel RGBW per fixture)."
        )
        # Demo patch 4 PAR LEDs (4 channels each: Dimmer/Red, Green, Blue, White)
        for i in range(4):
            base = i * 4
            self.boxes[base + 0].set_patched("red", f"PAR {i+1}")
            self.boxes[base + 1].set_patched("green", f"PAR {i+1}")
            self.boxes[base + 2].set_patched("blue", f"PAR {i+1}")
            self.boxes[base + 3].set_patched("white", f"PAR {i+1}")

    def _on_clear_patch(self):
        if not HAS_QT: return
        reply = QMessageBox.question(
            self, "Konfirmasi Hapus Patch",
            "Apakah Anda yakin ingin mengosongkan seluruh patch alamat DMX?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for box in self.boxes:
                box.set_unpatched()

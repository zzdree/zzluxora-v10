"""
address_tab.py — DMX Address Grid and Patch Sheet
Implements a 24-column horizontal grid for 256 DMX channels with drag-and-drop patching,
channel type color-coding, confirmation modal on clear, and Undo/Redo support.
"""

from __future__ import annotations
import json

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox, QDialog,
    QSpinBox, QComboBox, Qt, Signal, QMimeData, QColor,
    QDragEnterEvent, QDropEvent, QAction, QKeySequence
)
from ui.styles import Theme


class DMXChannelBox(QFrame if HAS_QT else object):
    """Visual widget representing one DMX channel (1–256) in the 24-column grid."""
    def __init__(self, channel_num: int, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.channel_num = channel_num
        self.is_patched = False
        self.channel_type = "empty"
        self.channel_label = ""
        self.fixture_name = ""

        self.setFixedSize(46, 46)
        self.setObjectName("DMXBox")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        # Channel number at top-right
        self.lbl_num = QLabel(str(channel_num), self)
        self.lbl_num.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.lbl_num.setStyleSheet(f"font-size: 9px; color: {Theme.TEXT_MUTED}; font-weight: 700; font-family: monospace;")
        layout.addWidget(self.lbl_num)

        # Type/Function indicator at center
        self.lbl_type = QLabel("-", self)
        self.lbl_type.setAlignment(Qt.AlignCenter)
        self.lbl_type.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Theme.TEXT_MUTED};")
        layout.addWidget(self.lbl_type, 1)

        self.update_style()

    def set_patched(self, ch_type: str, label: str = "", fixture_name: str = ""):
        self.is_patched = True
        self.channel_type = ch_type.lower()
        self.channel_label = label if label else ch_type.upper()
        self.fixture_name = fixture_name

        short_label = self.channel_label[:4].upper()
        if "dim" in self.channel_type: short_label = "DIM"
        elif "strobe" in self.channel_type: short_label = "STR"
        elif "red" in self.channel_type: short_label = "RED"
        elif "green" in self.channel_type: short_label = "GRN"
        elif "blue" in self.channel_type: short_label = "BLU"
        elif "white" in self.channel_type: short_label = "WHT"

        self.lbl_type.setText(short_label)
        self.update_style()

    def set_unpatched(self):
        self.is_patched = False
        self.channel_type = "empty"
        self.channel_label = ""
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
            "pan": Theme.CH_PAN_TILT,
            "tilt": Theme.CH_PAN_TILT,
            "color macro": Theme.CH_COLOR_MACRO,
            "empty": Theme.CH_EMPTY,
        }
        bg = color_map.get(self.channel_type, Theme.CH_EMPTY)
        border = Theme.BORDER_HIGHLIGHT if self.is_patched else Theme.BORDER_SUBTLE
        text_color = "#000000" if self.channel_type in ["dimmer", "white", "green", "strobe"] else "#ffffff"

        self.setStyleSheet(f"""
            QFrame#DMXBox {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
            }}
        """)
        if hasattr(self, 'lbl_type'):
            if self.is_patched:
                self.lbl_type.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {text_color};")
            else:
                self.lbl_type.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Theme.TEXT_MUTED};")


class AddressGridArea(QWidget if HAS_QT else object):
    """Grid container supporting Drag and Drop for Fixtures."""
    fixture_dropped = Signal(int, dict)  # (start_channel, fixture_data)

    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.boxes: dict[int, DMXChannelBox] = {}

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setSpacing(5)

        # 256 channels in max 24 columns
        COLS = 24
        for ch in range(1, 257):
            box = DMXChannelBox(ch, self)
            self.boxes[ch] = box
            row = (ch - 1) // COLS
            col = (ch - 1) % COLS
            self.grid_layout.addWidget(box, row, col)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat("application/x-zzluxora-fixture") or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        pos = event.position().toPoint()
        child = self.childAt(pos)
        while child and not isinstance(child, DMXChannelBox) and child != self:
            child = child.parentWidget()

        start_channel = child.channel_num if isinstance(child, DMXChannelBox) else 1

        try:
            if event.mimeData().hasFormat("application/x-zzluxora-fixture"):
                raw = bytes(event.mimeData().data("application/x-zzluxora-fixture")).decode("utf-8")
                fixture_data = json.loads(raw)
            else:
                raw = event.mimeData().text()
                fixture_data = json.loads(raw)
            self.fixture_dropped.emit(start_channel, fixture_data)
            event.acceptProposedAction()
        except Exception:
            event.ignore()


class AddressTab(QWidget if HAS_QT else object):
    """
    Address Tab: 256 DMX channels displayed in max 24 columns.
    Features Drag & Drop fixture patching, Clear All with confirmation, and Undo/Redo.
    """
    patch_changed = Signal()

    def __init__(self, project_state=None, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.project_state = project_state
        self.undo_stack: list[dict] = []
        self.redo_stack: list[dict] = []
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # Top Control Action Bar
        ctrl_bar = QHBoxLayout()

        title_box = QVBoxLayout()
        lbl_title = QLabel("DMX ADDRESS PATCH SHEET")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {Theme.TEXT_PRIMARY}; letter-spacing: 0.5px;")
        lbl_desc = QLabel("Matriks 256 Kanal DMX (Maks 24 Kolom) | Drag fixture dari Fixture List untuk melakukan patching.")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        ctrl_bar.addLayout(title_box)

        ctrl_bar.addStretch()

        # Action Buttons (Clean Industrial Lighting Style)
        self.btn_undo = QPushButton("UNDO (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.undo_patch)
        self.btn_undo.setEnabled(False)
        ctrl_bar.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("REDO (Ctrl+Y)")
        self.btn_redo.clicked.connect(self.redo_patch)
        self.btn_redo.setEnabled(False)
        ctrl_bar.addWidget(self.btn_redo)

        self.btn_auto_patch = QPushButton("AUTO PATCH (4 PAR)")
        self.btn_auto_patch.clicked.connect(self._on_auto_patch_default)
        ctrl_bar.addWidget(self.btn_auto_patch)

        self.btn_clear = QPushButton("CLEAR PATCH")
        self.btn_clear.setStyleSheet(f"color: {Theme.COLOR_DANGER}; border-color: {Theme.BORDER_STRONG};")
        self.btn_clear.clicked.connect(self._on_clear_patch_confirm)
        ctrl_bar.addWidget(self.btn_clear)

        main_layout.addLayout(ctrl_bar)

        # Scrollable Grid Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Theme.BG_ROOT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 6px;
            }}
        """)

        self.grid_area = AddressGridArea(self)
        self.grid_area.fixture_dropped.connect(self._on_fixture_dropped)
        self.scroll_area.setWidget(self.grid_area)
        main_layout.addWidget(self.scroll_area, 1)

    def _snapshot_state(self) -> dict:
        """Captures current patch state for Undo/Redo."""
        snap = {}
        for ch, box in self.grid_area.boxes.items():
            if box.is_patched:
                snap[ch] = (box.channel_type, box.channel_label, box.fixture_name)
        return snap

    def _restore_snapshot(self, snap: dict) -> None:
        for ch, box in self.grid_area.boxes.items():
            if ch in snap:
                ch_type, label, fixture_name = snap[ch]
                box.set_patched(ch_type, label, fixture_name)
            else:
                box.set_unpatched()
        self.patch_changed.emit()

    def record_undo(self) -> None:
        self.undo_stack.append(self._snapshot_state())
        self.redo_stack.clear()
        self.btn_undo.setEnabled(True)
        self.btn_redo.setEnabled(False)

    def undo_patch(self) -> None:
        if not self.undo_stack: return
        self.redo_stack.append(self._snapshot_state())
        snap = self.undo_stack.pop()
        self._restore_snapshot(snap)
        self.btn_undo.setEnabled(len(self.undo_stack) > 0)
        self.btn_redo.setEnabled(True)

    def redo_patch(self) -> None:
        if not self.redo_stack: return
        self.undo_stack.append(self._snapshot_state())
        snap = self.redo_stack.pop()
        self._restore_snapshot(snap)
        self.btn_undo.setEnabled(True)
        self.btn_redo.setEnabled(len(self.redo_stack) > 0)

    def _on_fixture_dropped(self, start_channel: int, fixture_data: dict) -> None:
        channels = fixture_data.get("channels", [])
        if not channels: return

        self.record_undo()
        fixture_name = fixture_data.get("model", "Fixture")

        for idx, ch_info in enumerate(channels):
            target_ch = start_channel + idx
            if target_ch > 256: break
            box = self.grid_area.boxes.get(target_ch)
            if box:
                ch_type = ch_info.get("type", "empty")
                label = ch_info.get("label", ch_type)
                box.set_patched(ch_type, label, fixture_name)

        self.patch_changed.emit()

    def _on_clear_patch_confirm(self) -> None:
        reply = QMessageBox.question(
            self,
            "Konfirmasi Clear All Patch",
            "Apakah Anda yakin ingin mengosongkan seluruh patch DMX?\n\n(Aksi ini dapat dibatalkan dengan tombol Undo)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.record_undo()
            for box in self.grid_area.boxes.values():
                box.set_unpatched()
            self.patch_changed.emit()

    def _on_auto_patch_default(self) -> None:
        """Auto patches 4 standard PAR LED RGBW fixtures (16 channels total)."""
        self.record_undo()
        channels_pattern = [
            ("red", "RED"),
            ("green", "GRN"),
            ("blue", "BLU"),
            ("white", "WHT"),
        ]
        ch_idx = 1
        for par_num in range(1, 5):
            for ch_type, lbl in channels_pattern:
                box = self.grid_area.boxes.get(ch_idx)
                if box:
                    box.set_patched(ch_type, lbl, f"PAR {par_num}")
                ch_idx += 1
        self.patch_changed.emit()

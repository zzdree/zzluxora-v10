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
        ct = self.channel_type
        if "dim" in ct: short_label = "DIM"
        elif "strobe" in ct: short_label = "STR"
        elif "shutter" in ct: short_label = "SHT"
        elif "red" in ct: short_label = "RED"
        elif "green" in ct: short_label = "GRN"
        elif "blue" in ct: short_label = "BLU"
        elif "white" in ct: short_label = "WHT"
        elif "amber" in ct: short_label = "AMB"
        elif "uv" in ct: short_label = "UV"
        elif "cyan" in ct: short_label = "CYN"
        elif "magenta" in ct: short_label = "MAG"
        elif "yellow" in ct: short_label = "YEL"
        elif "pan" in ct: short_label = "PAN"
        elif "tilt" in ct: short_label = "TLT"
        elif "gobo" in ct: short_label = "GOB"
        elif "prism" in ct: short_label = "PRS"
        elif "program" in ct: short_label = "PRG"
        elif "macro" in ct: short_label = "MAC"
        elif "speed" in ct: short_label = "SPD"
        elif "effect" in ct: short_label = "FX"
        elif "maint" in ct: short_label = "MNT"
        elif "empt" in ct: short_label = "EMP"

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
            "amber": Theme.CH_AMBER,
            "uv": Theme.CH_UV,
            "cyan": Theme.CH_CYAN,
            "magenta": Theme.CH_MAGENTA,
            "yellow": Theme.CH_YELLOW,
            "strobe": Theme.CH_STROBE,
            "shutter": Theme.CH_SHUTTER,
            "pan": Theme.CH_PAN_TILT,
            "tilt": Theme.CH_PAN_TILT,
            "color macro": Theme.CH_COLOR_MACRO,
            "macro": Theme.CH_COLOR_MACRO,
            "gobo": Theme.CH_GOBO,
            "prism": Theme.CH_PRISM,
            "program": Theme.CH_PROGRAM,
            "speed": Theme.CH_SPEED,
            "effect": Theme.CH_EFFECT,
            "maintenance": Theme.CH_MAINTENANCE,
            "empty": Theme.CH_EMPTY,
        }
        bg = color_map.get(self.channel_type, Theme.CH_EMPTY)
        border = Theme.BORDER_HIGHLIGHT if self.is_patched else Theme.BORDER_SUBTLE
        light_types = ["dimmer", "white", "green", "amber", "yellow", "cyan", "strobe", "shutter"]
        text_color = "#000000" if self.channel_type in light_types else "#ffffff"

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

        self.btn_patch_alien = QPushButton("PATCH 4x ALIEN (GIA)")
        self.btn_patch_alien.setToolTip("Auto-patch 4x Alien AL36 di DMX001, DMX017, DMX033, DMX049 (Panggung GIA Deliksari)")
        self.btn_patch_alien.setStyleSheet(f"border-color: {Theme.ACCENT_CYAN}; color: #ffffff; font-weight: bold;")
        self.btn_patch_alien.clicked.connect(self._on_patch_alien_gia)
        ctrl_bar.addWidget(self.btn_patch_alien)

        self.btn_patch_kuma = QPushButton("PATCH 1x KUMA (BENCH)")
        self.btn_patch_kuma.setToolTip("Auto-patch 1x Kumastb STL47 di DMX001 (Unit Uji Laboratorium RGBW)")
        self.btn_patch_kuma.setStyleSheet(f"border-color: {Theme.ACCENT_AMBER}; color: #ffffff; font-weight: bold;")
        self.btn_patch_kuma.clicked.connect(self._on_patch_kuma_bench)
        ctrl_bar.addWidget(self.btn_patch_kuma)

        # Legacy alias for backward compatibility
        self.btn_auto_patch = self.btn_patch_alien

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
        fixture_name = fixture_data.get("name") or fixture_data.get("model", "Fixture")

        for idx, ch_info in enumerate(channels):
            target_ch = start_channel + idx
            if target_ch > 256: break
            box = self.grid_area.boxes.get(target_ch)
            if box:
                ch_type = ch_info.get("type", "empty")
                label = ch_info.get("label", ch_type)
                box.set_patched(ch_type, label, fixture_name)

        self.patch_changed.emit()

    def get_patched_fixtures(self) -> list[dict]:
        """Returns list of active patched fixture blocks from the address grid."""
        fixtures = []
        visited = set()
        for ch in range(1, 257):
            if ch in visited:
                continue
            box = self.grid_area.boxes.get(ch)
            if box and box.is_patched and box.fixture_name:
                fname = box.fixture_name
                start_ch = ch
                fixture_channels = []
                cur = ch
                while cur <= 256:
                    cbox = self.grid_area.boxes.get(cur)
                    if cbox and cbox.is_patched and cbox.fixture_name == fname:
                        fixture_channels.append({
                            "channel": cur,
                            "type": cbox.channel_type,
                            "label": cbox.channel_label,
                        })
                        visited.add(cur)
                        cur += 1
                    else:
                        break
                fixtures.append({
                    "id": len(fixtures) + 1,
                    "name": fname,
                    "start_channel": start_ch,
                    "channels": fixture_channels,
                    "channel_count": len(fixture_channels),
                })
        return fixtures

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

    def _on_patch_alien_gia(self) -> None:
        """Auto-patch four Alien AL36 (8CH RGB) fixtures at DMX001, DMX017, DMX033, DMX049."""
        self.record_undo()
        for box in self.grid_area.boxes.values():
            box.set_unpatched()

        alien_channels = [
            {"type": "dimmer", "label": "Dimmer"},
            {"type": "red", "label": "Red"},
            {"type": "green", "label": "Green"},
            {"type": "blue", "label": "Blue"},
            {"type": "empty", "label": "Empty"},
            {"type": "program", "label": "Program"},
            {"type": "speed", "label": "Speed"},
            {"type": "empty", "label": "Emptz"},
        ]
        start_addresses = [1, 17, 33, 49]
        for fixture_idx, start_ch in enumerate(start_addresses):
            fixture_data = {
                "name": f"Alien AL36 #{fixture_idx + 1} (8CH)",
                "channels": alien_channels,
            }
            self._on_fixture_dropped(start_ch, fixture_data)

    def _on_patch_kuma_bench(self) -> None:
        """Auto-patch one Kumastb STL47 (8CH RGBW) fixture at DMX001."""
        self.record_undo()
        for box in self.grid_area.boxes.values():
            box.set_unpatched()

        kuma_channels = [
            {"type": "dimmer", "label": "Dimmer"},
            {"type": "red", "label": "Red"},
            {"type": "green", "label": "Green"},
            {"type": "blue", "label": "Blue"},
            {"type": "white", "label": "White"},
            {"type": "strobe", "label": "Strobe"},
            {"type": "program", "label": "Program"},
            {"type": "speed", "label": "Speed"},
        ]
        fixture_data = {
            "name": "Kumastb STL47 (8CH RGBW)",
            "channels": kuma_channels,
        }
        self._on_fixture_dropped(1, fixture_data)

    def _on_auto_patch_default(self) -> None:
        """Legacy compatibility method pointing to Alien AL36 4x GIA setup."""
        self._on_patch_alien_gia()

"""
address_tab.py | DMX Address Grid and Patch Sheet
Implements a 24-column horizontal grid for 512 DMX channels with drag-and-drop patching,
channel type color-coding, confirmation modal on clear, and Undo/Redo support.
"""

from __future__ import annotations
import json

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox, QDialog,
    QSpinBox, QComboBox, QInputDialog, QListWidget, QListWidgetItem,
    Qt, Signal, QMimeData, QColor,
    QDragEnterEvent, QDragMoveEvent, QDropEvent, QAction, QKeySequence
)
from ui.styles import Theme


class DMXChannelBox(QFrame if HAS_QT else object):
    """Visual widget representing one DMX channel (1-512) in the 24-column grid."""
    def __init__(self, channel_num: int, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.channel_num = channel_num
        self.is_patched = False
        self.channel_type = "empty"
        self.channel_label = ""
        self.fixture_name = ""
        self.is_drag_hover = False
        self.is_panel_selected = False
        self.boundary_type = ""  # "start", "mid", "end", "single", ""

        self.setFixedSize(46, 46)
        self.setObjectName("DMXBox")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        # Channel number at top-right
        self.lbl_num = QLabel(str(channel_num), self)
        self.lbl_num.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.lbl_num.setStyleSheet(f"font-size: 9px; color: {Theme.TEXT_CONTRAST_UNPATCHED}; font-weight: 700; font-family: monospace;")
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
        light_types = [
            "dimmer", "white", "green", "amber", "yellow", "cyan", "strobe", "shutter",
            "pan", "tilt", "macro", "effect", "gobo", "prism", "color macro", "magenta"
        ]
        text_color = Theme.SURFACE_VOID if self.channel_type in light_types else Theme.TEXT_PRIMARY

        if self.is_drag_hover:
            box_style = f"background-color: {Theme.BG_ELEVATED}; border: 2px solid {Theme.ACCENT_CYAN}; border-radius: 4px;"
        elif self.is_panel_selected:
            # Selection from the fixture panel is drawn as a white frame over
            # whatever the cell already shows, so the channel's own colour and
            # meaning survive while the operator sees which fixture is picked.
            border_base = f"border: 2px solid {Theme.TEXT_PRIMARY};"
            box_style = f"background-color: {bg}; {border_base} border-radius: 4px;"
        elif self.is_patched:
            border_base = f"border: 1px solid {Theme.BORDER_HIGHLIGHT};"
            if self.boundary_type == "start":
                border_base += f" border-left: 3px solid {Theme.ACCENT_CYAN};"
            elif self.boundary_type == "end":
                border_base += f" border-right: 3px solid {Theme.ACCENT_CYAN};"
            box_style = f"background-color: {bg}; {border_base} border-radius: 4px;"
        else:
            box_style = f"background-color: {bg}; border: 1px solid {Theme.BORDER_SUBTLE}; border-radius: 4px;"

        self.setStyleSheet(f"""
            QFrame#DMXBox {{
                {box_style}
            }}
        """)
        # The child labels must not paint their own background. The console
        # stylesheet sets `QWidget { background-color: ... }`, which every QLabel
        # inherits, so each label was drawing a dark rectangle over the cell fill
        # and a patched channel read as a coloured outline instead of a solid
        # block. Transparent labels let the channel colour fill the whole cell.
        if hasattr(self, 'lbl_num'):
            num_color = text_color if self.is_patched else Theme.TEXT_CONTRAST_UNPATCHED
            self.lbl_num.setStyleSheet(
                f"background: transparent; font-size: 9px; color: {num_color}; "
                f"font-weight: 700; font-family: monospace;"
            )
        if hasattr(self, 'lbl_type'):
            if self.is_patched:
                self.lbl_type.setStyleSheet(
                    f"background: transparent; font-size: 10px; font-weight: 800; color: {text_color};"
                )
            else:
                self.lbl_type.setStyleSheet(
                    f"background: transparent; font-size: 10px; font-weight: 800; "
                    f"color: {Theme.TEXT_MUTED};"
                )


class AddressGridArea(QWidget if HAS_QT else object):
    """Grid container supporting Drag and Drop for Fixtures."""
    fixture_dropped = Signal(int, dict)  # (start_channel, fixture_data)

    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.boxes: dict[int, DMXChannelBox] = {}
        self._drag_footprint = 8

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setSpacing(5)

        # 512 channels (one full universe) in max 24 columns
        COLS = 24
        for ch in range(1, 513):
            box = DMXChannelBox(ch, self)
            self.boxes[ch] = box
            row = (ch - 1) // COLS
            col = (ch - 1) % COLS
            self.grid_layout.addWidget(box, row, col)

    def _extract_drag_footprint(self, mime_data) -> int:
        try:
            if mime_data.hasFormat("application/x-zzluxora-fixture"):
                raw = bytes(mime_data.data("application/x-zzluxora-fixture")).decode("utf-8")
                fixture_data = json.loads(raw)
            elif mime_data.hasText():
                fixture_data = json.loads(mime_data.text())
            else:
                return 8
            channels = fixture_data.get("channels", [])
            return len(channels) if channels else int(fixture_data.get("channel_count", 8))
        except Exception:
            return 8

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat("application/x-zzluxora-fixture") or event.mimeData().hasText():
            self._drag_footprint = self._extract_drag_footprint(event.mimeData())
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        pos = event.position().toPoint()
        child = self.childAt(pos)
        while child and not isinstance(child, DMXChannelBox) and child != self:
            child = child.parentWidget()
        if isinstance(child, DMXChannelBox):
            footprint = getattr(self, "_drag_footprint", 8)
            self._set_drag_hover(child.channel_num, footprint)
            event.acceptProposedAction()
        else:
            self._clear_drag_hover()
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._clear_drag_hover()
        self._drag_footprint = 8

    def _set_drag_hover(self, start_channel: int, footprint: int = 8) -> None:
        self._drag_footprint = footprint
        # Track the previous footprint so a new hover that overlaps the old one
        # repaints every affected cell. Comparing only the boolean left the
        # cells shared by both footprints painted with the previous extent.
        previous = getattr(self, "_drag_hover_range", None)
        current = (start_channel, start_channel + footprint)
        self._drag_hover_range = current
        for ch, box in self.boxes.items():
            in_range = (start_channel <= ch < start_channel + footprint)
            was_in_range = bool(previous) and (previous[0] <= ch < previous[1])
            if box.is_drag_hover != in_range or was_in_range:
                box.is_drag_hover = in_range
                box.update_style()

    def _clear_drag_hover(self) -> None:
        self._drag_hover_range = None
        for box in self.boxes.values():
            if box.is_drag_hover:
                box.is_drag_hover = False
                box.update_style()

    def clear_drag_hover(self) -> None:
        """Public wrapper so callers outside the grid can drop a stale preview."""
        self._clear_drag_hover()

    def dropEvent(self, event: QDropEvent) -> None:
        self._clear_drag_hover()
        self._drag_footprint = 8
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


class FixtureListPanel(QWidget if HAS_QT else object):
    """The register of patched fixtures, and the source for drag-and-drop.

    Layout follows QLC+'s FixtureBrowserDelegate: one row per fixture at a fixed
    row height, label on the left, a 1px divider underneath, no decoration. The
    address is derived from the grid rather than stored, so the panel cannot
    drift out of step with the patch.
    """

    fixture_selected = Signal(list)   # channels of the selected fixture(s)
    remove_requested = Signal(list)   # start channels to remove
    add_requested = Signal()          # the operator pressed +

    PANEL_WIDTH = 210

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self.setFixedWidth(self.PANEL_WIDTH)
        self._rows: list[dict] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        bar = QHBoxLayout()
        bar.setContentsMargins(8, 0, 0, 0)
        bar.setSpacing(6)
        lbl = QLabel("FIXTURES")
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 800; letter-spacing: 0.6px; "
            f"color: {Theme.TEXT_SECONDARY};")
        bar.addWidget(lbl)
        bar.addStretch()

        self.btn_add = QPushButton("+")
        self.btn_add.setFixedSize(26, 22)
        self.btn_add.setToolTip("Patch a preset fixture layout")
        self.btn_add.clicked.connect(self.add_requested.emit)
        bar.addWidget(self.btn_add)

        self.btn_remove = QPushButton("-")
        self.btn_remove.setFixedSize(26, 22)
        self.btn_remove.setToolTip("Remove the selected fixture(s)")
        self.btn_remove.setEnabled(False)
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        bar.addWidget(self.btn_remove)

        layout.addLayout(bar)

        self.list_widget = QListWidget()
        # Qt6 moved enums inside the enum class, so ExtendedSelection is reached
        # through SelectionMode. Fall back to the flat Qt5 form when present.
        mode = getattr(QListWidget, "ExtendedSelection", None)
        if mode is None:
            selection_mode = getattr(QListWidget, "SelectionMode", None)
            mode = getattr(selection_mode, "ExtendedSelection", 3)
        self.list_widget.setSelectionMode(mode)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {Theme.SURFACE_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {Theme.BORDER_SUBTLE};
                color: {Theme.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QListWidget::item:selected {{
                background-color: {Theme.BG_ELEVATED};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.list_widget, 1)

        self.empty_label = QLabel("No fixtures patched.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; padding: 12px;")
        layout.addWidget(self.empty_label)

    def refresh_from_grid(self) -> None:
        """Rebuild the list from the AddressTab patch state."""
        tab = self.parent()
        fixtures = tab.get_patched_fixtures() if hasattr(tab, "get_patched_fixtures") else []
        # Order by starting address so the numbering matches the grid reading
        # order and stays stable while the operator patches.
        fixtures = sorted(fixtures, key=lambda f: f.get("start_channel", 0))
        self._rows = fixtures

        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for index, fixture in enumerate(fixtures, 1):
            start = fixture.get("start_channel", 0)
            count = len(fixture.get("channels", []))
            end = start + count - 1 if count else start
            span = f"DMX {start}" if count <= 1 else f"DMX {start}-{end}"
            item = QListWidgetItem(f"[{index}] {fixture.get('name', 'Fixture')}\n     {span}")
            item.setData(Qt.UserRole, start)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

        has_rows = bool(fixtures)
        self.list_widget.setVisible(has_rows)
        self.empty_label.setVisible(not has_rows)
        self.btn_remove.setEnabled(False)
        self.fixture_selected.emit([])

    def _on_selection_changed(self) -> None:
        starts = self.selected_start_channels()
        self.btn_remove.setEnabled(bool(starts))
        channels: list[int] = []
        for row in self._rows:
            if row.get("start_channel") in starts:
                channels.extend(c["channel"] for c in row.get("channels", []))
        self.fixture_selected.emit(channels)

    def selected_start_channels(self) -> list[int]:
        return [item.data(Qt.UserRole) for item in self.list_widget.selectedItems()]

    def _on_remove_clicked(self) -> None:
        starts = self.selected_start_channels()
        if starts:
            self.remove_requested.emit(starts)


class AddressTab(QWidget if HAS_QT else object):
    """
    Address Tab: 512 DMX channels displayed in max 24 columns.
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

        ctrl_bar.addStretch()

        # Patch and clear are the only two actions worth a button here. Undo and
        # redo were removed: Ctrl+Z / Ctrl+Y are bound globally, so dedicated
        # buttons duplicated a shortcut every operator already has and spent the
        # bar's width on nothing. The two auto-patch presets collapsed into one
        # PATCH button that asks which layout to apply.
        self.btn_patch = QPushButton("PATCH...")
        self.btn_patch.setToolTip("Patch a preset fixture layout")
        self.btn_patch.clicked.connect(self._on_patch_clicked)
        ctrl_bar.addWidget(self.btn_patch)

        # Backward-compatible aliases: existing tests and shortcuts refer to the
        # former two-button layout.
        self.btn_patch_alien = self.btn_patch
        self.btn_patch_kuma = self.btn_patch
        self.btn_auto_patch = self.btn_patch

        self.btn_clear = QPushButton("CLEAR PATCH")
        self.btn_clear.setToolTip("Remove every patched channel after confirmation")
        self.btn_clear.setStyleSheet(f"color: {Theme.COLOR_DANGER};")
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

        # Fixture panel on the left, grid on the right. The panel is the source
        # for drag-and-drop and the register of what is patched; without it the
        # only way to know what a block of coloured cells represents was to read
        # the cells themselves.
        self.fixture_panel = FixtureListPanel(self)
        self.fixture_panel.fixture_selected.connect(self._on_fixture_selected)
        self.fixture_panel.remove_requested.connect(self._on_remove_fixtures)
        self.fixture_panel.add_requested.connect(self._on_patch_clicked)

        body_split = QHBoxLayout()
        body_split.setSpacing(12)
        body_split.addWidget(self.fixture_panel, 0)
        body_split.addWidget(self.scroll_area, 1)
        main_layout.addLayout(body_split, 1)

        self.patch_changed.connect(self.fixture_panel.refresh_from_grid)
        self.fixture_panel.refresh_from_grid()

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
        self.update_fixture_brackets()
        self.patch_changed.emit()

    def record_undo(self) -> None:
        """Snapshot the patch before a change.

        The undo/redo stacks are kept because Ctrl+Z and Ctrl+Y drive them from
        the global shortcut handler. The buttons that used to enable or disable
        themselves from these two methods are gone: they only mirrored state the
        shortcut handler already owns, and a stack depth check belongs there, not
        in a button that no longer exists.
        """
        self.undo_stack.append(self._snapshot_state())
        self.redo_stack.clear()

    def undo_patch(self) -> None:
        if not self.undo_stack:
            return
        self.redo_stack.append(self._snapshot_state())
        snap = self.undo_stack.pop()
        self._restore_snapshot(snap)

    def redo_patch(self) -> None:
        if not self.redo_stack:
            return
        self.undo_stack.append(self._snapshot_state())
        snap = self.redo_stack.pop()
        self._restore_snapshot(snap)

    def update_fixture_brackets(self) -> None:
        """Computes and assigns fixture enclosure boundary markers across DMX boxes."""
        fixtures = self.get_patched_fixtures()
        for box in self.grid_area.boxes.values():
            box.boundary_type = ""

        for fix in fixtures:
            channels = fix.get("channels", [])
            if not channels: continue
            if len(channels) == 1:
                ch = channels[0]["channel"]
                if ch in self.grid_area.boxes:
                    self.grid_area.boxes[ch].boundary_type = "single"
            else:
                first_ch = channels[0]["channel"]
                last_ch = channels[-1]["channel"]
                if first_ch in self.grid_area.boxes:
                    self.grid_area.boxes[first_ch].boundary_type = "start"
                if last_ch in self.grid_area.boxes:
                    self.grid_area.boxes[last_ch].boundary_type = "end"
                for ch_info in channels[1:-1]:
                    mid_ch = ch_info["channel"]
                    if mid_ch in self.grid_area.boxes:
                        self.grid_area.boxes[mid_ch].boundary_type = "mid"

        for box in self.grid_area.boxes.values():
            box.update_style()

    def _on_fixture_selected(self, channels: list[int]) -> None:
        """Highlight the channels of the fixtures selected in the panel."""
        selected = set(channels)
        for ch, box in self.grid_area.boxes.items():
            want = ch in selected
            if box.is_panel_selected != want:
                box.is_panel_selected = want
                box.update_style()

    def _on_remove_fixtures(self, start_channels: list[int]) -> None:
        """Remove the named fixtures after one confirmation.

        One confirmation covers the whole selection: asking per fixture would
        turn removing four fixtures into four dialogs.
        """
        starts = sorted(set(start_channels))
        if not starts:
            return

        names = []
        to_clear: list[int] = []
        for row in self.get_patched_fixtures():
            if row.get("start_channel") in starts:
                names.append(row.get("name", "Fixture"))
                to_clear.extend(c["channel"] for c in row.get("channels", []))
        if not to_clear:
            return

        daftar = "\n".join(f"  - {n}" for n in names)
        jawab = QMessageBox.question(
            self,
            "Remove Fixtures",
            f"Remove {len(names)} fixture(s) from the patch?\n\n{daftar}\n\n"
            f"Channels released: {len(to_clear)}.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if jawab != QMessageBox.Yes:
            return

        self.record_undo()
        for ch in to_clear:
            box = self.grid_area.boxes.get(ch)
            if box:
                box.set_unpatched()
        self.update_fixture_brackets()
        self.patch_changed.emit()

    def _on_fixture_dropped(self, start_channel: int, fixture_data: dict,
                            record_undo: bool = True, notify: bool = True) -> bool:
        """Patch one fixture at a start channel.

        record_undo is False when a caller has already snapshotted the grid for
        a larger single user action (the quick-patch buttons), so one press is
        one undo step rather than one per fixture. notify is False for the same
        reason: emitting patch_changed per fixture made one quick-patch press
        re-run the full mixer resync four times, so the caller emits
        it once when the whole operation is done.

        Returns True when the patch was applied and False when it was refused,
        either because the range runs past the last channel or because the
        target already holds another fixture. Callers that move an existing
        fixture use the result to decide whether to release the old location.
        """
        channels = fixture_data.get("channels", [])
        if not channels:
            return False

        # Refuse a patch that would run past the last channel instead of silently keeping
        # a truncated footprint. The truncation was previously persisted to the
        # .zlx file, so a 12-channel head dropped at 250 was saved as a
        # 7-channel fixture and the rig then drove the wrong DMX offsets.
        last_channel = start_channel + len(channels) - 1
        if start_channel < 1 or last_channel > 512:
            fixture_name = fixture_data.get("name") or fixture_data.get("model", "Fixture")
            if start_channel < 1:
                detail = f"start channel {start_channel} is below 1"
            else:
                detail = (
                    f"channels {start_channel} to {last_channel} exceed the last "
                    f"DMX channel (512); the fixture needs {len(channels)} channels"
                )
            QMessageBox.warning(
                self,
                "Patch Out Of Range",
                f"{fixture_name} was not patched: {detail}.\n\n"
                "Choose a start channel that leaves room for the whole fixture.",
            )
            return False

        # Refuse a footprint that would overlap a fixture already sitting there.
        # QLC+ does the same: it rejects the drop and tells the operator why,
        # rather than letting two fixtures share channels and then driving the
        # wrong offsets. The channels of the fixture being moved are excluded so
        # it does not block its own destination. move_source_channels is read
        # from the payload because the caller releases the old location only
        # after this returns True.
        moving_from = fixture_data.get("move_source_channels")
        occupied = self._occupied_channels(exclude=set(moving_from or ()))
        clash = sorted(set(range(start_channel, last_channel + 1)) & occupied)
        if clash:
            fixture_name = fixture_data.get("name") or fixture_data.get("model", "Fixture")
            shown = ", ".join(str(ch) for ch in clash[:8])
            lebih = f" (+{len(clash) - 8} more)" if len(clash) > 8 else ""
            QMessageBox.warning(
                self,
                "Channels Already Patched",
                f"{fixture_name} was not patched: channel(s) {shown}{lebih} "
                "already belong to another fixture.\n\n"
                "Choose a free range, or clear that fixture first.",
            )
            return False

        self.grid_area.clear_drag_hover()
        if record_undo:
            self.record_undo()
        fixture_name = fixture_data.get("name") or fixture_data.get("model", "Fixture")

        for idx, ch_info in enumerate(channels):
            target_ch = start_channel + idx
            box = self.grid_area.boxes.get(target_ch)
            if box:
                ch_type = ch_info.get("type", "empty")
                label = ch_info.get("label", ch_type)
                box.set_patched(ch_type, label, fixture_name)

        self.update_fixture_brackets()
        if notify:
            self.patch_changed.emit()
        return True

    def _occupied_channels(self, exclude: set[int] | None = None) -> set[int]:
        """Channels that currently hold a patch, optionally ignoring some.

        exclude carries the channels of the fixture being moved, so they do not
        count as an obstacle to that same fixture's new position.
        """
        skip = exclude or set()
        return {
            ch for ch, box in self.grid_area.boxes.items()
            if box.is_patched and ch not in skip
        }

    def get_patched_fixtures(self) -> list[dict]:
        """Returns list of active patched fixture blocks from the address grid."""
        fixtures = []
        visited = set()
        for ch in range(1, 513):
            if ch in visited:
                continue
            box = self.grid_area.boxes.get(ch)
            if box and box.is_patched and box.fixture_name:
                fname = box.fixture_name
                start_ch = ch
                fixture_channels = []
                cur = ch
                while cur <= 512:
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
            "Confirm Clear Patch",
            "Are you sure you want to clear all DMX patches?\n\n(This action can be undone with Undo / Ctrl+Z)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.grid_area.clear_drag_hover()
            self.record_undo()
            for box in self.grid_area.boxes.values():
                box.set_unpatched()
            self.update_fixture_brackets()
            self.patch_changed.emit()

    def _on_patch_clicked(self) -> None:
        """Ask which preset to patch, then apply it.

        One button plus a chooser replaces two buttons that each committed a
        specific layout. The chooser makes the choice explicit and leaves room
        for further presets without widening the control bar.
        """
        pilihan, ok = QInputDialog.getItem(
            self,
            "Patch Preset",
            "Which fixture layout should be patched?",
            ["4x Alien AL36 (GIA stage)", "1x Kumastb STL47 (bench test)"],
            0,
            False,
        )
        if not ok:
            return
        if pilihan.startswith("4x"):
            self._on_patch_alien_gia()
        else:
            self._on_patch_kuma_bench()

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
            self._on_fixture_dropped(start_ch, fixture_data, record_undo=False, notify=False)

        self.update_fixture_brackets()
        self.patch_changed.emit()

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
        self._on_fixture_dropped(1, fixture_data, record_undo=False, notify=False)

        self.update_fixture_brackets()
        self.patch_changed.emit()

    def _on_auto_patch_default(self) -> None:
        """Legacy compatibility method pointing to Alien AL36 4x GIA setup."""
        self._on_patch_alien_gia()

"""
mixer_tab.py — grandMA3 257-Channel Industrial Console Mixer Desk
Features 1 Master Dimmer + 256 DMX channels utilizing tactile fader widgets
with illuminated groove rails, analog calibration scale marks, and smooth horizontal scrolling.
"""

from __future__ import annotations

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSplitter, Qt, Signal
)
from ui.styles import Theme
from ui.widgets.tactile_fader import TactileFader


class MixerTab(QWidget if HAS_QT else object):
    """
    Mixer Tab: 257 physical-style console faders (1 Grand Master + 256 DMX Output Channels).
    Emulates the hardware touch and lighting of grandMA3 lighting consoles.
    """
    fader_changed = Signal(int, int)  # (channel_id, value)
    blackout_triggered = Signal()

    def __init__(self, project_state=None, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.project_state = project_state
        self.faders: dict[int, TactileFader] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # Top Control Bar
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("GRANDMA3 INDUSTRIAL CONSOLE MIXER (257 FADERS)")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {Theme.TEXT_PRIMARY}; letter-spacing: 0.5px;")
        lbl_desc = QLabel("1 Grand Master Dimmer + 256 Kanal DMX Output | Rel Fader Ber-LED Menyala & Skala Kalibrasi Analog")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_reset_all = QPushButton("RESET DMX")
        self.btn_reset_all.clicked.connect(self._reset_dmx_channels)
        top_bar.addWidget(self.btn_reset_all)

        self.btn_full_master = QPushButton("FULL MASTER")
        self.btn_full_master.setStyleSheet(f"color: {Theme.ACCENT_AMBER}; border-color: {Theme.ACCENT_AMBER};")
        self.btn_full_master.clicked.connect(lambda: self.set_channel_value(0, 255))
        top_bar.addWidget(self.btn_full_master)

        self.btn_refresh = QPushButton("REFRESH")
        self.btn_refresh.clicked.connect(self.refresh_display)
        top_bar.addWidget(self.btn_refresh)

        main_layout.addLayout(top_bar)

        # Faders Container Area (Master on left, Channels scrollable on right)
        desk_container = QHBoxLayout()
        desk_container.setSpacing(10)

        # 1. Master Fader Column (Fixed, Anchored on Far Left)
        master_frame = QFrame()
        master_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SURFACE};
                border: 2px solid {Theme.ACCENT_AMBER};
                border-radius: 6px;
                padding: 4px;
            }}
        """)
        master_layout = QVBoxLayout(master_frame)
        master_layout.setContentsMargins(6, 6, 6, 6)

        lbl_m = QLabel("GRAND MASTER")
        lbl_m.setAlignment(Qt.AlignCenter)
        lbl_m.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {Theme.ACCENT_AMBER};")
        master_layout.addWidget(lbl_m)

        self.master_fader = TactileFader(channel_id=0, label="MASTER", initial_value=255, is_master=True, parent=master_frame)
        self.master_fader.valueChanged.connect(self._on_fader_value_changed)
        self.faders[0] = self.master_fader
        master_layout.addWidget(self.master_fader, 1, alignment=Qt.AlignCenter)

        desk_container.addWidget(master_frame)

        # 2. 256 DMX Channels Scroll Area (Horizontally Scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Theme.BG_ROOT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 6px;
            }}
        """)

        channels_container = QWidget()
        channels_layout = QHBoxLayout(channels_container)
        channels_layout.setContentsMargins(10, 8, 10, 8)
        channels_layout.setSpacing(6)

        # Populate 256 DMX channels
        for ch in range(1, 257):
            fader = TactileFader(channel_id=ch, label=f"Ch {ch}", initial_value=0, is_master=False, parent=channels_container)
            fader.valueChanged.connect(self._on_fader_value_changed)
            self.faders[ch] = fader
            channels_layout.addWidget(fader)

        channels_layout.addStretch()
        scroll_area.setWidget(channels_container)
        desk_container.addWidget(scroll_area, 1)

        main_layout.addLayout(desk_container, 1)

    def _on_fader_value_changed(self, ch_num: int, val: int) -> None:
        self.fader_changed.emit(ch_num, val)

    def set_channel_value(self, ch_num: int, val: int, silent: bool = False) -> None:
        """Sets a fader value programmatically."""
        fader = self.faders.get(ch_num)
        if fader:
            if silent:
                fader.set_value_silent(val)
            else:
                fader.value = val

    def apply_blackout(self) -> None:
        """Instant blackout: sets Grand Master to 0."""
        self.master_fader.value = 0

    def _reset_dmx_channels(self) -> None:
        """Sets channels 1-256 to 0 while preserving Grand Master."""
        for ch in range(1, 257):
            self.faders[ch].value = 0

    def refresh_display(self) -> None:
        for f in self.faders.values():
            f.update()

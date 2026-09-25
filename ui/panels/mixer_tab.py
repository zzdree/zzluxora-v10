"""
mixer_tab.py — 513-Channel Industrial Lighting Console Fader Desk
Inspired by grandMA3 console architecture: 1 Master Dimmer + 512 DMX Output Faders.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QSlider, QFrame, QSpinBox
    )
    from PySide6.QtCore import Qt, Signal
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

from ui.styles import Theme

class ChannelFaderWidget(QFrame if HAS_QT else object):
    """Single industrial vertical fader channel strip."""
    value_changed = Signal(int, int) if HAS_QT else None  # ch_index, value

    def __init__(self, ch_num: int, label_text: str, is_master: bool = False, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.ch_num = ch_num
        self.is_master = is_master
        self.setFixedWidth(54)

        border_color = Theme.ACCENT_CYAN if is_master else Theme.BORDER_SUBTLE
        bg_color = "#1f1824" if is_master else Theme.BG_SURFACE
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(4)

        # Channel label
        lbl_name = QLabel(label_text, self)
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_color = Theme.ACCENT_CYAN if is_master else Theme.TEXT_SECONDARY
        lbl_name.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {lbl_color};")
        layout.addWidget(lbl_name)

        # Value display spinbox
        self.spin = QSpinBox(self)
        self.spin.setRange(0, 255)
        self.spin.setValue(0)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.setButtonSymbols(QSpinBox.NoButtons)
        self.spin.setStyleSheet(f"""
            background-color: {Theme.BG_INPUT};
            border: 1px solid {Theme.BORDER_STRONG};
            color: {Theme.TEXT_PRIMARY};
            font-size: 11px;
            font-weight: bold;
        """)
        layout.addWidget(self.spin)

        # Vertical Slider
        self.slider = QSlider(Qt.Vertical, self)
        self.slider.setRange(0, 255)
        self.slider.setValue(0)
        layout.addWidget(self.slider, alignment=Qt.AlignCenter)

        # Connect signals
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, val: int):
        if HAS_QT and self.value_changed:
            self.value_changed.emit(self.ch_num, val)

    def set_value(self, val: int):
        self.slider.setValue(max(0, min(255, val)))


class MixerTab(QWidget):
    """513-Slider Console Mixer Desk (1 Master Dimmer + 512 DMX Channels)."""
    dmx_channel_changed = Signal(int, int) if HAS_QT else None

    def __init__(self, artnet_sender=None, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.artnet_sender = artnet_sender
        self.faders = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("DMX512 CONSOLE MIXER (513 CHANNELS)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        desc = QLabel("Konsol fader industrial: 1 Master Dimmer + 512 Kanal DMX Universe 0 (0-255).")
        desc.setStyleSheet("color: #abb2bf; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        self.btn_refresh = QPushButton("Refresh / Sync")
        self.btn_refresh.clicked.connect(self._on_refresh)
        header_layout.addWidget(self.btn_refresh)

        self.btn_zero = QPushButton("All Faders to 0")
        self.btn_zero.setStyleSheet("background-color: #2b0d13; border-color: #ff1744; color: #ff5252;")
        self.btn_zero.clicked.connect(self.reset_all_to_zero)
        header_layout.addWidget(self.btn_zero)

        main_layout.addLayout(header_layout)

        # Scroll Area for 513 faders
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setStyleSheet("background-color: #121417; border: 1px solid #282c34; border-radius: 6px;")

        faders_container = QWidget()
        faders_layout = QHBoxLayout(faders_container)
        faders_layout.setContentsMargins(8, 8, 8, 8)
        faders_layout.setSpacing(6)

        # 1. Master Dimmer Fader
        master_fader = ChannelFaderWidget(0, "MASTER", is_master=True, parent=faders_container)
        master_fader.set_value(255)
        master_fader.value_changed.connect(self._on_master_changed)
        faders_layout.addWidget(master_fader)
        self.faders.append(master_fader)

        # Divider line
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #3e4451;")
        faders_layout.addWidget(div)

        # 2. 512 DMX Channel Faders
        for ch in range(1, 513):
            fader = ChannelFaderWidget(ch, f"CH {ch}", is_master=False, parent=faders_container)
            fader.value_changed.connect(self._on_channel_changed)
            faders_layout.addWidget(fader)
            self.faders.append(fader)

        scroll.setWidget(faders_container)
        main_layout.addWidget(scroll)

    def _on_master_changed(self, ch_num: int, val: int):
        pass

    def _on_channel_changed(self, ch_num: int, val: int):
        if self.artnet_sender:
            self.artnet_sender.set_channel(ch_num, val)

    def reset_all_to_zero(self):
        for fader in self.faders:
            fader.set_value(0)
        if self.artnet_sender:
            self.artnet_sender.blackout()

    def _on_refresh(self):
        pass

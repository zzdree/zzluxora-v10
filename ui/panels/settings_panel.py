"""
settings_panel.py — Application Audio Hardware & Preferences Panel
Configures audio input device, sampling buffer size, and DMX universe timing.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QComboBox, QSpinBox, QGroupBox, QCheckBox
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

class SettingsPanel(QWidget):
    """Audio Device & App Preferences Panel."""
    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        title = QLabel("PENGATURAN PERANGKAT & PREFERENSI SISTEM")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        main_layout.addWidget(title)

        # Audio Config
        audio_group = QGroupBox("Konfigurasi Audio Driver")
        a_layout = QVBoxLayout(audio_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Audio Output Device:"))
        self.combo_audio = QComboBox()
        self.combo_audio.addItems(["Default System Audio", "ALSA / PulseAudio (Linux Mint)", "WASAPI Audio Output (Windows 11)"])
        row1.addWidget(self.combo_audio)
        a_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Sampling Rate Analisis:"))
        self.combo_fs = QComboBox()
        self.combo_fs.addItems(["22.050 Hz (Standar MIR & Librosa - Nyquist 11.025 Hz)", "44.100 Hz (High Resolution)"])
        row2.addWidget(self.combo_fs)
        a_layout.addLayout(row2)

        main_layout.addWidget(audio_group)

        # DMX Timing Config
        dmx_group = QGroupBox("Konfigurasi Parameter Transmisi DMX & Art-Net")
        d_layout = QVBoxLayout(dmx_group)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Target Output Refresh Rate (FPS):"))
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(20, 60)
        self.spin_fps.setValue(44)
        row3.addWidget(self.spin_fps)
        d_layout.addLayout(row3)

        self.chk_failsafe = QCheckBox("Aktifkan Proteksi Fail-Safe Auto-Blackout jika sinyal hilang > 10 detik")
        self.chk_failsafe.setChecked(True)
        d_layout.addWidget(self.chk_failsafe)

        main_layout.addWidget(dmx_group)
        main_layout.addStretch()

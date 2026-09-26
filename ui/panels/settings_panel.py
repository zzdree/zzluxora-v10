"""
settings_panel.py — Standalone Network & Art-Net Configuration Dialog
Provides automatic interface scanning and mandatory presets: 127.0.0.1 (SITL QLC+),
192.168.4.1 (ESP32 AP mode), and Custom IP with Port 6454 & Universe 1 configuration.
"""

from __future__ import annotations
import socket

from ui.qt_compat import (
    HAS_QT, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, Qt, Signal
)
from ui.styles import Theme, CONSOLE_QSS


class SettingsDialog(QDialog if HAS_QT else object):
    """Network & Art-Net configuration dialog for ZZLUXORA."""
    settings_saved = Signal(str, int, int)  # (ip, port, universe)

    def __init__(self, current_ip: str = "127.0.0.1", current_universe: int = 0, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Pengaturan Jaringan & Art-Net — ZZLUXORA")
        self.resize(560, 460)
        self.setStyleSheet(CONSOLE_QSS)

        self.current_ip = current_ip
        self.current_universe = current_universe
        self._init_ui()
        self._scan_network_interfaces()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # Header Title
        title_box = QVBoxLayout()
        lbl_title = QLabel("KONFIGURASI JARINGAN ART-NET DMX512")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        lbl_desc = QLabel("Pilih target IP penerima paket DMX (Simulasi SITL QLC+ atau Modul Hardware ESP32).")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        main_layout.addLayout(title_box)

        # Preset IP Selector
        grp_target = QGroupBox("Target Penerima Paket Art-Net")
        grp_target.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        target_layout = QVBoxLayout(grp_target)
        target_layout.setSpacing(10)

        row_preset = QHBoxLayout()
        row_preset.addWidget(QLabel("Preset Target IP:"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItem("127.0.0.1 (Localhost — Loopback SITL QLC+ v4 / v5)", "127.0.0.1")
        self.combo_presets.addItem("192.168.4.1 (ESP32 Hardware — SoftAP Mode Gateway)", "192.168.4.1")
        self.combo_presets.addItem("Custom IP (Input Manual Venue / Gereja)", "custom")
        self.combo_presets.currentIndexChanged.connect(self._on_preset_changed)
        row_preset.addWidget(self.combo_presets, 1)
        target_layout.addLayout(row_preset)

        row_ip = QHBoxLayout()
        row_ip.addWidget(QLabel("Alamat IP Tujuan:"))
        self.txt_ip = QLineEdit(self.current_ip)
        row_ip.addWidget(self.txt_ip, 1)

        row_ip.addWidget(QLabel("Port UDP:"))
        self.spin_port = QSpinBox()
        self.spin_port.setRange(1024, 65535)
        self.spin_port.setValue(6454)
        row_ip.addWidget(self.spin_port)
        target_layout.addLayout(row_ip)

        row_uni = QHBoxLayout()
        row_uni.addWidget(QLabel("DMX Universe:"))
        self.spin_universe = QSpinBox()
        self.spin_universe.setRange(0, 15)
        self.spin_universe.setValue(self.current_universe)
        row_uni.addWidget(self.spin_universe)

        row_uni.addWidget(QLabel("Laju Frame (FPS):"))
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(20, 60)
        self.spin_fps.setValue(44)
        row_uni.addWidget(self.spin_fps)
        target_layout.addLayout(row_uni)

        main_layout.addWidget(grp_target)

        # Scanned Local Adapters Table
        grp_adapters = QGroupBox("Adapter Jaringan Lokal Terdeteksi")
        grp_adapters.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        adap_layout = QVBoxLayout(grp_adapters)

        self.table_adapters = QTableWidget(0, 2)
        self.table_adapters.setHorizontalHeaderLabels(["Nama Interface / Host", "Alamat IP Lokal"])
        self.table_adapters.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_adapters.verticalHeader().setVisible(False)
        adap_layout.addWidget(self.table_adapters)

        main_layout.addWidget(grp_adapters, 1)

        # Bottom Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.btn_rescan = QPushButton("SCAN INTERFACES")
        self.btn_rescan.clicked.connect(self._scan_network_interfaces)
        btn_bar.addWidget(self.btn_rescan)

        self.btn_save = QPushButton("SAVE")
        self.btn_save.setStyleSheet(f"background-color: #143521; color: {Theme.COLOR_SUCCESS}; font-weight: bold;")
        self.btn_save.clicked.connect(self._on_save_clicked)
        btn_bar.addWidget(self.btn_save)

        self.btn_close = QPushButton("CANCEL")
        self.btn_close.clicked.connect(self.close)
        btn_bar.addWidget(self.btn_close)

        main_layout.addLayout(btn_bar)

    def _scan_network_interfaces(self) -> None:
        self.table_adapters.setRowCount(0)
        adapters = [("Local Loopback (SITL)", "127.0.0.1")]
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            adapters.append((f"Host ({hostname})", local_ip))
        except Exception:
            pass

        self.table_adapters.setRowCount(len(adapters))
        for row, (name, ip) in enumerate(adapters):
            it1 = QTableWidgetItem(name)
            it2 = QTableWidgetItem(ip)
            it1.setForeground(Theme.TEXT_PRIMARY)
            it2.setForeground(Theme.ACCENT_CYAN)
            self.table_adapters.setItem(row, 0, it1)
            self.table_adapters.setItem(row, 1, it2)

    def _on_preset_changed(self, index: int) -> None:
        val = self.combo_presets.currentData()
        if val != "custom":
            self.txt_ip.setText(val)
            self.txt_ip.setEnabled(False)
        else:
            self.txt_ip.setEnabled(True)
            self.txt_ip.setFocus()

    def _on_save_clicked(self) -> None:
        target_ip = self.txt_ip.text().strip()
        port = self.spin_port.value()
        uni = self.spin_universe.value()

        if not target_ip:
            QMessageBox.warning(self, "IP Kosong", "Alamat IP target tidak boleh kosong.")
            return

        self.settings_saved.emit(target_ip, port, uni)
        QMessageBox.information(
            self,
            "Konfigurasi Tersimpan",
            f"Target Art-Net berhasil diperbarui ke:\nIP: {target_ip}:{port} (Universe {uni})",
        )
        self.accept()

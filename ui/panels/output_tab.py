"""
output_tab.py — Art-Net 4 Network Destination and Node Output Manager
Configures target IP (Localhost, ESP32 AP Mode 192.168.4.1, Custom IP) on UDP Port 6454.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QRadioButton, QButtonGroup, QLineEdit, QGroupBox, QMessageBox
    )
    from PySide6.QtCore import Signal
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

class OutputTab(QWidget):
    """Art-Net Network Output Settings Tab."""
    output_configured = Signal(str) if HAS_QT else None

    def __init__(self, artnet_sender=None, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.artnet_sender = artnet_sender
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Title
        title_box = QVBoxLayout()
        title = QLabel("ART-NET 4 OUTPUT NETWORK MANAGER")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e5ff;")
        desc = QLabel("Pengaturan alamat IP tujuan paket UDP datagram DMX512 (Port 6454, Universe 0).")
        desc.setStyleSheet("color: #abb2bf; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        main_layout.addLayout(title_box)

        # Options Box
        group = QGroupBox("Pilihan Alamat IP Tujuan Art-Net")
        grp_layout = QVBoxLayout(group)
        grp_layout.setSpacing(12)

        self.btn_group = QButtonGroup(self)

        self.rb_localhost = QRadioButton("Localhost (127.0.0.1) — Simulasi Software QLC+ / Capture")
        self.rb_esp32_ap = QRadioButton("ESP32 ARTNET-DMX Node (192.168.4.1) — Mode Access Point Fisik")
        self.rb_custom = QRadioButton("Custom Network IP (Jaringan WiFi Lokal Ruang Ibadah):")

        self.rb_esp32_ap.setChecked(True)

        self.btn_group.addButton(self.rb_localhost, 1)
        self.btn_group.addButton(self.rb_esp32_ap, 2)
        self.btn_group.addButton(self.rb_custom, 3)

        grp_layout.addWidget(self.rb_localhost)
        grp_layout.addWidget(self.rb_esp32_ap)
        grp_layout.addWidget(self.rb_custom)

        # Custom IP Input
        custom_layout = QHBoxLayout()
        custom_layout.setContentsMargins(24, 0, 0, 0)
        self.txt_custom_ip = QLineEdit("192.168.1.100")
        self.txt_custom_ip.setPlaceholderText("Masukkan alamat IP target (misal: 192.168.1.150)")
        self.txt_custom_ip.setEnabled(False)
        custom_layout.addWidget(self.txt_custom_ip)
        grp_layout.addLayout(custom_layout)

        self.rb_custom.toggled.connect(self.txt_custom_ip.setEnabled)

        main_layout.addWidget(group)

        # Protocol Details Box
        proto_group = QGroupBox("Detail Protokol Fisik")
        proto_layout = QVBoxLayout(proto_group)
        proto_layout.addWidget(QLabel("• Protokol Transmisi: Art-Net 4 (ArtDmx OpOutput 0x5000)"))
        proto_layout.addWidget(QLabel("• Port Jaringan: UDP 6454"))
        proto_layout.addWidget(QLabel("• Universe DMX: Universe 0 (Sub-Net 0, Net 0)"))
        proto_layout.addWidget(QLabel("• Laju Frame: 43.07 FPS (Sinkron STFT H=512 & Standar DMX512-A)"))
        main_layout.addWidget(proto_group)

        # Save Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("Simpan Konfigurasi Output")
        self.btn_save.setStyleSheet("background-color: #0b3d36; border-color: #00e5ff; color: #00e5ff; font-weight: bold; padding: 8px 24px;")
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)
        main_layout.addLayout(btn_layout)

        main_layout.addStretch()

    def _on_save(self):
        if not HAS_QT: return
        target_ip = "192.168.4.1"
        if self.rb_localhost.isChecked():
            target_ip = "127.0.0.1"
        elif self.rb_esp32_ap.isChecked():
            target_ip = "192.168.4.1"
        elif self.rb_custom.isChecked():
            target_ip = self.txt_custom_ip.text().strip()

        if self.artnet_sender:
            self.artnet_sender.target_ip = target_ip

        if self.output_configured:
            self.output_configured.emit(target_ip)

        QMessageBox.information(
            self, "Konfigurasi Disimpan",
            f"Alamat IP Art-Net berhasil diperbarui ke: {target_ip}:6454"
        )

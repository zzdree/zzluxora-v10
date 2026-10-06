"""
settings_panel.py — Standalone Network & Art-Net Configuration Dialog
Provides automatic interface scanning and presets: 127.0.0.1 (SITL QLC+),
192.168.4.1 (ESP32 AP mode), and Custom IP with UDP Port & Universe 0-3 configuration.
"""

from __future__ import annotations
import socket
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, Qt, Signal, QColor, QIcon
)
from ui.styles import Theme, CONSOLE_QSS


class SettingsDialog(QDialog if HAS_QT else object):
    """Network & Art-Net configuration dialog for ZZLUXORA."""
    settings_saved = Signal(str, int, int)  # (ip, port, universe)

    def __init__(self, current_ip: str = "127.0.0.1", current_universe: int = 0, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Settings")
        self.resize(540, 440)
        self.setStyleSheet(CONSOLE_QSS)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_zz.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self.current_ip = current_ip
        self.current_universe = current_universe
        self._init_ui()
        self._scan_network_interfaces()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(10)

        # Target Configuration Group
        grp_target = QGroupBox("Target")
        grp_target.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        target_layout = QVBoxLayout(grp_target)
        target_layout.setSpacing(8)

        # Preset Row
        row_preset = QHBoxLayout()
        lbl_preset = QLabel("Preset:")
        lbl_preset.setFixedWidth(80)
        lbl_preset.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        row_preset.addWidget(lbl_preset)

        self.combo_presets = QComboBox()
        self.combo_presets.addItem("127.0.0.1 - Localhost (SITL QLC+)", "127.0.0.1")
        self.combo_presets.addItem("192.168.4.1 - ESP32 AP Mode", "192.168.4.1")
        self.combo_presets.addItem("255.255.255.255 - Subnet Broadcast", "255.255.255.255")
        self.combo_presets.addItem("Custom IP", "custom")
        self.combo_presets.currentIndexChanged.connect(self._on_preset_changed)
        row_preset.addWidget(self.combo_presets, 1)
        target_layout.addLayout(row_preset)

        # IP Address & UDP Port Row
        row_ip = QHBoxLayout()
        lbl_ip = QLabel("IP Address:")
        lbl_ip.setFixedWidth(80)
        lbl_ip.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        row_ip.addWidget(lbl_ip)

        self.txt_ip = QLineEdit(self.current_ip)
        self.txt_ip.setStyleSheet(f"background-color: {Theme.BG_INPUT}; border: 1px solid {Theme.BORDER_STRONG}; color: #ffffff;")
        row_ip.addWidget(self.txt_ip, 1)

        lbl_port = QLabel("UDP Port:")
        lbl_port.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        row_ip.addWidget(lbl_port)

        self.spin_port = QSpinBox()
        self.spin_port.setRange(1024, 65535)
        self.spin_port.setValue(6454)
        self.spin_port.setFixedWidth(75)
        self.spin_port.setStyleSheet(f"background-color: {Theme.BG_INPUT}; border: 1px solid {Theme.BORDER_STRONG}; color: #ffffff;")
        row_ip.addWidget(self.spin_port)
        target_layout.addLayout(row_ip)

        # DMX Universe (0-3) & FPS Row
        row_uni = QHBoxLayout()
        lbl_uni = QLabel("Universe:")
        lbl_uni.setFixedWidth(80)
        lbl_uni.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        row_uni.addWidget(lbl_uni)

        self.combo_universe = QComboBox()
        self.combo_universe.addItem("0", 0)
        self.combo_universe.addItem("1", 1)
        self.combo_universe.addItem("2", 2)
        self.combo_universe.addItem("3", 3)
        # Select matching universe (0-3)
        uni_idx = min(3, max(0, self.current_universe))
        self.combo_universe.setCurrentIndex(uni_idx)
        self.combo_universe.setFixedWidth(70)
        row_uni.addWidget(self.combo_universe)

        row_uni.addSpacing(20)
        lbl_fps = QLabel("FPS:")
        lbl_fps.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        row_uni.addWidget(lbl_fps)

        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(20, 60)
        self.spin_fps.setValue(44)
        self.spin_fps.setFixedWidth(70)
        self.spin_fps.setStyleSheet(f"background-color: {Theme.BG_INPUT}; border: 1px solid {Theme.BORDER_STRONG}; color: #ffffff;")
        row_uni.addWidget(self.spin_fps)

        row_uni.addStretch()
        target_layout.addLayout(row_uni)

        main_layout.addWidget(grp_target)

        # Scanned Interfaces Table
        grp_adapters = QGroupBox("Scanned Interfaces")
        grp_adapters.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        adap_layout = QVBoxLayout(grp_adapters)
        adap_layout.setContentsMargins(10, 10, 10, 10)

        self.table_adapters = QTableWidget(0, 2)
        self.table_adapters.setHorizontalHeaderLabels(["Name", "Address"])
        self.table_adapters.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_adapters.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_adapters.verticalHeader().setVisible(False)
        self.table_adapters.cellDoubleClicked.connect(self._on_adapter_selected)
        self.table_adapters.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_ELEVATED};
                color: {Theme.TEXT_PRIMARY};
                font-weight: 700;
                padding: 4px;
                border: 1px solid {Theme.BORDER_SUBTLE};
            }}
        """)
        adap_layout.addWidget(self.table_adapters)

        main_layout.addWidget(grp_adapters, 1)

        # Bottom Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.btn_rescan = QPushButton("Scan Interfaces")
        self.btn_rescan.setStyleSheet("padding: 6px 14px; border-radius: 4px;")
        self.btn_rescan.clicked.connect(self._scan_network_interfaces)
        btn_bar.addWidget(self.btn_rescan)

        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet("background-color: #16a34a; color: #ffffff; font-weight: bold; min-width: 80px; padding: 6px 14px; border-radius: 4px; border: none;")
        self.btn_save.clicked.connect(self._on_save_clicked)
        btn_bar.addWidget(self.btn_save)

        self.btn_close = QPushButton("Cancel")
        self.btn_close.setStyleSheet("min-width: 80px; padding: 6px 14px; border-radius: 4px;")
        self.btn_close.clicked.connect(self.close)
        btn_bar.addWidget(self.btn_close)

        main_layout.addLayout(btn_bar)

    def _scan_network_interfaces() -> None:
        pass

    def _scan_network_interfaces(self) -> None:
        self.table_adapters.setRowCount(0)
        adapters = [("Local Loopback (SITL QLC+)", "127.0.0.1")]
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
            s.close()
            adapters.append(("Active Wi-Fi / LAN Adapter", lan_ip))
            parts = lan_ip.split(".")
            if len(parts) == 4:
                bcast_ip = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
                adapters.append(("Subnet Broadcast (Auto ESP32)", bcast_ip))
        except Exception:
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
            it1.setForeground(QColor(Theme.TEXT_PRIMARY))
            it2.setForeground(QColor(Theme.ACCENT_CYAN))
            self.table_adapters.setItem(row, 0, it1)
            self.table_adapters.setItem(row, 1, it2)

    def _on_adapter_selected(self, row: int, col: int) -> None:
        item = self.table_adapters.item(row, 1)
        if item:
            ip = item.text().strip()
            self.combo_presets.setCurrentIndex(self.combo_presets.count() - 1)  # Custom IP
            self.txt_ip.setText(ip)

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
        if not target_ip:
            QMessageBox.warning(self, "Invalid IP", "Please specify a valid target IP address.")
            return

        port = self.spin_port.value()
        universe = self.combo_universe.currentData()
        if universe is None:
            universe = int(self.combo_universe.currentText())

        self.settings_saved.emit(target_ip, port, universe)
        self.accept()

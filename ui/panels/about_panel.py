"""
about_panel.py — Academic Information and Author Credentials
Presents research identity, thesis title, university credentials, and advisor information.
"""

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

class AboutPanel(QWidget):
    """About Panel: Academic Thesis Metadata & Software Credentials."""
    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        title = QLabel("TENTANG SISTEM ZZLUXORA")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00e5ff;")
        main_layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet("background-color: #16181d; border: 1px solid #282c34; border-radius: 8px; padding: 16px;")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        fields = [
            ("1. Application", "ZZLUXORA (v10.0.0 Production Stage Lighting Console)"),
            ("2. Deskripsi", "Sistem Audio-Reactive Lighting Design Berbasis Analisis Mood Lagu Rohani dengan Pemetaan Warna HSV-RGBW dan Protokol Art-Net DMX512"),
            ("3. Author", "Andreas Restuawanta Christwara"),
            ("4. NIM", "5312422036"),
            ("5. Program Studi", "S1 Teknik Komputer"),
            ("6. Jurusan", "Teknik Elektro"),
            ("7. Fakultas", "Fakultas Teknik"),
            ("8. Universitas", "Universitas Negeri Semarang (UNNES)"),
            ("9. Dosen Pembimbing", "Mario Norman Syah, S.Pd., M.Eng. (NIP: 199304212024061001)"),
            ("10. Judul Skripsi", "Rancang Bangun Sistem Audio-Reactive Lighting Design Berbasis Analisis Mood Lagu Rohani dengan Pemetaan Warna HSV-RGBW dan Protokol Art-Net DMX512"),
            ("11. Lokasi Pengujian", "Gereja GIA Deliksari, Kota Semarang")
        ]

        for label_text, val_text in fields:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(160)
            lbl.setStyleSheet("font-weight: bold; color: #abb2bf; font-size: 13px;")

            val = QLabel(val_text)
            val.setWordWrap(True)
            val.setStyleSheet("color: #ffffff; font-size: 13px;")

            row.addWidget(lbl)
            row.addWidget(val)
            card_layout.addLayout(row)

        main_layout.addWidget(card)
        main_layout.addStretch()

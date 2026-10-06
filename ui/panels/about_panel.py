"""
about_panel.py — Academic Thesis Information & Software Credentials Dialog
Presents official student credentials, advisor information, UNNES affiliation, and research title.
"""

from __future__ import annotations
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QPixmap, QIcon, Qt
)
from ui.styles import Theme, CONSOLE_QSS


class AboutDialog(QDialog if HAS_QT else object):
    """About Dialog: Academic Thesis Metadata & Software Credentials."""
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("About Developer & System — ZZLUXORA")
        self.resize(620, 520)
        self.setStyleSheet(CONSOLE_QSS)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_zz.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 20, 22, 20)
        main_layout.setSpacing(14)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_zz.png"

        # Header Row (Official Logo Badge + Title)
        header_row = QHBoxLayout()
        header_row.setSpacing(14)
        if logo_path.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(logo_path)).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setFixedSize(48, 48)
            logo_lbl.setStyleSheet("border-radius: 4px; background: #000000;")
            header_row.addWidget(logo_lbl)

        # Header Title
        title_box = QVBoxLayout()
        title = QLabel("ABOUT ZZLUXORA v10")
        title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        subtitle = QLabel("Intelligent Audio-Reactive Stage Lighting Controller • Computer Engineering FT UNNES")
        subtitle.setStyleSheet(f"font-size: 11px; color: {Theme.ACCENT_CYAN};")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        # Card
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        fields = [
            ("1. Application", "ZZLUXORA (v10.0.0 Next-Gen Production Stage Console)"),
            ("2. Description", "Audio-Reactive Stage Lighting Design System based on Worship Music Mood Analysis with HSV-RGBW Color Mapping and Art-Net DMX512 Protocol"),
            ("3. Author / Researcher", "Andreas Restuawanta Christwara"),
            ("4. Student ID (NIM)", "5312422036"),
            ("5. Study Program", "Computer Engineering (S1)"),
            ("6. Department", "Electrical Engineering"),
            ("7. Faculty", "Faculty of Engineering"),
            ("8. University", "Universitas Negeri Semarang (UNNES)"),
            ("9. Thesis Advisor", "Mario Norman Syah, S.Pd., M.Eng. (NIP: 199304212024061001)"),
            ("10. Research Title", "Rancang Bangun Sistem Audio-Reactive Lighting Design Berbasis Analisis Mood Lagu Rohani dengan Pemetaan Warna HSV-RGBW dan Protokol Art-Net DMX512"),
            ("11. Field Location", "Gereja Isa Almasih (GIA) Deliksari, Semarang"),
        ]

        for label_text, val_text in fields:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(150)
            lbl.setStyleSheet(f"font-weight: 700; color: {Theme.TEXT_SECONDARY}; font-size: 12px;")

            val = QLabel(val_text)
            val.setWordWrap(True)
            val.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 12px;")

            row.addWidget(lbl)
            row.addWidget(val, 1)
            card_layout.addLayout(row)

        main_layout.addWidget(card, 1)

        # Bottom Close Button
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_bar.addWidget(btn_close)
        main_layout.addLayout(btn_bar)

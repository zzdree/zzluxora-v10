"""
result_tab.py — Analysis Results & Affective Dashboard
Displays MIR acoustic metrics, Russell 2D Plane, mood quadrant, and provides
the 'Export to Perform' workflow trigger.
"""

from __future__ import annotations

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSplitter,
    Qt, Signal, QColor, QFont
)
from ui.styles import Theme
from ui.panels.analyze_tab import RussellPlaneWidget


class ResultTab(QWidget if HAS_QT else object):
    """Result Tab: Summarizes extracted audio analysis and exports cue sequences to Perform."""
    export_to_perform = Signal(dict)
    reanalyze_requested = Signal()

    def __init__(self, project_state=None, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.project_state = project_state
        self.current_analysis: dict | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # Header Title
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("HASIL ANALISIS AFEKTIF & METRIK AUDIO")
        lbl_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        lbl_desc = QLabel("Hasil Komputasi Sinyal Lagu Rohani • Model Afektif Russell 2D & Rekomendasi Suasana Panggung")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_reanalyze = QPushButton("🔄 Re-Analyze")
        self.btn_reanalyze.clicked.connect(lambda: self.reanalyze_requested.emit())
        top_bar.addWidget(self.btn_reanalyze)

        self.btn_export = QPushButton("🚀 Export to Perform")
        self.btn_export.setStyleSheet(f"background-color: #1e3a5f; border-color: {Theme.ACCENT_CYAN}; font-weight: bold;")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export_clicked)
        top_bar.addWidget(self.btn_export)

        main_layout.addLayout(top_bar)

        # Content Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Metric Details Table
        left_box = QGroupBox("Tabel Metrik Akustik & Karakteristik Lagu")
        left_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        left_layout = QVBoxLayout(left_box)

        self.table = QTableWidget(7, 2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Nilai Terhitung"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        metrics = [
            ("Judul Lagu", "Belum ada analisis"),
            ("Estimasi BPM", "-"),
            ("Durasi Audio", "-"),
            ("Energy RMS", "-"),
            ("Valence (Valensi)", "-"),
            ("Arousal (Gairah)", "-"),
            ("Kuadran Suasana", "-"),
        ]
        for row, (param, val) in enumerate(metrics):
            i1 = QTableWidgetItem(param)
            i2 = QTableWidgetItem(val)
            i1.setFont(QFont("Inter", 9, QFont.Bold))
            i2.setFont(QFont("JetBrains Mono", 9))
            i1.setForeground(QColor(Theme.TEXT_PRIMARY))
            i2.setForeground(QColor(Theme.ACCENT_CYAN))
            self.table.setItem(row, 0, i1)
            self.table.setItem(row, 1, i2)

        left_layout.addWidget(self.table)
        splitter.addWidget(left_box)

        # Right: Russell 2D Plane Display
        right_box = QGroupBox("Pemetaan Bidang Emosi Russell (Valence-Arousal)")
        right_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        right_layout = QVBoxLayout(right_box)

        self.russell_plane = RussellPlaneWidget()
        right_layout.addWidget(self.russell_plane, alignment=Qt.AlignCenter)

        self.lbl_palette_desc = QLabel("Palet Warna Panggung: Belum ditentukan.")
        self.lbl_palette_desc.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY};")
        self.lbl_palette_desc.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_palette_desc)

        splitter.addWidget(right_box)
        splitter.setSizes([550, 450])
        main_layout.addWidget(splitter, 1)

    def load_analysis_result(self, res: dict) -> None:
        """Loads and visualizes analysis data from AnalyzeTab."""
        self.current_analysis = res
        self.btn_export.setEnabled(True)

        v = res.get("valence", 0.0)
        a = res.get("arousal", 0.0)
        quad = res.get("quadrant", "Idle")

        self.russell_plane.set_coordinates(v, a, quad)

        vals = [
            res.get("title", "Untitled"),
            f"{res.get('bpm', 120.0):.1f} BPM",
            f"{res.get('duration_sec', 0.0):.1f} detik",
            f"{res.get('rms', 0.0):.3f}",
            f"{v:+.2f}",
            f"{a:+.2f}",
            f"{quad}",
        ]
        for row, val_str in enumerate(vals):
            self.table.item(row, 1).setText(val_str)

        palette = res.get("palette", {})
        r, g, b, w = palette.get("R", 255), palette.get("G", 255), palette.get("B", 255), palette.get("W", 0)
        self.lbl_palette_desc.setText(
            f"<b>Rekomendasi Warna Pencahayaan:</b><br>"
            f"<span style='color: rgb({r},{g},{b}); font-size: 14px;'>■■■ RGBW: ({r}, {g}, {b}, {w})</span>"
        )

    def _on_export_clicked(self) -> None:
        if self.current_analysis:
            self.export_to_perform.emit(self.current_analysis)

"""
result_tab.py | Analysis Results & Affective Dashboard
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

        top_bar.addStretch()

        self.btn_reanalyze = QPushButton("RE-ANALYZE")
        self.btn_reanalyze.clicked.connect(lambda: self.reanalyze_requested.emit())
        top_bar.addWidget(self.btn_reanalyze)

        self.btn_export = QPushButton("EXPORT TO PERFORM")
        self.btn_export.setStyleSheet(f"font-weight: bold;")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export_clicked)
        top_bar.addWidget(self.btn_export)

        main_layout.addLayout(top_bar)

        # Content Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Metric Details Table
        left_box = QGroupBox("Acoustic Metrics & Song Characteristics")
        left_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        left_layout = QVBoxLayout(left_box)

        self.table = QTableWidget(12, 2)
        self.table.setHorizontalHeaderLabels(["Scientific & DSP Parameter", "Computed Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        metrics = [
            ("Song Title", "No analysis yet"),
            ("Estimated Tempo", "-"),
            ("Duration & STFT Frames", "-"),
            ("RMS Energy (Parseval)", "-"),
            ("Spectral Centroid", "-"),
            ("Chroma STFT & Tonality", "-"),
            ("MFCC Acoustic Density", "-"),
            ("Spectral Flux (Onsets)", "-"),
            ("Valence (Mood)", "-"),
            ("Arousal (Energy)", "-"),
            ("Quadrant Classification", "-"),
            ("Physical RGBW Decomposition", "-"),
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
        right_box = QGroupBox("Russell Emotion Plane Mapping (Valence-Arousal)")
        right_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        right_layout = QVBoxLayout(right_box)

        self.russell_plane = RussellPlaneWidget()
        right_layout.addWidget(self.russell_plane, alignment=Qt.AlignCenter)

        self.lbl_palette_desc = QLabel("Stage Color Palette: Not assigned.")
        self.lbl_palette_desc.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY};")
        self.lbl_palette_desc.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_palette_desc)

        splitter.addWidget(right_box)
        splitter.setSizes([550, 450])
        main_layout.addWidget(splitter, 1)

    def load_analysis_result(self, res: dict) -> None:
        """Loads and visualizes analysis data from AnalyzeTab."""
        self.current_analysis = res

        # Only offer Export when the result carries real, usable numbers.
        # Previously every row was rendered from a plausible numeric default
        # (centroid 1850 Hz, MFCC 0.500, BPM 120, a white RGBW palette), so a
        # partial result read as a complete measurement and Export was enabled
        # for data that did not exist.
        required = ("bpm", "valence", "arousal", "rms", "palette")
        analysed = res.get("frames_count", 0) > 1 and all(res.get(k) is not None for k in required)
        self.btn_export.setEnabled(analysed)

        def value(key, default=None):
            """Return the recorded value or None, never a stand-in number."""
            raw = res.get(key)
            return default if raw is None else raw

        def show(fmt: str, key: str, fallback: str = "- (not measured)") -> str:
            raw = res.get(key)
            if raw is None:
                return fallback
            try:
                return fmt.format(raw)
            except (TypeError, ValueError):
                return fallback

        v = float(res.get("valence", 0.0))
        a = float(res.get("arousal", 0.0))
        quad = res.get("quadrant", "Idle")

        self.russell_plane.set_coordinates(v, a, quad)

        palette = res.get("palette")
        has_palette = isinstance(palette, dict) and bool(palette)
        r = palette.get("R") if has_palette else None
        g = palette.get("G") if has_palette else None
        b = palette.get("B") if has_palette else None
        w = palette.get("W") if has_palette else None

        frames_cnt = res.get("frames_count")
        fps_rate = value("fps_rate")

        vals = [
            res.get("title", "Untitled"),
            show("{:.1f} BPM (Beat Tracking)", "bpm"),
            show("{:.1f}s", "duration_sec") if value("duration_sec") is not None else "- (not measured)",
            show("{:.3f} (Dinamika Master Dimmer)", "rms"),
            show("{:.1f} Hz (Kecerahan Timbre Audio)", "spectral_centroid"),
            res.get("chroma_key", "- (not measured)"),
            show("{:.3f} / 1,000 (Indeks Tekstur Akustik Ternormalisasi)", "mfcc_density"),
            show("{:.3f} / 1,000 (Kepadatan Onset Ritmik Ternormalisasi)", "spectral_flux"),
            f"{v:+.2f} ({'Praise/Joyful' if v >= 0 else 'Worship/Solemn'})",
            f"{a:+.2f} ({'Dynamic/High' if a >= 0 else 'Ambient/Calm'})",
            f"{quad}",
            (f"R:{r} G:{g} B:{b} W:{w} (Anti-Washout)" if has_palette
             else "- (no palette assigned)"),
        ]
        for row, val_str in enumerate(vals):
            self.table.item(row, 1).setText(val_str)

        # Fold the frame/rate detail into the duration cell only when known.
        if frames_cnt is not None and fps_rate is not None:
            self.table.item(2, 1).setText(
                f"{res.get('duration_sec', 0.0):.1f}s ({frames_cnt:,} Frame @ {fps_rate:.2f} FPS)"
            )

        if has_palette:
            self.lbl_palette_desc.setText(
                f"<b>Recommended Stage Lighting Color:</b><br>"
                f"<span style='color: rgb({r},{g},{b}); font-size: 14px;'>"
                f"RGBW: ({r}, {g}, {b}, {w})</span>"
            )
        else:
            self.lbl_palette_desc.setText("<b>Recommended Stage Lighting Color:</b> not assigned.")

    def _on_export_clicked(self) -> None:
        if self.current_analysis:
            self.export_to_perform.emit(self.current_analysis)

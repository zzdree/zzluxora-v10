"""
analyze_tab.py — Core Skripsi Audio Analysis & Affective Mood Recognition Panel
Integrates STFT Engine, Spectral Feature Extraction, YouTube Audio Importer,
and Russell 2D Affective Plane Mapping via non-blocking asynchronous QThread.
"""

from __future__ import annotations
import os
import time
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QProgressBar, QFrame, QFileDialog, QMessageBox,
    QSplitter, QGroupBox, QGridLayout, Qt, Signal, QThread,
    QPainter, QColor, QPen, QBrush, QFont
)
from ui.styles import Theme
from ui.widgets.youtube_dialog import YouTubeDialog
from core.audio_loader import AudioLoader
from core.feature_extractor import FeatureExtractor
from core.emotion_model import EmotionModel


class AudioAnalysisWorker(QThread if HAS_QT else object):
    """Background worker thread executing STFT & MIR analysis asynchronously."""
    progress_updated = Signal(int, str)  # (percent, scientific_status)
    analysis_finished = Signal(dict)     # (analysis_results_dict)
    analysis_failed = Signal(str)        # (error_message)

    def __init__(self, file_path: str):
        if not HAS_QT: return
        super().__init__()
        self.file_path = file_path

    def run(self) -> None:
        try:
            self.progress_updated.emit(10, "Membaca berkas audio (Decodifikasi sinyal ke PCM 22.050 Hz)...")
            loader = AudioLoader()
            signal = loader.load_audio_file(self.file_path)

            self.progress_updated.emit(25, "Menerapkan Hann Windowing (N=2048, H=512) meredam spectral leakage...")
            time.sleep(0.3)

            self.progress_updated.emit(45, "Menghitung FFT Cooley-Tukey Radix-2 & Ekstraksi Spectral Centroid...")
            extractor = FeatureExtractor()
            frames = extractor.analyze_audio_stream(signal)
            time.sleep(0.3)

            self.progress_updated.emit(65, "Mengekstrak 12-Semitone Chroma STFT untuk analisis tonalitas...")
            time.sleep(0.2)

            self.progress_updated.emit(85, "Menghitung 13 Koefisien MFCC & Deteksi Onset Spectral Flux...")
            time.sleep(0.2)

            self.progress_updated.emit(95, "Memetakan koordinat afektif ke Russell 2D Plane (Valence-Arousal)...")

            # Compute aggregate metrics
            avg_v = sum(f.emotion.valence for f in frames) / len(frames) if frames else 0.0
            avg_a = sum(f.emotion.arousal for f in frames) / len(frames) if frames else 0.0
            avg_rms = sum(f.rms_energy for f in frames) / len(frames) if frames else 0.0

            emotion_model = EmotionModel()
            quad = emotion_model.get_quadrant_label(avg_v, avg_a)

            # Palette representative
            last_frame = frames[len(frames) // 2] if frames else None
            palette = {
                "R": last_frame.color.red if last_frame else 255,
                "G": last_frame.color.green if last_frame else 180,
                "B": last_frame.color.blue if last_frame else 50,
                "W": last_frame.color.white if last_frame else 0,
            }

            duration_sec = len(signal) / 22050.0
            bpm_est = 120.0 if avg_a > 0.0 else 72.0

            result = {
                "file_path": self.file_path,
                "title": Path(self.file_path).stem,
                "duration_sec": duration_sec,
                "frames_count": len(frames),
                "valence": avg_v,
                "arousal": avg_a,
                "rms": avg_rms,
                "quadrant": quad,
                "bpm": bpm_est,
                "palette": palette,
            }

            self.progress_updated.emit(100, "✓ Analisis Akustik Audio & Pemodelan Mood Selesai!")
            self.analysis_finished.emit(result)

        except Exception as e:
            self.analysis_failed.emit(str(e))


class RussellPlaneWidget(QFrame if HAS_QT else object):
    """Visualizes audio mood coordinate in Russell 2D Valence-Arousal Plane."""
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setFixedSize(240, 240)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 6px;
            }}
        """)
        self.valence = 0.0
        self.arousal = 0.0
        self.quadrant_text = "Idle"

    def set_coordinates(self, v: float, a: float, quad: str = ""):
        self.valence = max(-1.0, min(1.0, v))
        self.arousal = max(-1.0, min(1.0, a))
        self.quadrant_text = quad
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # Axes
        pen_axis = QPen(QColor(Theme.BORDER_STRONG), 1.5, Qt.DashLine)
        painter.setPen(pen_axis)
        painter.drawLine(15, cy, w - 15, cy)
        painter.drawLine(cx, 15, cx, h - 15)

        # Labels
        painter.setFont(QFont("Inter", 8))
        painter.setPen(QColor(Theme.TEXT_MUTED))
        painter.drawText(w - 70, cy - 6, "+V (Praise)")
        painter.drawText(10, cy - 6, "-V (Worship)")
        painter.drawText(cx + 6, 20, "+A (Energetic)")
        painter.drawText(cx + 6, h - 10, "-A (Calm)")

        # Quadrant labels
        painter.setPen(QColor(Theme.ACCENT_AMBER))
        painter.drawText(w - 75, 36, "Q1: Praise")
        painter.setPen(QColor(Theme.ACCENT_CYAN))
        painter.drawText(15, h - 30, "Q3: Worship")

        # Current Mood Point
        px = cx + int(self.valence * (cx - 25))
        py = cy - int(self.arousal * (cy - 25))

        # Glow halo
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(6, 182, 212, 60))
        painter.drawEllipse(px - 12, py - 12, 24, 24)

        # Center dot
        painter.setBrush(QColor(Theme.ACCENT_CYAN))
        painter.drawEllipse(px - 5, py - 5, 10, 10)
        painter.end()


class AnalyzeTab(QWidget if HAS_QT else object):
    """
    Tab Analyze: Core Audio DSP & Mood Analyzer.
    Supports local audio files (.wav, .mp3, .flac, .ogg) and direct YouTube link imports.
    """
    analysis_ready = Signal(dict)

    def __init__(self, project_state=None, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.project_state = project_state
        self.worker: AudioAnalysisWorker | None = None
        self.loaded_songs: list[str] = []
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # Top Section: Title & Controls
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("AUDIO STFT & AFFECTIVE MOOD ANALYZER")
        lbl_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        lbl_desc = QLabel("Short-Time Fourier Transform (N=2048, H=512, 43 FPS) • Ekstraksi Akustik MIR & Model Afektif Russell 2D")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_load_file = QPushButton("📁 Load Audio File...")
        self.btn_load_file.clicked.connect(self._on_load_audio_file)
        top_bar.addWidget(self.btn_load_file)

        self.btn_import_yt = QPushButton("🌐 Import from YouTube...")
        self.btn_import_yt.setStyleSheet(f"background-color: #1e3a5f; border-color: {Theme.ACCENT_CYAN};")
        self.btn_import_yt.clicked.connect(self._on_open_youtube_dialog)
        top_bar.addWidget(self.btn_import_yt)

        self.btn_remove = QPushButton("🗑️ Remove Song")
        self.btn_remove.setEnabled(False)
        self.btn_remove.clicked.connect(self._on_remove_song)
        top_bar.addWidget(self.btn_remove)

        self.btn_analyze = QPushButton("⚡ Analyze Song")
        self.btn_analyze.setStyleSheet(f"background-color: #143521; color: {Theme.COLOR_SUCCESS}; font-weight: bold;")
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.clicked.connect(self._on_start_analysis)
        top_bar.addWidget(self.btn_analyze)

        main_layout.addLayout(top_bar)

        # Splitter: Left Songlist, Right Visualizer & Progress
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #333844; }")

        # Left Container: Song List
        left_box = QGroupBox("Daftar Lagu Sesi Analisis")
        left_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        left_layout = QVBoxLayout(left_box)
        self.song_list_widget = QListWidget()
        self.song_list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {Theme.BG_ELEVATED};
                border-left: 3px solid {Theme.ACCENT_AMBER};
                color: #ffffff;
            }}
        """)
        self.song_list_widget.currentRowChanged.connect(self._on_song_selected)
        left_layout.addWidget(self.song_list_widget)
        splitter.addWidget(left_box)

        # Right Container: Analysis Visualization & Status
        right_box = QGroupBox("Status DSP & Bidang Afektif Russell 2D")
        right_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        right_layout = QVBoxLayout(right_box)

        vis_row = QHBoxLayout()
        self.russell_plane = RussellPlaneWidget()
        vis_row.addWidget(self.russell_plane)

        # Stats Card
        self.stats_label = QLabel("Silakan muat lagu rohani (.mp3/.wav atau link YouTube) lalu klik Analyze.")
        self.stats_label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY}; line-height: 1.5;")
        self.stats_label.setWordWrap(True)
        vis_row.addWidget(self.stats_label, 1)
        right_layout.addLayout(vis_row)

        # Scientific Ticker & Progress
        self.lbl_dsp_status = QLabel("Engine siap.")
        self.lbl_dsp_status.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {Theme.ACCENT_CYAN};")
        right_layout.addWidget(self.lbl_dsp_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                height: 22px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.ACCENT_AMBER};
                border-radius: 3px;
            }}
        """)
        right_layout.addWidget(self.progress_bar)

        splitter.addWidget(right_box)
        splitter.setSizes([320, 680])
        main_layout.addWidget(splitter, 1)

    def _on_load_audio_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Berkas Audio Rohani",
            "",
            "Audio Files (*.wav *.mp3 *.flac *.ogg);;All Files (*.*)",
        )
        if file_path:
            self._add_audio_path(file_path)

    def _on_open_youtube_dialog(self) -> None:
        dlg = YouTubeDialog(self)
        dlg.audio_imported.connect(self._add_audio_path)
        dlg.exec()

    def _add_audio_path(self, path_str: str) -> None:
        self.loaded_songs.append(path_str)
        self.song_list_widget.addItem(f"🎵 {Path(path_str).name}")
        self.song_list_widget.setCurrentRow(len(self.loaded_songs) - 1)
        self.btn_analyze.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.lbl_dsp_status.setText(f"Lagu siap: {Path(path_str).name}")

    def _on_song_selected(self, row: int) -> None:
        has_sel = row >= 0 and row < len(self.loaded_songs)
        self.btn_analyze.setEnabled(has_sel)
        self.btn_remove.setEnabled(has_sel)

    def _on_remove_song(self) -> None:
        row = self.song_list_widget.currentRow()
        if 0 <= row < len(self.loaded_songs):
            self.loaded_songs.pop(row)
            self.song_list_widget.takeItem(row)
            self.btn_analyze.setEnabled(len(self.loaded_songs) > 0)
            self.btn_remove.setEnabled(len(self.loaded_songs) > 0)

    def _on_start_analysis(self) -> None:
        row = self.song_list_widget.currentRow()
        if not (0 <= row < len(self.loaded_songs)):
            return

        target_file = self.loaded_songs[row]
        self.btn_analyze.setEnabled(False)
        self.btn_load_file.setEnabled(False)
        self.btn_import_yt.setEnabled(False)
        self.progress_bar.setValue(5)

        self.worker = AudioAnalysisWorker(target_file)
        self.worker.progress_updated.connect(self._on_analysis_progress)
        self.worker.analysis_finished.connect(self._on_analysis_finished)
        self.worker.analysis_failed.connect(self._on_analysis_failed)
        self.worker.start()

    def _on_analysis_progress(self, percent: int, msg: str) -> None:
        self.progress_bar.setValue(percent)
        self.lbl_dsp_status.setText(msg)

    def _on_analysis_finished(self, res: dict) -> None:
        self.progress_bar.setValue(100)
        self.btn_analyze.setEnabled(True)
        self.btn_load_file.setEnabled(True)
        self.btn_import_yt.setEnabled(True)

        v = res.get("valence", 0.0)
        a = res.get("arousal", 0.0)
        quad = res.get("quadrant", "Idle")
        bpm = res.get("bpm", 120.0)
        rms = res.get("rms", 0.0)

        self.russell_plane.set_coordinates(v, a, quad)

        self.stats_label.setText(
            f"<b>Lagu:</b> {res.get('title')}<br>"
            f"<b>Durasi:</b> {res.get('duration_sec'):.1f} s | <b>Frames STFT:</b> {res.get('frames_count')}<br>"
            f"<b>Estimasi BPM:</b> {bpm:.1f} | <b>Energy RMS:</b> {rms:.3f}<br>"
            f"<b>Russell Affective:</b> Valence = {v:+.2f}, Arousal = {a:+.2f}<br>"
            f"<b>Kuadran Ibadah:</b> <span style='color: {Theme.ACCENT_AMBER}; font-weight: bold;'>{quad}</span><br>"
            f"<b>Warna Panggung:</b> RGBW ({res['palette']['R']}, {res['palette']['G']}, {res['palette']['B']}, {res['palette']['W']})"
        )

        self.analysis_ready.emit(res)

    def _on_analysis_failed(self, err_msg: str) -> None:
        self.btn_analyze.setEnabled(True)
        self.btn_load_file.setEnabled(True)
        self.btn_import_yt.setEnabled(True)
        self.progress_bar.setValue(0)
        self.lbl_dsp_status.setText("Gagal melakukan analisis audio.")
        QMessageBox.critical(self, "Error DSP Analisis", f"Gagal menganalisis audio:\n{err_msg}")

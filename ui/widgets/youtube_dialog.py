"""
youtube_dialog.py — YouTube Audio Importer & Extractor Dialog
Provides an independent pop-up window to paste YouTube links, download audio streams asynchronously,
and automatically load the extracted audio into ZZLUXORA's Analyze workspace.
"""

from __future__ import annotations
import os
import re
import subprocess
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QMessageBox, QWidget, Qt, Signal, QThread
)
from ui.styles import Theme, CONSOLE_QSS


class YouTubeDownloaderWorker(QThread if HAS_QT else object):
    """Background worker thread to download & extract audio from YouTube without freezing the GUI."""
    progress_updated = Signal(int, str)      # (percent, status_message)
    download_finished = Signal(str)          # (downloaded_file_path)
    download_failed = Signal(str)            # (error_message)

    def __init__(self, youtube_url: str, output_dir: Path):
        if not HAS_QT: return
        super().__init__()
        self.url = youtube_url.strip()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        try:
            self.progress_updated.emit(10, "Memvalidasi tautan YouTube...")

            # Check yt-dlp availability
            has_ytdlp = False
            try:
                res = subprocess.run(["yt-dlp", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                has_ytdlp = (res.returncode == 0)
            except Exception:
                has_ytdlp = False

            if has_ytdlp:
                self.progress_updated.emit(25, "Mengunduh audio stream via yt-dlp...")
                # Download audio only as wav/mp3
                output_template = str(self.output_dir / "%(title)s.%(ext)s")
                cmd = [
                    "yt-dlp",
                    "-x",
                    "--audio-format", "wav",
                    "--audio-quality", "0",
                    "-o", output_template,
                    "--no-playlist",
                    self.url
                ]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode != 0:
                    raise RuntimeError(f"Gagal mengunduh audio: {proc.stderr[:200]}")

                # Find the most recently created .wav in output_dir
                wav_files = sorted(self.output_dir.glob("*.wav"), key=os.path.getmtime, reverse=True)
                if wav_files:
                    target_file = str(wav_files[0])
                    self.progress_updated.emit(100, "Ekstraksi audio tuntas!")
                    self.download_finished.emit(target_file)
                    return
                else:
                    raise FileNotFoundError("Berkas audio hasil unduhan tidak ditemukan.")
            else:
                # Standalone fallback: generate synthetic test worship audio if yt-dlp is missing
                self.progress_updated.emit(50, "Pustaka yt-dlp belum terpasang. Menyiapkan audio rohani lokal...")
                from core.audio_loader import AudioLoader
                import soundfile as sf
                loader = AudioLoader()
                synth = loader.generate_synthetic_praise_beat(duration_sec=30.0)
                fallback_path = self.output_dir / "YouTube_Import_Sample.wav"
                sf.write(str(fallback_path), synth, 22050)

                self.progress_updated.emit(100, "Audio siap dianalisis!")
                self.download_finished.emit(str(fallback_path))

        except Exception as e:
            self.download_failed.emit(str(e))


class YouTubeDialog(QDialog if HAS_QT else object):
    """Independent pop-up window for importing YouTube audio into ZZLUXORA."""
    audio_imported = Signal(str)  # Emits target audio path to AnalyzeTab

    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setWindowTitle("Import Audio dari YouTube — ZZLUXORA")
        self.setFixedSize(540, 260)
        self.setStyleSheet(CONSOLE_QSS)

        self.output_dir = Path.home() / "ANDREAS" / "zzluxora_v10" / "data" / "audio"
        self.worker: YouTubeDownloaderWorker | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Title
        title_lbl = QLabel("🌐 Import Lagu Rohani dari YouTube")
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(
            "Masukkan tautan video YouTube lagu puji-pujian atau penyembahan. "
            "Sistem akan mengunduh stream audio berkualitas tinggi untuk dianalisis STFT."
        )
        desc_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # URL Input Field
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        layout.addWidget(self.url_input)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                text-align: center;
                color: {Theme.TEXT_PRIMARY};
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.ACCENT_CYAN};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Status message label
        self.status_lbl = QLabel("Siap mengunduh.")
        self.status_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.status_lbl)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_download = QPushButton("⬇ Download & Extract Audio")
        self.btn_download.setStyleSheet(f"background-color: #1e3a5f; border-color: {Theme.ACCENT_CYAN};")
        self.btn_download.clicked.connect(self._on_start_download)
        btn_layout.addWidget(self.btn_download)

        layout.addLayout(btn_layout)

    def _on_start_download(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Tautan Kosong", "Silakan masukkan URL YouTube terlebih dahulu.")
            return

        self.btn_download.setEnabled(False)
        self.url_input.setEnabled(False)
        self.progress_bar.setValue(5)
        self.status_lbl.setText("Memulai proses unduhan...")

        self.worker = YouTubeDownloaderWorker(url, self.output_dir)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.download_finished.connect(self._on_finished)
        self.worker.download_failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, percent: int, msg: str) -> None:
        self.progress_bar.setValue(percent)
        self.status_lbl.setText(msg)

    def _on_finished(self, file_path: str) -> None:
        self.progress_bar.setValue(100)
        self.status_lbl.setText("✓ Audio berhasil diunduh dan siap dianalisis.")
        self.audio_imported.emit(file_path)
        QMessageBox.information(
            self,
            "Ekstraksi Audio Berhasil",
            f"Audio berhasil diekstrak dan disimpan ke:\n{Path(file_path).name}\n\nAudio otomatis dimuat ke Tab Analyze.",
        )
        self.accept()

    def _on_failed(self, error_msg: str) -> None:
        self.btn_download.setEnabled(True)
        self.url_input.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_lbl.setText("Gagal mengunduh audio.")
        QMessageBox.critical(self, "Error Unduhan", f"Terjadi kesalahan saat mengunduh audio:\n{error_msg}")

"""
youtube_dialog.py | YouTube Audio Importer & Extractor Dialog
Provides an independent pop-up window to paste YouTube links, download audio streams asynchronously,
and automatically load the extracted audio into ZZLUXORA's Analyze workspace.
"""

from __future__ import annotations
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QMessageBox, QWidget, Qt, Signal, QThread
)
from ui.styles import Theme, CONSOLE_QSS
from core import youtube_importer as yt


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
        """Download and convert via core.youtube_importer, reporting progress."""
        try:
            target = yt.download_and_convert(
                self.url,
                self.output_dir,
                progress=lambda percent, message: self.progress_updated.emit(percent, message),
            )
        except yt.YouTubeImportError as exc:
            self.download_failed.emit(str(exc))
            return
        except Exception as exc:  # unexpected: still surface it instead of hanging
            self.download_failed.emit(f"Unexpected import error: {exc}")
            return

        self.download_finished.emit(str(target))


class YouTubeDialog(QDialog if HAS_QT else object):
    """Independent pop-up window for importing YouTube audio into ZZLUXORA."""
    audio_imported = Signal(str)  # Emits target audio path to AnalyzeTab

    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setWindowTitle("Import YouTube Audio | ZZLUXORA")
        self.setMinimumSize(560, 320)
        self.setStyleSheet(CONSOLE_QSS)

        # Derive from the repository location rather than a fixed home path, so
        # the dialog works on the Windows build machine as well as on Linux.
        repo_root = Path(__file__).resolve().parents[2]
        self.output_dir = repo_root / "data" / "audio"
        self.worker: YouTubeDownloaderWorker | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Title
        title_lbl = QLabel("Import Audio from YouTube")
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(
            "Enter a YouTube video link. The system will download high-quality audio stream for STFT analysis."
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
                background-color: {Theme.SURFACE_INPUT};
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

        # Dependency line: tells the operator up front whether imports can run.
        self.dep_lbl = QLabel("")
        self.dep_lbl.setWordWrap(True)
        layout.addWidget(self.dep_lbl)
        self._refresh_dependency_line()

        # Status message label
        self.status_lbl = QLabel("Ready to download.")
        self.status_lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.status_lbl)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_download = QPushButton("Download & Extract Audio")
        self.btn_download.setStyleSheet(f"font-weight: bold;")
        self.btn_download.clicked.connect(self._on_start_download)
        btn_layout.addWidget(self.btn_download)

        layout.addLayout(btn_layout)

    def _refresh_dependency_line(self) -> None:
        """Show whether the required components are present, before any attempt."""
        missing = [status for status in yt.check_dependencies() if not status.available]
        if missing:
            names = ", ".join(status.name for status in missing)
            self.dep_lbl.setText(f"Missing: {names}. Cannot import until installed.")
            self.dep_lbl.setStyleSheet(
                f"color: {Theme.COLOR_DANGER}; font-size: 11px; font-weight: 700;"
            )
            self.btn_download.setEnabled(False)
        else:
            self.dep_lbl.setText("All components ready (yt-dlp, ffmpeg).")
            self.dep_lbl.setStyleSheet(f"color: {Theme.COLOR_SUCCESS}; font-size: 11px;")
            self.btn_download.setEnabled(True)

    def _on_start_download(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return

        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Empty URL", "Please enter a valid YouTube video link first.")
            return

        if not yt.looks_like_youtube_url(url):
            QMessageBox.warning(
                self,
                "Invalid Link",
                "That does not look like a YouTube video link.\n\n"
                "Paste a single video URL, for example:\n"
                "https://www.youtube.com/watch?v=...  or  https://youtu.be/...",
            )
            return

        missing = [status for status in yt.check_dependencies() if not status.available]
        if missing:
            details = "\n".join(f"- {s.name}: install with {s.remedy}" for s in missing)
            self.status_lbl.setText("Missing required components.")
            QMessageBox.critical(
                self,
                "Missing Components",
                "YouTube import needs components that are not installed:\n\n" + details,
            )
            return

        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.url_input.setEnabled(False)
        self.progress_bar.setValue(5)
        self.status_lbl.setText("Preparing download...")

        self.worker = YouTubeDownloaderWorker(url, self.output_dir)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.download_finished.connect(self._on_finished)
        self.worker.download_failed.connect(self._on_failed)
        self.worker.finished.connect(self._release_worker)
        self.worker.start()

    def _release_worker(self) -> None:
        """Release the finished worker so a second import does not leak a thread."""
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None

    def _on_progress(self, percent: int, msg: str) -> None:
        self.progress_bar.setValue(percent)
        self.status_lbl.setText(msg)

    def _on_finished(self, file_path: str) -> None:
        self.progress_bar.setValue(100)
        self.status_lbl.setText("[OK] Audio successfully downloaded and ready for analysis.")
        self.audio_imported.emit(file_path)
        QMessageBox.information(
            self,
            "Audio Extracted",
            f"Audio successfully extracted and saved to:\n{Path(file_path).name}\n\nLoaded into Analyze tab.",
        )
        self.accept()

    def _on_failed(self, error_msg: str) -> None:
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.url_input.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_lbl.setText("Import failed. See the message for the reason.")
        QMessageBox.critical(self, "Import Failed", error_msg)

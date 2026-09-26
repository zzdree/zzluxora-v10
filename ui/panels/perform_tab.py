"""
perform_tab.py — Live Stage Show Controller & Performance Cue Generator
Manages the worship song playlist, song sections (Verse, Chorus, Bridge),
fade timings, and exports automated executor triggers to Tab Page.
"""

from __future__ import annotations

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSplitter, QDoubleSpinBox, QMessageBox,
    Qt, Signal, QColor, QFont
)
from ui.styles import Theme


class PerformTab(QWidget if HAS_QT else object):
    """Perform Tab: Live stage show sequencer and automated Page executor generator."""
    export_to_page = Signal(list)  # Emits list of generated cues for PageTab

    def __init__(self, project_state=None, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.project_state = project_state
        self.playlist: list[dict] = []
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # Top Control Bar
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("LIVE STAGE SHOW CONTROLLER & PERFORMANCE")
        lbl_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        lbl_desc = QLabel("Pengaturan Playlist Pertunjukan Live • Section Cues (Verse, Chorus, Bridge) & Transisi Fade")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_move_up = QPushButton("▲ Geser Naik")
        self.btn_move_up.clicked.connect(self._on_move_up)
        top_bar.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("▼ Geser Turun")
        self.btn_move_down.clicked.connect(self._on_move_down)
        top_bar.addWidget(self.btn_move_down)

        self.btn_delete_song = QPushButton("🗑️ Hapus Lagu")
        self.btn_delete_song.clicked.connect(self._on_delete_song)
        top_bar.addWidget(self.btn_delete_song)

        self.btn_export_page = QPushButton("⚡ Generate / Export to Page")
        self.btn_export_page.setStyleSheet(f"background-color: #143521; color: {Theme.COLOR_SUCCESS}; font-weight: 800;")
        self.btn_export_page.clicked.connect(self._on_export_to_page)
        top_bar.addWidget(self.btn_export_page)

        main_layout.addLayout(top_bar)

        # Splitter: Playlist vs Cues
        splitter = QSplitter(Qt.Horizontal)

        # Left: Playlist List
        left_box = QGroupBox("Playlist Urutan Pertunjukan Live")
        left_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        left_layout = QVBoxLayout(left_box)

        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {Theme.BG_ELEVATED};
                border-left: 3px solid {Theme.ACCENT_CYAN};
                color: #ffffff;
            }}
        """)
        self.playlist_widget.currentRowChanged.connect(self._on_song_selected)
        left_layout.addWidget(self.playlist_widget)
        splitter.addWidget(left_box)

        # Right: Section Cues & Timing Table
        right_box = QGroupBox("Section Cues & Timing Pencahayaan Lagu Terpilih")
        right_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        right_layout = QVBoxLayout(right_box)

        self.cue_table = QTableWidget(0, 5)
        self.cue_table.setHorizontalHeaderLabels(["Bagian Lagu", "Suasana", "Fade In (s)", "Fade Out (s)", "Chase Rate"])
        self.cue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cue_table.verticalHeader().setVisible(False)

        right_layout.addWidget(self.cue_table)
        splitter.addWidget(right_box)

        splitter.setSizes([350, 650])
        main_layout.addWidget(splitter, 1)

    def add_analyzed_song(self, song_data: dict) -> None:
        """Receives exported song from ResultTab and appends to live playlist."""
        self.playlist.append(song_data)
        title = song_data.get("title", "Untitled")
        quad = song_data.get("quadrant", "General")
        bpm = song_data.get("bpm", 120.0)
        self.playlist_widget.addItem(f"🎶 {title} — [{quad}, {bpm:.0f} BPM]")
        self.playlist_widget.setCurrentRow(len(self.playlist) - 1)

    def _on_song_selected(self, row: int) -> None:
        pass

    def _on_move_up(self) -> None:
        row = self.playlist_widget.currentRow()
        if row > 0:
            song = self.playlist.pop(row)
            self.playlist.insert(row - 1, song)
            item = self.playlist_widget.takeItem(row)
            self.playlist_widget.insertItem(row - 1, item)
            self.playlist_widget.setCurrentRow(row - 1)

    def _on_move_down(self) -> None:
        row = self.playlist_widget.currentRow()
        if 0 <= row < len(self.playlist) - 1:
            song = self.playlist.pop(row)
            self.playlist.insert(row + 1, song)
            item = self.playlist_widget.takeItem(row)
            self.playlist_widget.insertItem(row + 1, item)
            self.playlist_widget.setCurrentRow(row + 1)

    def _on_delete_song(self) -> None:
        row = self.playlist_widget.currentRow()
        if 0 <= row < len(self.playlist):
            self.playlist.pop(row)
            self.playlist_widget.takeItem(row)

    def _on_export_to_page(self) -> None:
        """Generates executor cues and pushes to PageTab."""
        if not self.playlist:
            QMessageBox.warning(self, "Playlist Kosong", "Tambahkan lagu ke playlist terlebih dahulu sebelum mengekspor ke Page.")
            return

        generated_cues = []
        for song in self.playlist:
            title = song.get("title", "Song")
            quad = song.get("quadrant", "Praise")
            palette = song.get("palette", {"R": 255, "G": 255, "B": 255, "W": 0})

            # Generate cues for Intro, Verse, Chorus
            generated_cues.append({
                "label": f"{title}\n(Verse)",
                "type": "scene",
                "color": palette,
                "dimmer": 180,
            })
            generated_cues.append({
                "label": f"{title}\n(Chorus)",
                "type": "scene",
                "color": palette,
                "dimmer": 255,
            })
            generated_cues.append({
                "label": f"FLASH ⚡\n{title[:6]}",
                "type": "flash",
                "color": {"R": 255, "G": 255, "B": 255, "W": 255},
                "dimmer": 255,
            })

        self.export_to_page.emit(generated_cues)
        QMessageBox.information(
            self,
            "Ekspor Selesai",
            f"Berhasil membangkitkan {len(generated_cues)} tombol eksekutor virtual di Tab Page!",
        )

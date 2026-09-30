"""
perform_tab.py — Live Stage Show Controller & Performance Cue Generator
Manages the worship song playlist, song sections (Intro, Verse, Chorus, Bridge, Ending),
fade timings, smooth live cue crossfading [GO+], and exports automated executor triggers to Tab Page.
"""

from __future__ import annotations

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSplitter, QDoubleSpinBox, QMessageBox,
    Qt, Signal, QColor, QFont
)
from ui.styles import Theme


class PerformTab(QWidget if HAS_QT else object):
    """Perform Tab: Live stage show sequencer, cue crossfade controller, and Page executor generator."""
    export_to_page = Signal(list)  # Emits list of generated cues for PageTab
    cue_activated = Signal(dict)   # Emits active cue with color, dimmer, fade_time to MainWindow

    def __init__(self, project_state=None, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.project_state = project_state
        self.playlist: list[dict] = []
        self.current_song_cues: list[dict] = []
        self.active_cue_index: int = -1
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        # Top Control Bar
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("LIVE STAGE SHOW CONTROLLER & PERFORMANCE")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        lbl_desc = QLabel("Pengaturan Playlist Pertunjukan Live | Section Cues, Crossfade [GO+], & Transisi Fade")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_move_up = QPushButton("MOVE UP")
        self.btn_move_up.clicked.connect(self._on_move_up)
        top_bar.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("MOVE DOWN")
        self.btn_move_down.clicked.connect(self._on_move_down)
        top_bar.addWidget(self.btn_move_down)

        self.btn_delete_song = QPushButton("DELETE")
        self.btn_delete_song.clicked.connect(self._on_delete_song)
        top_bar.addWidget(self.btn_delete_song)

        self.btn_export_page = QPushButton("GENERATE EXECUTORS")
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

        # Right: Section Cues & Master Playback
        right_box = QGroupBox("Section Cues & Timing Pencahayaan Lagu Terpilih")
        right_box.setStyleSheet(f"QGroupBox {{ font-weight: 700; color: {Theme.TEXT_PRIMARY}; }}")
        right_layout = QVBoxLayout(right_box)

        self.cue_table = QTableWidget(0, 6)
        self.cue_table.setHorizontalHeaderLabels([
            "Bagian Lagu", "Suasana / Mood", "Fade In", "Fade Out", "Dimmer", "Trigger"
        ])
        self.cue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cue_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.cue_table.verticalHeader().setVisible(False)
        self.cue_table.cellDoubleClicked.connect(lambda row, col: self._trigger_cue_at_row(row))
        right_layout.addWidget(self.cue_table, 1)

        # Live Master Playback Transport Toolbar
        playback_box = QFrame()
        playback_box.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_ELEVATED};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        playback_layout = QHBoxLayout(playback_box)
        playback_layout.setContentsMargins(10, 8, 10, 8)
        playback_layout.setSpacing(10)

        self.btn_prev_cue = QPushButton("⏮ PREV")
        self.btn_prev_cue.setStyleSheet(f"font-weight: 700; color: {Theme.TEXT_PRIMARY};")
        self.btn_prev_cue.clicked.connect(self._on_prev_clicked)
        playback_layout.addWidget(self.btn_prev_cue)

        self.btn_go_cue = QPushButton("▶ GO [NEXT CUE]")
        self.btn_go_cue.setStyleSheet(f"""
            QPushButton {{
                background-color: #1e3a1e;
                border: 2px solid {Theme.COLOR_SUCCESS};
                color: {Theme.COLOR_SUCCESS};
                font-weight: 900;
                font-size: 13px;
                padding: 8px 18px;
            }}
            QPushButton:hover {{
                background-color: {Theme.COLOR_SUCCESS};
                color: #000000;
            }}
        """)
        self.btn_go_cue.clicked.connect(self._on_go_clicked)
        playback_layout.addWidget(self.btn_go_cue)

        self.btn_fade_black = QPushButton("⏹ FADE BLACK")
        self.btn_fade_black.setStyleSheet(f"""
            QPushButton {{
                background-color: #3b1818;
                border: 1px solid {Theme.COLOR_DANGER};
                color: {Theme.COLOR_DANGER};
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {Theme.COLOR_DANGER};
                color: #ffffff;
            }}
        """)
        self.btn_fade_black.clicked.connect(self._on_fade_black_clicked)
        playback_layout.addWidget(self.btn_fade_black)

        playback_layout.addStretch()

        self.lbl_cue_status = QLabel("STATUS: STANDBY — PILIH CUE ATAU TEKAN [GO]")
        self.lbl_cue_status.setStyleSheet(f"font-weight: 800; color: {Theme.ACCENT_AMBER}; font-size: 11px;")
        playback_layout.addWidget(self.lbl_cue_status)

        right_layout.addWidget(playback_box)
        splitter.addWidget(right_box)

        splitter.setSizes([320, 680])
        main_layout.addWidget(splitter, 1)

    # -----------------------------------------------------------------
    # PLAYLIST & SONG SECTION GENERATION
    # -----------------------------------------------------------------
    def add_analyzed_song(self, song_data: dict) -> None:
        """Receives exported song from ResultTab and appends to live playlist."""
        self.playlist.append(song_data)
        title = song_data.get("title", "Untitled")
        quad = song_data.get("quadrant", "General")
        bpm = song_data.get("bpm", 120.0)
        self.playlist_widget.addItem(f"{title} [{quad}, {bpm:.0f} BPM]")
        self.playlist_widget.setCurrentRow(len(self.playlist) - 1)

    def _on_song_selected(self, row: int) -> None:
        if not (0 <= row < len(self.playlist)):
            self.cue_table.setRowCount(0)
            self.current_song_cues = []
            self.active_cue_index = -1
            self.lbl_cue_status.setText("STATUS: STANDBY")
            return

        song = self.playlist[row]
        self._populate_song_cues(song)

    def _populate_song_cues(self, song: dict) -> None:
        """Generates dynamic worship section cues based on affective quadrant and tempo."""
        title = song.get("title", "Lagu")
        quadrant = str(song.get("quadrant", "")).lower()
        base_palette = song.get("palette", {"R": 255, "G": 200, "B": 100, "W": 40})
        r_base = int(base_palette.get("R", 255))
        g_base = int(base_palette.get("G", 200))
        b_base = int(base_palette.get("B", 100))
        w_base = int(base_palette.get("W", 40))

        is_worship = ("worship" in quadrant or "q3" in quadrant or "q4" in quadrant)

        if is_worship:
            # Worship: Deep reverence, meditative intro, sacred altar call, high white ratio
            cues = [
                {
                    "section": "Intro",
                    "mood": "Deep Sanctuary Atmosphere",
                    "fade_in": 3.0,
                    "fade_out": 2.5,
                    "dimmer": 140,
                    "chase_rate": 0.5,
                    "color": {"R": max(20, int(r_base * 0.4)), "G": max(30, int(g_base * 0.5)), "B": max(180, int(b_base * 1.2)), "W": 20},
                },
                {
                    "section": "Verse 1",
                    "mood": "Warm Prayerful Reflection",
                    "fade_in": 2.0,
                    "fade_out": 2.0,
                    "dimmer": 180,
                    "chase_rate": 0.8,
                    "color": {"R": max(180, int(r_base * 0.9)), "G": max(130, int(g_base * 0.8)), "B": 40, "W": 90},
                },
                {
                    "section": "Chorus",
                    "mood": "Majestic Sacred Reverence",
                    "fade_in": 1.5,
                    "fade_out": 2.0,
                    "dimmer": 240,
                    "chase_rate": 1.2,
                    "color": {"R": 255, "G": 210, "B": 90, "W": 130},
                },
                {
                    "section": "Verse 2",
                    "mood": "Intimate Soft Lavender",
                    "fade_in": 2.0,
                    "fade_out": 2.0,
                    "dimmer": 180,
                    "chase_rate": 0.8,
                    "color": {"R": 170, "G": 90, "B": 230, "W": 50},
                },
                {
                    "section": "Bridge",
                    "mood": "Holy Surrender (Altar Call)",
                    "fade_in": 2.5,
                    "fade_out": 2.0,
                    "dimmer": 255,
                    "chase_rate": 1.0,
                    "color": {"R": 230, "G": 230, "B": 255, "W": 255},
                },
                {
                    "section": "Ending",
                    "mood": "Quiet Peaceful Night",
                    "fade_in": 3.0,
                    "fade_out": 4.0,
                    "dimmer": 100,
                    "chase_rate": 0.5,
                    "color": {"R": 15, "G": 30, "B": 160, "W": 0},
                },
            ]
        else:
            # Praise: High energy, bright saturated color, faster chase, triumphant hits
            cues = [
                {
                    "section": "Intro",
                    "mood": "Praise Energy Rise",
                    "fade_in": 1.5,
                    "fade_out": 1.5,
                    "dimmer": 210,
                    "chase_rate": 1.5,
                    "color": {"R": 255, "G": 160, "B": 20, "W": 30},
                },
                {
                    "section": "Verse 1",
                    "mood": "Joyful Groove (Cyan/Yellow)",
                    "fade_in": 1.0,
                    "fade_out": 1.5,
                    "dimmer": 200,
                    "chase_rate": 1.5,
                    "color": {"R": 240, "G": 220, "B": 30, "W": 20},
                },
                {
                    "section": "Chorus",
                    "mood": "Shout of Victory (Full Dynamic)",
                    "fade_in": 0.8,
                    "fade_out": 1.0,
                    "dimmer": 255,
                    "chase_rate": 2.5,
                    "color": {"R": 255, "G": 50, "B": 190, "W": 50},
                },
                {
                    "section": "Verse 2",
                    "mood": "Stepping Forward (Emerald)",
                    "fade_in": 1.0,
                    "fade_out": 1.5,
                    "dimmer": 200,
                    "chase_rate": 1.5,
                    "color": {"R": 30, "G": 240, "B": 80, "W": 30},
                },
                {
                    "section": "Bridge",
                    "mood": "Blazing Anthem Build",
                    "fade_in": 1.0,
                    "fade_out": 1.0,
                    "dimmer": 255,
                    "chase_rate": 2.0,
                    "color": {"R": 255, "G": 100, "B": 0, "W": 40},
                },
                {
                    "section": "Ending",
                    "mood": "Triumphant Flash & Hit",
                    "fade_in": 0.5,
                    "fade_out": 3.0,
                    "dimmer": 255,
                    "chase_rate": 1.0,
                    "color": {"R": 255, "G": 255, "B": 180, "W": 120},
                },
            ]

        self.current_song_cues = cues
        self.active_cue_index = -1
        self.cue_table.setRowCount(len(cues))

        for row, cue in enumerate(cues):
            it_sec = QTableWidgetItem(cue["section"])
            it_sec.setFont(QFont("Inter", 10, QFont.Bold))
            it_sec.setForeground(QColor(Theme.TEXT_PRIMARY))
            self.cue_table.setItem(row, 0, it_sec)

            it_mood = QTableWidgetItem(cue["mood"])
            it_mood.setForeground(QColor(Theme.ACCENT_CYAN))
            self.cue_table.setItem(row, 1, it_mood)

            it_fi = QTableWidgetItem(f"{cue['fade_in']:.1f}s")
            it_fi.setTextAlignment(Qt.AlignCenter)
            it_fi.setForeground(QColor(Theme.COLOR_SUCCESS))
            self.cue_table.setItem(row, 2, it_fi)

            it_fo = QTableWidgetItem(f"{cue['fade_out']:.1f}s")
            it_fo.setTextAlignment(Qt.AlignCenter)
            it_fo.setForeground(QColor(Theme.COLOR_WARNING))
            self.cue_table.setItem(row, 3, it_fo)

            it_dim = QTableWidgetItem(f"{int(cue['dimmer'] * 100 / 255)}%")
            it_dim.setTextAlignment(Qt.AlignCenter)
            it_dim.setForeground(QColor(Theme.TEXT_PRIMARY))
            self.cue_table.setItem(row, 4, it_dim)

            # Trigger Button in Table
            btn_go = QPushButton("GO")
            btn_go.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1a2a1a;
                    border: 1px solid {Theme.COLOR_SUCCESS};
                    color: {Theme.COLOR_SUCCESS};
                    font-weight: 800;
                    font-size: 10px;
                    padding: 3px 8px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.COLOR_SUCCESS};
                    color: #000000;
                }}
            """)
            btn_go.clicked.connect(lambda _, r=row: self._trigger_cue_at_row(r))
            self.cue_table.setCellWidget(row, 5, btn_go)

        self.lbl_cue_status.setText(f"READY: {title} ({len(cues)} Section Cues)")

    # -----------------------------------------------------------------
    # CUE PLAYBACK & MASTER GO+ ENGINE
    # -----------------------------------------------------------------
    def _trigger_cue_at_row(self, row: int) -> None:
        if not (0 <= row < len(self.current_song_cues)):
            return

        self.active_cue_index = row
        cue = self.current_song_cues[row]

        # Highlight active row in table
        for r in range(self.cue_table.rowCount()):
            for c in range(5):
                it = self.cue_table.item(r, c)
                if it:
                    if r == row:
                        it.setBackground(QColor("#243322"))
                    else:
                        it.setBackground(QColor("transparent"))

        self.cue_table.selectRow(row)

        sec_name = cue.get("section", "Cue")
        fade_time = float(cue.get("fade_in", 1.5))
        self.lbl_cue_status.setText(f"AKTIF: [{sec_name.upper()} — {cue['mood']}] | Fade: {fade_time:.1f}s")

        # Emit to MainWindow for smooth crossfade
        payload = {
            "type": "scene",
            "active": True,
            "label": sec_name,
            "dimmer": cue.get("dimmer", 255),
            "color": cue.get("color", {"R": 255, "G": 255, "B": 255, "W": 0}),
            "fade_time": fade_time,
        }
        self.cue_activated.emit(payload)

    def _on_go_clicked(self) -> None:
        """Master GO+ / Next Cue trigger."""
        if not self.current_song_cues:
            return

        next_row = self.active_cue_index + 1
        if next_row >= len(self.current_song_cues):
            # Advance to next song if available
            curr_song_row = self.playlist_widget.currentRow()
            if curr_song_row + 1 < len(self.playlist):
                self.playlist_widget.setCurrentRow(curr_song_row + 1)
                next_row = 0
            else:
                next_row = 0  # Loop back to start

        self._trigger_cue_at_row(next_row)

    def _on_prev_clicked(self) -> None:
        """Trigger previous cue."""
        if not self.current_song_cues:
            return
        prev_row = max(0, self.active_cue_index - 1)
        self._trigger_cue_at_row(prev_row)

    def _on_fade_black_clicked(self) -> None:
        """Smoothly fade to blackout over 2.5s."""
        self.lbl_cue_status.setText("AKTIF: [BLACKOUT] | Fade: 2.5s")
        # Deselect rows
        for r in range(self.cue_table.rowCount()):
            for c in range(5):
                it = self.cue_table.item(r, c)
                if it: it.setBackground(QColor("transparent"))

        self.cue_activated.emit({
            "type": "scene",
            "active": False,
            "dimmer": 0,
            "color": {"R": 0, "G": 0, "B": 0, "W": 0},
            "fade_time": 2.5,
        })

    # -----------------------------------------------------------------
    # PLAYLIST REORDERING & EXPORT TO PAGE
    # -----------------------------------------------------------------
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
        """Generates executor cues across all songs and pushes to PageTab."""
        if not self.playlist:
            QMessageBox.warning(self, "Playlist Kosong", "Tambahkan lagu ke playlist terlebih dahulu sebelum mengekspor ke Page.")
            return

        generated_cues = []
        for song in self.playlist:
            title = song.get("title", "Song")
            short_title = title.split("(")[0].strip()[:14]
            palette = song.get("palette", {"R": 255, "G": 255, "B": 255, "W": 0})
            quadrant = str(song.get("quadrant", "")).lower()
            is_worship = ("worship" in quadrant or "q3" in quadrant or "q4" in quadrant)

            # 1. Verse Cue
            generated_cues.append({
                "label": f"{short_title}\n(Verse)",
                "type": "scene",
                "color": palette,
                "dimmer": 180,
                "fade_time": 2.0,
            })
            # 2. Chorus Cue
            generated_cues.append({
                "label": f"{short_title}\n(Chorus)",
                "type": "scene",
                "color": palette,
                "dimmer": 255,
                "fade_time": 1.2 if is_worship else 0.8,
            })
            # 3. Flash Hit Button
            generated_cues.append({
                "label": f"FLASH\n{short_title[:8]}",
                "type": "flash",
                "color": {"R": 255, "G": 255, "B": 255, "W": 255},
                "dimmer": 255,
                "fade_time": 0.0,
            })

        self.export_to_page.emit(generated_cues)
        QMessageBox.information(
            self,
            "Ekspor Selesai",
            f"Berhasil membangkitkan {len(generated_cues)} tombol eksekutor virtual di Tab Page!",
        )

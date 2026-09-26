"""
main_window.py — Master Lighting Console Window for ZZLUXORA v10
Features a 3-level header hierarchy (TitleBar, MenuBar, ProgramBar), 6 central workspaces,
and floating tool windows (Fixture List, Fixture Editor, Stage Visualizer, Settings, Help, About).
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QMenuBar, QMenu,
    QFileDialog, QMessageBox, QButtonGroup, Qt, QTimer, QSize,
    QAction, QKeySequence, QIcon, QPixmap
)

from ui.styles import Theme, CONSOLE_QSS
from ui.panels.address_tab import AddressTab
from ui.panels.analyze_tab import AnalyzeTab
from ui.panels.result_tab import ResultTab
from ui.panels.perform_tab import PerformTab
from ui.panels.page_tab import PageTab
from ui.panels.mixer_tab import MixerTab
from ui.panels.fixture_list import FixtureListWindow
from ui.panels.fixture_editor import FixtureEditorWindow
from ui.panels.preview_tab import StageVisualizerWindow
from ui.panels.settings_panel import SettingsDialog
from ui.panels.help_panel import HelpDialog
from ui.panels.about_panel import AboutDialog

from core.artnet_sender import ArtNetSender
from core.models import ProjectState
from core.project_io import ProjectIO


class MainWindow(QMainWindow if HAS_QT else object):
    """
    Main Production Lighting Console Window.
    Implements 3-level desktop header, 6 integrated workspaces, and floating utility windows.
    """
    def __init__(self):
        if not HAS_QT: return
        super().__init__()
        self.setWindowTitle("ZZLUXORA — Stage Lighting Console")
        self.resize(1280, 800)
        self.setStyleSheet(CONSOLE_QSS)

        # Set Window and Taskbar Icon
        logo_path = Path(__file__).resolve().parent / "assets" / "logo_zz.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        # DMX Buffer & State
        self.dmx_buffer = bytearray(512)
        self.project_state = ProjectState(project_name="Untitled.zlx")
        self.current_project_path = "Untitled.zlx"
        self.target_ip = "127.0.0.1"
        self.target_universe = 0
        self.target_port = 6454
        self.is_transmitting = False

        # Core ArtNet Sender
        self.artnet_sender = ArtNetSender(target_ip=self.target_ip, universe=self.target_universe, port=self.target_port)

        # Streaming Timer (43 FPS, ~23.22 ms)
        self.stream_timer = QTimer(self)
        self.stream_timer.setInterval(23)
        self.stream_timer.timeout.connect(self._stream_artnet_packet)

        # Floating Sub-Windows
        self.win_fixture_list: FixtureListWindow | None = None
        self.win_fixture_editor: FixtureEditorWindow | None = None
        self.win_visualizer: StageVisualizerWindow | None = None

        self._init_menu_bar()
        self._init_ui()
        self._init_shortcuts()
        self._update_title_bar()

    def _init_menu_bar(self) -> None:
        """Level 2: Main Menu Bar."""
        mb = self.menuBar()

        # 1. File Menu
        menu_file = mb.addMenu("File")

        act_open = QAction("Open Project...", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._on_open_project)
        menu_file.addAction(act_open)

        act_save = QAction("Save Project", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._on_save_project)
        menu_file.addAction(act_save)

        act_save_as = QAction("Save As Project...", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._on_save_as_project)
        menu_file.addAction(act_save_as)

        menu_file.addSeparator()

        act_exit = QAction("Exit", self)
        act_exit.setShortcut(QKeySequence("Alt+F4"))
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        # 2. Standalone Floating Window Menus
        act_fix = QAction("Fixture", self)
        act_fix.triggered.connect(self._on_open_fixture_list)
        mb.addAction(act_fix)

        act_edit = QAction("Editor", self)
        act_edit.triggered.connect(self._on_open_fixture_editor)
        mb.addAction(act_edit)

        act_prev = QAction("Preview", self)
        act_prev.triggered.connect(self._on_open_visualizer)
        mb.addAction(act_prev)

        act_set = QAction("Setting", self)
        act_set.triggered.connect(self._on_open_settings)
        mb.addAction(act_set)

        act_help = QAction("Help", self)
        act_help.triggered.connect(self._on_open_help)
        mb.addAction(act_help)

        act_about = QAction("About", self)
        act_about.triggered.connect(self._on_open_about)
        mb.addAction(act_about)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # -------------------------------------------------------------
        # LEVEL 1: TITLE BAR FRAME (App Name & File Path)
        # -------------------------------------------------------------
        title_bar_frame = QFrame()
        title_bar_frame.setObjectName("TitleBarFrame")
        title_bar_layout = QHBoxLayout(title_bar_frame)
        title_bar_layout.setContentsMargins(12, 4, 12, 4)
        title_bar_layout.setSpacing(10)

        # App Logo Icon
        logo_path = Path(__file__).resolve().parent / "assets" / "logo_zz.png"
        lbl_logo = QLabel()
        if logo_path.exists():
            aspect_mode = getattr(Qt, "KeepAspectRatio", getattr(Qt.AspectRatioMode, "KeepAspectRatio", None))
            smooth_mode = getattr(Qt, "SmoothTransformation", getattr(Qt.TransformationMode, "SmoothTransformation", None))
            pix = QPixmap(str(logo_path)).scaled(20, 20, aspect_mode, smooth_mode)
            lbl_logo.setPixmap(pix)
        title_bar_layout.addWidget(lbl_logo)

        lbl_app_name = QLabel("ZZLUXORA")
        lbl_app_name.setObjectName("AppTitleLabel")
        title_bar_layout.addWidget(lbl_app_name)

        title_bar_layout.addWidget(QLabel("|", styleSheet=f"color: {Theme.BORDER_STRONG};"))

        self.lbl_project_path = QLabel("[Untitled.zlx]")
        self.lbl_project_path.setObjectName("ProjectPathLabel")
        title_bar_layout.addWidget(self.lbl_project_path)

        title_bar_layout.addStretch()
        root_layout.addWidget(title_bar_frame)

        # -------------------------------------------------------------
        # LEVEL 3: PROGRAM VIEW BAR (Horizontal Workspace Tabs & Status)
        # -------------------------------------------------------------
        program_bar_frame = QFrame()
        program_bar_frame.setObjectName("ProgramBarFrame")
        pbar_layout = QHBoxLayout(program_bar_frame)
        pbar_layout.setContentsMargins(12, 4, 12, 4)
        pbar_layout.setSpacing(8)

        # Workspace Tab Buttons Group (Left)
        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)

        tab_names = ["Address", "Analyze", "Result", "Perform", "Page", "Mixer"]
        self.tab_buttons: list[QPushButton] = []
        for idx, name in enumerate(tab_names):
            btn = QPushButton(name)
            btn.setProperty("class", "ProgramTabBtn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, i=idx: self._switch_workspace(i))
            self.tab_group.addButton(btn, idx)
            pbar_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        self.tab_buttons[0].setChecked(True)
        pbar_layout.addStretch()

        # Telemetry & Main Stage Action Buttons (Right)
        self.btn_artnet_badge = QPushButton("ART-NET: IDLE")
        self.btn_artnet_badge.setObjectName("ArtNetBadgeBtn")
        self.btn_artnet_badge.setProperty("connected", "false")
        self.btn_artnet_badge.clicked.connect(self._on_open_settings)
        pbar_layout.addWidget(self.btn_artnet_badge)

        self.btn_blackout = QPushButton("○ Blackout")
        self.btn_blackout.setObjectName("BlackoutBtn")
        self.btn_blackout.clicked.connect(self._on_blackout_clicked)
        pbar_layout.addWidget(self.btn_blackout)

        self.btn_play_stop = QPushButton("▶ Play")
        self.btn_play_stop.setObjectName("PlayStopToggleBtn")
        self.btn_play_stop.setProperty("state", "play")
        self.btn_play_stop.clicked.connect(self._on_play_stop_toggled)
        pbar_layout.addWidget(self.btn_play_stop)

        root_layout.addWidget(program_bar_frame)

        # -------------------------------------------------------------
        # WORKSPACE AREA (QStackedWidget)
        # -------------------------------------------------------------
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {Theme.BG_ROOT};")

        # 1. Address Tab
        self.tab_address = AddressTab(self.project_state, self)
        self.tab_address.patch_changed.connect(self._on_patch_changed)
        self.stack.addWidget(self.tab_address)

        # 2. Analyze Tab
        self.tab_analyze = AnalyzeTab(self.project_state, self)
        self.tab_analyze.analysis_ready.connect(self._on_analysis_ready)
        self.stack.addWidget(self.tab_analyze)

        # 3. Result Tab
        self.tab_result = ResultTab(self.project_state, self)
        self.tab_result.export_to_perform.connect(self._on_export_to_perform)
        self.tab_result.reanalyze_requested.connect(lambda: self._switch_workspace(1))
        self.stack.addWidget(self.tab_result)

        # 4. Perform Tab
        self.tab_perform = PerformTab(self.project_state, self)
        self.tab_perform.export_to_page.connect(self._on_export_to_page)
        self.stack.addWidget(self.tab_perform)

        # 5. Page Tab
        self.tab_page = PageTab(self)
        self.tab_page.cue_activated.connect(self._on_cue_activated)
        self.stack.addWidget(self.tab_page)

        # 6. Mixer Tab
        self.tab_mixer = MixerTab(self.project_state, self)
        self.tab_mixer.fader_changed.connect(self._on_fader_moved)
        self.stack.addWidget(self.tab_mixer)

        root_layout.addWidget(self.stack, 1)

    def _init_shortcuts(self) -> None:
        """Global Keyboard Shortcuts."""
        # F1 to F6: Direct workspace tab switching
        for i in range(6):
            act = QAction(self)
            act.setShortcut(QKeySequence(f"F{i+1}"))
            act.triggered.connect(lambda _, idx=i: self._switch_workspace(idx))
            self.addAction(act)

        # Space: Toggle Play / Stop
        act_play = QAction(self)
        act_play.setShortcut(QKeySequence(Qt.Key_Space))
        act_play.triggered.connect(self._on_play_stop_toggled)
        self.addAction(act_play)

        # Escape / B: Blackout
        act_blackout = QAction(self)
        act_blackout.setShortcut(QKeySequence(Qt.Key_Escape))
        act_blackout.triggered.connect(self._on_blackout_clicked)
        self.addAction(act_blackout)

        # Global Undo: Ctrl+Z
        act_undo = QAction(self)
        act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        act_undo.triggered.connect(self.tab_address.undo_patch)
        self.addAction(act_undo)

        # Global Redo: Ctrl+Shift+Z / Ctrl+Y
        act_redo = QAction(self)
        act_redo.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        act_redo.triggered.connect(self.tab_address.redo_patch)
        self.addAction(act_redo)

    def _switch_workspace(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if 0 <= index < len(self.tab_buttons):
            self.tab_buttons[index].setChecked(True)

    def _update_title_bar(self) -> None:
        self.lbl_project_path.setText(f"[{self.current_project_path}]")
        self.setWindowTitle(f"ZZLUXORA — {Path(self.current_project_path).name}")

    # -----------------------------------------------------------------
    # MENU POP-UP ACTIONS (WINDOWED INDEPENDENT TOOLS)
    # -----------------------------------------------------------------
    def _on_open_fixture_list(self) -> None:
        if self.win_fixture_list is None:
            self.win_fixture_list = FixtureListWindow()
        self.win_fixture_list.show()
        self.win_fixture_list.raise_()
        self.win_fixture_list.activateWindow()

    def _on_open_fixture_editor(self) -> None:
        if self.win_fixture_editor is None:
            self.win_fixture_editor = FixtureEditorWindow()
        self.win_fixture_editor.show()
        self.win_fixture_editor.raise_()
        self.win_fixture_editor.activateWindow()

    def _on_open_visualizer(self) -> None:
        if self.win_visualizer is None:
            self.win_visualizer = StageVisualizerWindow()
        self.win_visualizer.show()
        self.win_visualizer.raise_()
        self.win_visualizer.activateWindow()

    def _on_open_settings(self) -> None:
        dlg = SettingsDialog(self.target_ip, self.target_universe, self)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec()

    def _on_settings_saved(self, ip: str, port: int, universe: int) -> None:
        self.target_ip = ip
        self.target_port = port
        self.target_universe = universe
        self.artnet_sender.close()
        self.artnet_sender = ArtNetSender(target_ip=ip, universe=universe, port=port)

    def _on_open_help(self) -> None:
        dlg = HelpDialog(self)
        dlg.exec()

    def _on_open_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()

    # -----------------------------------------------------------------
    # STAGE CONTROLS: BLACKOUT & PLAY/STOP
    # -----------------------------------------------------------------
    def _on_blackout_clicked(self) -> None:
        self.tab_mixer.apply_blackout()
        for i in range(512):
            self.dmx_buffer[i] = 0
        self.artnet_sender.blackout()
        if self.win_visualizer and self.win_visualizer.isVisible():
            self.win_visualizer.update_dmx([0] * 512)

    def _on_play_stop_toggled(self) -> None:
        self.is_transmitting = not self.is_transmitting

        if self.is_transmitting:
            # Change button to STOP (Red)
            self.btn_play_stop.setText("■ Stop")
            self.btn_play_stop.setProperty("state", "stop")
            self.btn_play_stop.style().polish(self.btn_play_stop)

            # Update Art-Net badge to TRANSMITTING (Green)
            self.btn_artnet_badge.setText("ART-NET: TRANSMITTING")
            self.btn_artnet_badge.setProperty("connected", "true")
            self.btn_artnet_badge.style().polish(self.btn_artnet_badge)

            # Transmit immediately on play
            self.artnet_sender.send_raw(self.dmx_buffer)
            self.stream_timer.start()
        else:
            # Change button to PLAY (Green)
            self.btn_play_stop.setText("▶ Play")
            self.btn_play_stop.setProperty("state", "play")
            self.btn_play_stop.style().polish(self.btn_play_stop)

            # Update Art-Net badge to IDLE (Red)
            self.btn_artnet_badge.setText("ART-NET: IDLE")
            self.btn_artnet_badge.setProperty("connected", "false")
            self.btn_artnet_badge.style().polish(self.btn_artnet_badge)

            self.stream_timer.stop()

    def _stream_artnet_packet(self) -> None:
        if self.is_transmitting:
            self.artnet_sender.send_raw(self.dmx_buffer)
            if self.win_visualizer and self.win_visualizer.isVisible():
                self.win_visualizer.update_dmx(self.dmx_buffer)

    def _on_fader_moved(self, ch_id: int, val: int) -> None:
        master_val = self.tab_mixer.master_fader.value
        master_dim = master_val / 255.0

        if ch_id == 0:
            # Grand Master moved: scale all 256 channels
            for ch in range(1, 257):
                raw = self.tab_mixer.faders[ch].value
                self.dmx_buffer[ch - 1] = int(round(raw * master_dim))
        elif 1 <= ch_id <= 512:
            self.dmx_buffer[ch_id - 1] = int(round(val * master_dim))

        if self.is_transmitting:
            self.artnet_sender.send_raw(self.dmx_buffer)

        if self.win_visualizer and self.win_visualizer.isVisible():
            self.win_visualizer.update_dmx(self.dmx_buffer)

    def _on_patch_changed(self) -> None:
        pass

    # -----------------------------------------------------------------
    # WORKFLOW INTEGRATION ACROSS TABS
    # -----------------------------------------------------------------
    def _on_analysis_ready(self, res: dict) -> None:
        self.tab_result.load_analysis_result(res)
        self._switch_workspace(2)  # Switch to Result tab

    def _on_export_to_perform(self, song_res: dict) -> None:
        self.tab_perform.add_analyzed_song(song_res)
        self._switch_workspace(3)  # Switch to Perform tab

    def _on_export_to_page(self, cues: list) -> None:
        self.tab_page.load_cues(cues)
        self._switch_workspace(4)  # Switch to Page tab

    def _on_cue_activated(self, cue_info: dict) -> None:
        pal = cue_info.get("color", {})
        r = pal.get("R", 255)
        g = pal.get("G", 255)
        b = pal.get("B", 255)
        w = pal.get("W", 0)
        dim = cue_info.get("dimmer", 255) if cue_info.get("active", True) else 0

        # Apply to channels 1-16 (4 PAR LEDs)
        for par in range(4):
            base = par * 4
            self.dmx_buffer[base] = int(r * dim / 255.0)
            self.dmx_buffer[base + 1] = int(g * dim / 255.0)
            self.dmx_buffer[base + 2] = int(b * dim / 255.0)
            self.dmx_buffer[base + 3] = int(w * dim / 255.0)

            # Sync faders in MixerTab silently
            self.tab_mixer.set_channel_value(base + 1, self.dmx_buffer[base], silent=True)
            self.tab_mixer.set_channel_value(base + 2, self.dmx_buffer[base + 1], silent=True)
            self.tab_mixer.set_channel_value(base + 3, self.dmx_buffer[base + 2], silent=True)
            self.tab_mixer.set_channel_value(base + 4, self.dmx_buffer[base + 3], silent=True)

        if self.win_visualizer and self.win_visualizer.isVisible():
            self.win_visualizer.update_dmx(self.dmx_buffer)

    # -----------------------------------------------------------------
    # FILE MANAGEMENT (.zlx)
    # -----------------------------------------------------------------
    def _on_open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Buka File Proyek ZZLUXORA",
            "",
            "ZZLUXORA Project (*.zlx);;All Files (*.*)",
        )
        if path:
            self.current_project_path = path
            self._update_title_bar()
            QMessageBox.information(self, "Project Dimuat", f"Proyek berhasil dibuka:\n{Path(path).name}")

    def _on_save_project(self) -> None:
        if self.current_project_path == "Untitled.zlx":
            self._on_save_as_project()
        else:
            QMessageBox.information(self, "Project Disimpan", f"Proyek berhasil disimpan ke:\n{self.current_project_path}")

    def _on_save_as_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Proyek ZZLUXORA",
            "Untitled.zlx",
            "ZZLUXORA Project (*.zlx)",
        )
        if path:
            self.current_project_path = path
            self._update_title_bar()
            QMessageBox.information(self, "Project Disimpan", f"Proyek berhasil disimpan ke:\n{Path(path).name}")

    def closeEvent(self, event) -> None:
        self.stream_timer.stop()
        self.artnet_sender.blackout()
        self.artnet_sender.close()
        # Close all child windows
        if self.win_fixture_list: self.win_fixture_list.close()
        if self.win_fixture_editor: self.win_fixture_editor.close()
        if self.win_visualizer: self.win_visualizer.close()
        event.accept()

"""
main_window.py — Master Window for ZZLUXORA Lighting Console
Integrates Header Bar, Menu Bar, Collapsible Sidebar, and Multi-View Panels.
"""

import sys
import os
try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QFrame, QStackedWidget, QMenuBar, QMenu,
        QFileDialog, QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
        QHeaderView
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QAction, QKeySequence, QIcon
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QMainWindow: pass

from ui.styles import Theme, CONSOLE_QSS
from ui.sidebar import Sidebar
from ui.panels.program_panel import ProgramPanel
from ui.panels.fixture_list import FixtureList
from ui.panels.fixture_editor import FixtureEditor
from ui.panels.settings_panel import SettingsPanel
from ui.panels.about_panel import AboutPanel
from core.artnet_sender import ArtNetSender
from core.project_io import ProjectIO
from core.models import ProjectState

class KeyboardShortcutsDialog(QDialog if HAS_QT else object):
    """Clean, un-cluttered shortcut cheat sheet window."""
    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setWindowTitle("Shortcut")
        self.setFixedSize(460, 420)
        self.setStyleSheet(CONSOLE_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("TABEL SHORTCUT KEYBOARD")
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #00e5ff;")
        layout.addWidget(lbl)

        table = QTableWidget(9, 2)
        table.setHorizontalHeaderLabels(["Aksi", "Tombol Pintas"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        shortcuts = [
            ("Open Project (.zlx)", "Ctrl + O"),
            ("Save Project (.zlx)", "Ctrl + S"),
            ("Save As Project", "Ctrl + Shift + S"),
            ("Navigasi: Program", "Ctrl + 1"),
            ("Navigasi: Fixture List", "Ctrl + 2"),
            ("Navigasi: Fixture Editor", "Ctrl + 3"),
            ("Navigasi: Settings", "Ctrl + 4"),
            ("Navigasi: About", "Ctrl + 5 / Ctrl + H"),
            ("Toggle Play / Pause", "Space"),
        ]
        for row, (act, key) in enumerate(shortcuts):
            i1 = QTableWidgetItem(act)
            i2 = QTableWidgetItem(key)
            i1.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            i2.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, i1)
            table.setItem(row, 1, i2)

        layout.addWidget(table)

        btn_close = QPushButton("Tutup")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)


class MainWindow(QMainWindow):
    """Main Production Lighting Console Window."""
    def __init__(self):
        if not HAS_QT: return
        super().__init__()
        self.setWindowTitle("ZZLUXORA — Stage Lighting Console")
        self.resize(1280, 800)
        self.setStyleSheet(CONSOLE_QSS)

        # Core Engines
        self.artnet_sender = ArtNetSender(target_ip="192.168.4.1", universe=0)
        self.project_state = ProjectState(project_name="untitled.zlx")
        self.project_file_path = "untitled.zlx"
        self.is_playing = False

        self._init_menu_bar()
        self._init_ui()

    def _init_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        menu_file = menu_bar.addMenu("File")

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
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        # View Menu
        menu_view = menu_bar.addMenu("View")

        views = [
            ("Program", "Ctrl+1", "program"),
            ("Fixture List", "Ctrl+2", "fixture_list"),
            ("Fixture Editor", "Ctrl+3", "fixture_editor"),
            ("Settings", "Ctrl+4", "settings"),
            ("About", "Ctrl+5", "about")
        ]
        for name, shortcut, key in views:
            act = QAction(name, self)
            act.setShortcut(QKeySequence(shortcut))
            act.triggered.connect(lambda ch=False, k=key: self._switch_view(k))
            menu_view.addAction(act)

        # Help Menu
        menu_help = menu_bar.addMenu("Help")
        act_about = QAction("About", self)
        act_about.setShortcut(QKeySequence("Ctrl+H"))
        act_about.triggered.connect(lambda: self._switch_view("about"))
        menu_help.addAction(act_about)

        act_shortcuts = QAction("Keyboard Shortcuts", self)
        act_shortcuts.triggered.connect(self._on_show_shortcuts)
        menu_help.addAction(act_shortcuts)

    def _init_ui(self):
        root_widget = QWidget(self)
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Header Bar
        header = QFrame(self)
        header.setObjectName("HeaderBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)

        # Left Header: Hamburger + Lamp Logo + Brand + Project Name
        self.btn_hamburger = QPushButton("☰")
        self.btn_hamburger.setFixedSize(32, 32)
        self.btn_hamburger.setStyleSheet("font-size: 16px; font-weight: bold; padding: 2px;")
        self.btn_hamburger.clicked.connect(self._toggle_sidebar)
        header_layout.addWidget(self.btn_hamburger)

        lbl_logo = QLabel("💡")
        lbl_logo.setStyleSheet("font-size: 18px; margin-left: 6px;")
        header_layout.addWidget(lbl_logo)

        lbl_brand = QLabel("ZZLUXORA")
        lbl_brand.setObjectName("LogoTitle")
        header_layout.addWidget(lbl_brand)

        self.lbl_project_name = QLabel(f"[{self.project_file_path}]")
        self.lbl_project_name.setObjectName("ProjectPath")
        header_layout.addWidget(self.lbl_project_name)

        header_layout.addStretch()

        # Right Header: Art-Net Indicator, Play/Pause, Blackout
        self.lbl_artnet_status = QLabel("● Art-Net Connected (192.168.4.1)")
        self.lbl_artnet_status.setObjectName("ArtNetStatusConnected")
        header_layout.addWidget(self.lbl_artnet_status)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setObjectName("PlayPauseBtn")
        self.btn_play.clicked.connect(self._toggle_play)
        header_layout.addWidget(self.btn_play)

        self.btn_blackout = QPushButton("BLACKOUT")
        self.btn_blackout.setObjectName("BlackoutBtn")
        self.btn_blackout.clicked.connect(self._on_master_blackout)
        header_layout.addWidget(self.btn_blackout)

        root_layout.addWidget(header)

        # 2. Main Body Area (Sidebar Left + Stacked Content Right)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.view_changed.connect(self._switch_view)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget(self)

        self.panel_program = ProgramPanel(artnet_sender=self.artnet_sender)
        self.panel_fixture_list = FixtureList()
        self.panel_fixture_editor = FixtureEditor()
        self.panel_settings = SettingsPanel()
        self.panel_about = AboutPanel()

        self.stack.addWidget(self.panel_program)       # index 0
        self.stack.addWidget(self.panel_fixture_list)  # index 1
        self.stack.addWidget(self.panel_fixture_editor)# index 2
        self.stack.addWidget(self.panel_settings)      # index 3
        self.stack.addWidget(self.panel_about)         # index 4

        body_layout.addWidget(self.stack)
        root_layout.addLayout(body_layout)

        self.setCentralWidget(root_widget)

    def _toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _switch_view(self, key: str):
        mapping = {
            "program": 0,
            "fixture_list": 1,
            "fixture_editor": 2,
            "settings": 3,
            "about": 4
        }
        idx = mapping.get(key, 0)
        self.stack.setCurrentIndex(idx)
        self.sidebar.set_active(key)

    def _toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.setText("⏸ Pause")
            self.btn_play.setStyleSheet("background-color: #2b2311; border-color: #ffb300; color: #ffb300; font-weight: bold;")
        else:
            self.btn_play.setText("▶ Play")
            self.btn_play.setStyleSheet("background-color: #0d2621; border-color: #00e676; color: #00e676; font-weight: bold;")

    def _on_master_blackout(self):
        self.artnet_sender.blackout()
        self.panel_program.tab_mixer.reset_all_to_zero()
        QMessageBox.information(self, "Blackout", "Master Blackout diaktifkan: seluruh 512 kanal DMX dipadamkan (nilai 0).")

    def _on_open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Buka Berkas Project ZZLUXORA", "", "ZZLUXORA Project (*.zlx)")
        if file_path:
            self.project_file_path = file_path
            self.lbl_project_name.setText(f"[{os.path.basename(file_path)}]")
            QMessageBox.information(self, "Project Dimuat", f"Project berhasil dibuka: {file_path}")

    def _on_save_project(self):
        if self.project_file_path == "untitled.zlx":
            self._on_save_as_project()
        else:
            ProjectIO.save_project(self.project_state, self.project_file_path)
            QMessageBox.information(self, "Disimpan", "Project tersimpan!")

    def _on_save_as_project(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Simpan Project Sebagai", "my_worship_service.zlx", "ZZLUXORA Project (*.zlx)")
        if file_path:
            self.project_file_path = file_path
            self.lbl_project_name.setText(f"[{os.path.basename(file_path)}]")
            ProjectIO.save_project(self.project_state, file_path)
            QMessageBox.information(self, "Disimpan", f"Project tersimpan di {file_path}")

    def _on_show_shortcuts(self):
        dlg = KeyboardShortcutsDialog(self)
        dlg.exec()

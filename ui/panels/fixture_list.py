"""
fixture_list.py | Standalone Floating Fixture Library Window
Provides a resizable tool window with drag-and-drop support into the DMX Address grid.
"""

from __future__ import annotations
import json
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSplitter, QTextEdit, QIcon,
    Qt, QMimeData, QPoint, QDrag, QFont
)
from ui.styles import Theme, CONSOLE_QSS


class DraggableFixtureListWidget(QListWidget if HAS_QT else object):
    """ListWidget supporting dragging fixture profiles onto the Address grid."""
    def __init__(self, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item: return

        fixture_data = item.data(Qt.UserRole)
        if not fixture_data: return

        drag = QDrag(self)
        mime = QMimeData()
        payload = json.dumps(fixture_data)
        mime.setData("application/x-zzluxora-fixture", payload.encode("utf-8"))
        mime.setText(payload)

        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


class FixtureListWindow(QWidget if HAS_QT else object):
    """Standalone resizable floating window for browsing and dragging fixture profiles."""
    def __init__(self, fixtures_dir: Path | None = None, parent: QWidget | None = None):
        if not HAS_QT: return
        # Set as an independent window with minimize, maximize, and close buttons
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Fixture Library")
        self.resize(520, 480)
        self.setStyleSheet(CONSOLE_QSS)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_zz.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self.fixtures_dir = fixtures_dir or (Path.home() / "ANDREAS" / "zzluxora_v10" / "fixtures")
        self._init_ui()
        self.reload_fixtures()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # Splitter: Top List, Bottom Channel Inspector (No decorative headers)
        splitter = QSplitter(Qt.Vertical)

        self.list_widget = DraggableFixtureListWidget(self)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {Theme.BORDER_SUBTLE};
            }}
            QListWidget::item:selected {{
                background-color: {Theme.BG_ELEVATED};
                border-left: 3px solid {Theme.ACCENT_CYAN};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.list_widget.currentItemChanged.connect(self._on_item_selected)
        splitter.addWidget(self.list_widget)

        # Inspector preview directly in splitter without groupbox title
        self.inspector_text = QTextEdit()
        self.inspector_text.setReadOnly(True)
        self.inspector_text.setPlaceholderText("Select a fixture profile to view DMX channel footprint...")
        self.inspector_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.SURFACE_INPUT};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                color: {Theme.TEXT_SECONDARY};
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 11px;
                padding: 6px;
            }}
        """)
        splitter.addWidget(self.inspector_text)

        # Center splitter divider by default
        splitter.setSizes([220, 220])
        main_layout.addWidget(splitter, 1)

        # Bottom Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.btn_refresh = QPushButton("RELOAD")
        self.btn_refresh.setStyleSheet(f"background-color: {Theme.COLOR_SUCCESS}; color: {Theme.BG_ROOT}; font-weight: bold; padding: 6px 14px; border-radius: 4px; border: none;")
        self.btn_refresh.clicked.connect(self.reload_fixtures)
        btn_bar.addWidget(self.btn_refresh)

        self.btn_close = QPushButton("CLOSE")
        self.btn_close.setStyleSheet("padding: 6px 14px; border-radius: 4px;")
        self.btn_close.clicked.connect(self.close)
        btn_bar.addWidget(self.btn_close)

        main_layout.addLayout(btn_bar)

    def reload_fixtures(self) -> None:
        self.list_widget.clear()
        if not self.fixtures_dir.exists():
            return

        # Strictly load official .zfx fixture definitions
        files = sorted(list(self.fixtures_dir.glob("*.zfx")))
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    name = data.get("name", f.stem)
                    mfr = data.get("manufacturer", "Generic")

                    # Display clean name (Alien-AL36, Kumastb-STL47)
                    item = QListWidgetItem(name)
                    item.setData(Qt.UserRole, data)
                    self.list_widget.addItem(item)
            except Exception:
                continue

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_item_selected(self, current: QListWidgetItem | None, previous) -> None:
        if not current:
            self.inspector_text.clear()
            return
        data = current.data(Qt.UserRole)
        if not data: return

        channels = data.get("channels", [])
        model_name = data.get("model") or data.get("name", "Unknown")
        lines = [
            f"Model\t\t: {model_name}",
            f"Manufacture\t: {data.get('manufacturer', 'Generic')}",
            f"Channel\t\t: {len(channels)}",
            "-" * 36,
        ]
        for ch in channels:
            idx = ch.get("index", 1)
            lbl = ch.get("label", "Channel")
            ctype = ch.get("type", "dimmer")
            lines.append(f"{idx:02d}\t| {lbl} ({ctype.title()})")

        self.inspector_text.setPlainText("\n".join(lines))

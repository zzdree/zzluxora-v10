"""
program_panel.py — Program Container Hosting All 8 Modular Console Tabs
Organizes Address, Analyze, Scenes, Chase, Page, Mixer, Preview, and Output.
"""

try:
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
    HAS_QT = True
except ImportError:
    HAS_QT = False
    class QWidget: pass

from ui.panels.address_tab import AddressTab
from ui.panels.analyze_tab import AnalyzeTab
from ui.panels.scenes_tab import ScenesTab
from ui.panels.chase_tab import ChaseTab
from ui.panels.page_tab import PageTab
from ui.panels.mixer_tab import MixerTab
from ui.panels.preview_tab import PreviewTab
from ui.panels.output_tab import OutputTab

class ProgramPanel(QWidget):
    """Main Program Workbench holding all 8 operational console tabs."""
    def __init__(self, core_engine=None, artnet_sender=None, parent=None):
        if not HAS_QT: return
        super().__init__(parent)
        self.core_engine = core_engine
        self.artnet_sender = artnet_sender
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget(self)

        self.tab_address = AddressTab()
        self.tab_analyze = AnalyzeTab(core_engine=self.core_engine)
        self.tab_scenes = ScenesTab()
        self.tab_chase = ChaseTab()
        self.tab_page = PageTab()
        self.tab_mixer = MixerTab(artnet_sender=self.artnet_sender)
        self.tab_preview = PreviewTab()
        self.tab_output = OutputTab(artnet_sender=self.artnet_sender)

        self.tab_widget.addTab(self.tab_address, "Address")
        self.tab_widget.addTab(self.tab_analyze, "Analyze (Core)")
        self.tab_widget.addTab(self.tab_scenes, "Scenes")
        self.tab_widget.addTab(self.tab_chase, "Chase")
        self.tab_widget.addTab(self.tab_page, "Live Page")
        self.tab_widget.addTab(self.tab_mixer, "Mixer 513")
        self.tab_widget.addTab(self.tab_preview, "Preview 2D")
        self.tab_widget.addTab(self.tab_output, "Output Art-Net")

        layout.addWidget(self.tab_widget)

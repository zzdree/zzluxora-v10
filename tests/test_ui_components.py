"""
test_ui_components.py — Unit Tests for ZZLUXORA v10 UI Architecture & Modules
Validates component imports, theme tokens, widgets, and headless window initialization.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class TestUIModules(unittest.TestCase):
    """Verifies that all newly created UI widgets and panels import and initialize cleanly."""

    def test_theme_tokens(self):
        from ui.styles import Theme
        self.assertEqual(Theme.BG_ROOT, "#1e2024")
        self.assertEqual(Theme.TEXT_PRIMARY, "#ffffff")
        self.assertEqual(Theme.ACCENT_AMBER, "#f59e0b")
        self.assertEqual(Theme.ACCENT_CYAN, "#06b6d4")

    def test_ui_panels_import(self):
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
        from ui.widgets.tactile_fader import TactileFader
        from ui.widgets.youtube_dialog import YouTubeDialog

        self.assertTrue(True)

    def test_headless_main_window_instantiation(self):
        from ui.qt_compat import QApplication, HAS_QT
        if not HAS_QT:
            self.skipTest("No Qt binding available in test runner environment")

        from ui.main_window import MainWindow

        # Create or reuse QApplication with offscreen platform
        app = QApplication.instance()
        if app is None:
            app = QApplication(["-platform", "offscreen"])

        win = MainWindow()
        self.assertIsNotNone(win)
        self.assertEqual(len(win.tab_buttons), 6)
        self.assertEqual(win.stack.count(), 6)

        # Check mixer fader count (1 Master + 256 DMX = 257)
        self.assertEqual(len(win.tab_mixer.faders), 257)

        # Test Blackout logic
        win.tab_mixer.set_channel_value(0, 255)
        win.tab_mixer.apply_blackout()
        self.assertEqual(win.tab_mixer.master_fader.value, 0)

        # Test Play / Stop toggle
        self.assertFalse(win.is_transmitting)
        win._on_play_stop_toggled()
        self.assertTrue(win.is_transmitting)
        win._on_play_stop_toggled()
        self.assertFalse(win.is_transmitting)

        win.close()


if __name__ == "__main__":
    unittest.main()

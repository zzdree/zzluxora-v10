"""
test_ui_components.py — Unit tests for ZZLUXORA v10 UI and project fixtures.
"""

import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class TestUIModules(unittest.TestCase):
    """Verifies UI imports, demo showfile patching, and QLC+ workspace agreement."""

    def _application(self):
        from ui.qt_compat import QApplication, HAS_QT
        if not HAS_QT:
            self.skipTest("No Qt binding available in test runner environment")
        app = QApplication.instance()
        if app is None:
            app = QApplication(["-platform", "offscreen"])
        self.__class__._qapp = app
        return app

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
        self.assertTrue(all((AddressTab, AnalyzeTab, ResultTab, PerformTab, PageTab,
                             MixerTab, FixtureListWindow, FixtureEditorWindow,
                             StageVisualizerWindow, SettingsDialog, HelpDialog,
                             AboutDialog, TactileFader, YouTubeDialog)))

    def test_settings_dialog_initializes_adapter_table_with_qcolors(self):
        self._application()
        from ui.panels.settings_panel import SettingsDialog
        dialog = SettingsDialog()
        self.assertGreater(dialog.table_adapters.rowCount(), 0)
        self.assertEqual(dialog.table_adapters.item(0, 0).foreground().color().name(), "#ffffff")
        self.assertEqual(dialog.table_adapters.item(0, 1).foreground().color().name(), "#06b6d4")
        dialog.close()

    def test_demo_showfile_patches_requested_eight_channel_fixture(self):
        self._application()
        from ui.main_window import MainWindow
        win = MainWindow()
        demo_path = BASE_DIR / "showfiles" / "demo_church_worship.zlx"
        with patch("ui.main_window.QMessageBox.information"):
            win.load_project_file(str(demo_path))

        expected = [
            ("dimmer", "Dimmer"), ("red", "Red"), ("green", "Green"),
            ("blue", "Blue"), ("white", "White"), ("strobe", "Strobe"),
            ("program", "Program"), ("speed", "Speed"),
        ]
        for fixture_idx in range(4):
            fixture_name = f"PAR LED {fixture_idx + 1} (8CH)"
            start_channel = fixture_idx * 8 + 1
            for offset, (channel_type, label) in enumerate(expected):
                box = win.tab_address.grid_area.boxes[start_channel + offset]
                self.assertTrue(box.is_patched)
                self.assertEqual((box.channel_type, box.channel_label, box.fixture_name),
                                 (channel_type, label, fixture_name))
        self.assertFalse(win.tab_address.grid_area.boxes[33].is_patched)
        self.assertEqual(len(win.tab_perform.playlist), 3)
        self.assertEqual(len(win.tab_page.executor_buttons), 4)

        win._on_cue_activated({"type": "scene", "active": True, "dimmer": 255,
                               "color": {"R": 100, "G": 80, "B": 60, "W": 40}})
        for fixture_idx in range(4):
            start = fixture_idx * 8
            self.assertEqual(list(win.dmx_buffer[start:start + 8]), [255, 100, 80, 60, 40, 0, 0, 0])
        win.close()

    def test_qlcplus_definition_and_workspace_use_requested_eight_channel_order(self):
        fixtures_dir = BASE_DIR / "fixtures"
        showfiles_dir = BASE_DIR / "showfiles"
        ns = {"q": "http://www.qlcplus.org/FixtureDefinition"}
        qxf = ET.parse(fixtures_dir / "Kumastb-STL47.qxf").getroot()
        expected = ["Dimmer", "Red", "Green", "Blue", "White", "Strobe", "Program", "Speed"]
        names = [node.attrib["Name"] for node in qxf.findall("q:Channel", ns)]
        mode = qxf.find("q:Mode[@Name='Modes']", ns)
        self.assertEqual(names, expected)
        self.assertEqual([node.text for node in mode.findall("q:Channel", ns)], expected)

        workspace = ET.parse(showfiles_dir / "qlcplus_template.qxw").getroot()
        fixtures = workspace.findall("./Engine/Fixture")
        self.assertEqual(len(fixtures), 4)
        self.assertEqual([int(f.findtext("Channels")) for f in fixtures], [8] * 4)
        self.assertEqual([int(f.findtext("Address")) for f in fixtures], [0, 8, 16, 24])

        sliders = workspace.findall("./VirtualConsole/Frame/Slider")
        self.assertEqual(len(sliders), 32)
        for fixture_idx in range(4):
            for channel_idx, channel_name in enumerate(expected):
                slider = sliders[fixture_idx * 8 + channel_idx]
                self.assertEqual(slider.find("Input").get("Channel"), str(fixture_idx * 8 + channel_idx))
                self.assertEqual(slider.find("Level/Channel").get("Fixture"), str(fixture_idx))
                self.assertIn(channel_name, slider.get("Caption"))

    def test_qlc_user_fixture_definition_is_installed_for_qxw(self):
        user_fixture = Path.home() / ".qlcplus" / "fixtures" / "Kumastb" / "Kumastb-STL47.qxf"
        self.assertTrue(user_fixture.is_file(), f"QLC+ user fixture definition missing: {user_fixture}")

    def test_official_kumastb_and_alien_fixtures(self):
        fixtures_dir = BASE_DIR / "fixtures"
        # 1. Test Kumastb STL47 (8CH RGBW) .zfx and .qxf
        kuma_zfx_file = fixtures_dir / "Kumastb-STL47.zfx"
        self.assertTrue(kuma_zfx_file.is_file())
        with open(kuma_zfx_file, "r", encoding="utf-8") as fp:
            kuma_data = json.load(fp)
        self.assertEqual(kuma_data["manufacturer"], "Kumastb")
        self.assertEqual(kuma_data["channel_count"], 8)
        self.assertEqual([ch["label"] for ch in kuma_data["channels"]],
                         ["Dimmer", "Red", "Green", "Blue", "White", "Strobe", "Program", "Speed"])

        kuma_qxf_file = fixtures_dir / "Kumastb-STL47.qxf"
        self.assertTrue(kuma_qxf_file.is_file())
        ns = {"q": "http://www.qlcplus.org/FixtureDefinition"}
        qxf_kuma = ET.parse(kuma_qxf_file).getroot()
        self.assertEqual([node.attrib["Name"] for node in qxf_kuma.findall("q:Channel", ns)],
                         ["Dimmer", "Red", "Green", "Blue", "White", "Strobe", "Program", "Speed"])

        # 2. Test Alien AL36 (8CH RGB) .zfx and .qxf
        alien_zfx_file = fixtures_dir / "Alien-AL36.zfx"
        self.assertTrue(alien_zfx_file.is_file())
        with open(alien_zfx_file, "r", encoding="utf-8") as fp:
            alien_data = json.load(fp)
        self.assertEqual(alien_data["manufacturer"], "Alien")
        self.assertEqual(alien_data["channel_count"], 8)
        self.assertEqual([ch["label"] for ch in alien_data["channels"]],
                         ["Dimmer", "Red", "Green", "Blue", "Empty", "Program", "Speed", "Emptz"])

        alien_qxf_file = fixtures_dir / "Alien-AL36.qxf"
        self.assertTrue(alien_qxf_file.is_file())
        qxf_alien = ET.parse(alien_qxf_file).getroot()
        self.assertEqual([node.attrib["Name"] for node in qxf_alien.findall("q:Channel", ns)],
                         ["Dimmer", "Red", "Green", "Blue", "Empty", "Program", "Speed", "Emptz"])

        # 3. Test FixtureProfile factory methods
        from core.models import FixtureProfile
        kuma_prof = FixtureProfile.create_kumastb_stl47()
        self.assertEqual(kuma_prof.manufacturer, "Kumastb")
        self.assertEqual(kuma_prof.channel_count, 8)
        alien_prof = FixtureProfile.create_alien_al36()
        self.assertEqual(alien_prof.manufacturer, "Alien")
        self.assertEqual(alien_prof.channel_count, 8)

    def test_headless_main_window_instantiation(self):
        self._application()
        from ui.main_window import MainWindow
        win = MainWindow()
        self.assertIsNotNone(win)
        self.assertEqual(len(win.tab_buttons), 6)
        self.assertEqual(win.stack.count(), 6)
        self.assertEqual(len(win.tab_mixer.faders), 257)
        win.tab_mixer.set_channel_value(0, 255)
        win.tab_mixer.apply_blackout()
        self.assertEqual(win.tab_mixer.master_fader.value, 0)
        self.assertFalse(win.is_transmitting)
        win._on_play_stop_toggled()
        self.assertTrue(win.is_transmitting)
        win._on_play_stop_toggled()
        self.assertFalse(win.is_transmitting)
        win.close()


if __name__ == "__main__":
    unittest.main()

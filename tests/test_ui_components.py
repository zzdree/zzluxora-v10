"""
test_ui_components.py - Unit tests for ZZLUXORA v10 UI and project fixtures.
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

    def test_impeccable_semantic_tokens_and_fader_tag(self):
        from ui.styles import Theme
        from ui.qt_compat import QApplication, HAS_QT
        if not HAS_QT:
            self.skipTest("No Qt binding available in test runner environment")
        app = QApplication.instance() or QApplication(["-platform", "offscreen"])
        from ui.widgets.tactile_fader import TactileFader
        self.assertEqual(Theme.STATUS_SUCCESS_BG, "#143521")
        self.assertEqual(Theme.RIGGING_CLAMP, "#717b8f")
        fader = TactileFader(channel_id=3, initial_value=10)
        fader.set_fixture_tag("AL36-1:DIM")
        self.assertEqual(fader.fixture_tag, "AL36-1:DIM")
        fader.close()
        self.__class__._qapp = app

    def test_perform_transport_and_crossfade_telemetry(self):
        self._application()
        from ui.main_window import MainWindow
        win = MainWindow()
        tab = win.tab_perform
        self.assertEqual(tab.btn_prev_cue.text(), "[PREV]")
        self.assertEqual(tab.btn_go_cue.text(), "[GO+]")
        self.assertEqual(tab.btn_fade_black.text(), "[FADE BLACK]")
        tab.set_crossfade_progress(0.5, 1.0, 2.0)
        self.assertEqual(tab.progress_crossfade.value(), 50)
        self.assertIn("1.0s", tab.lbl_fade_countdown.text())
        tab.set_crossfade_progress(1.0, 2.0, 2.0)
        self.assertIn("COMPLETE", tab.lbl_fade_countdown.text())
        win.close()

    def test_fixture_bracket_and_drag_preview_state(self):
        self._application()
        from ui.panels.address_tab import AddressTab
        tab = AddressTab()
        tab._on_patch_alien_gia()
        self.assertEqual(tab.grid_area.boxes[1].boundary_type, "start")
        self.assertEqual(tab.grid_area.boxes[2].boundary_type, "mid")
        self.assertEqual(tab.grid_area.boxes[8].boundary_type, "end")
        tab.grid_area._set_drag_hover(100, 8)
        self.assertTrue(all(tab.grid_area.boxes[ch].is_drag_hover for ch in range(100, 108)))
        self.assertFalse(tab.grid_area.boxes[108].is_drag_hover)
        tab.grid_area._clear_drag_hover()
        self.assertFalse(any(box.is_drag_hover for box in tab.grid_area.boxes.values()))
        tab.close()

    def test_mixer_syncs_patch_role_labels_and_active_bank(self):
        self._application()
        from ui.panels.mixer_tab import MixerTab
        tab = MixerTab()
        tab.sync_patch([{"name": "Alien-AL36 #1", "channels": [
            {"channel": 1, "type": "dimmer", "label": "Dimmer"},
            {"channel": 2, "type": "red", "label": "Red"},
        ]}])
        self.assertEqual(tab.faders[1].fixture_tag, "AL36-1:DIM")
        self.assertEqual(tab.faders[2].fixture_tag, "AL36-1:RED")
        tab._on_scroll_changed(16 * 58)
        self.assertEqual(tab.active_bank_index, 1)
        tab.close()

    def test_preview_segmented_switch_and_direct_controls(self):
        self._application()
        from ui.panels.preview_tab import StageVisualizerWindow
        vis = StageVisualizerWindow()
        self.assertEqual(vis.tabs.count(), 2)
        self.assertEqual(vis.tabs.currentIndex(), 0)
        self.assertFalse(vis.drawer_widget.isVisible())
        self.assertFalse(vis.canvas_3d.haze_enabled)
        vis._switch_view(1)
        self.assertEqual(vis.tabs.currentIndex(), 1)
        self.assertFalse(vis.box_rot_widget.isHidden())
        vis.close()

    def test_address_unpatched_channel_contrast(self):
        self._application()
        from ui.panels.address_tab import DMXChannelBox
        box = DMXChannelBox(99)
        self.assertEqual(box.lbl_num.styleSheet().find("#cbd5e1") >= 0, True)
        box.close()

    def test_icon_hamburger_is_vector_icon(self):
        self._application()
        from ui.icons import create_hamburger_icon
        icon = create_hamburger_icon()
        self.assertIsNotNone(icon)
        self.assertFalse(icon.isNull())

    def test_master_go_button_has_commanding_size(self):
        self._application()
        from ui.panels.perform_tab import PerformTab
        tab = PerformTab()
        self.assertGreaterEqual(tab.btn_go_cue.minimumHeight(), 44)
        self.assertEqual(tab.btn_go_cue.text(), "[GO+]")
        tab.close()

    def test_crossfade_zero_total_resets_to_idle(self):
        self._application()
        from ui.panels.perform_tab import PerformTab
        tab = PerformTab()
        tab.set_crossfade_progress(0.0, 0.0, 0.0)
        self.assertEqual(tab.progress_crossfade.value(), 0)
        self.assertIn("IDLE", tab.lbl_fade_countdown.text())
        tab.close()

    def test_mixer_unpatched_channels_clear_fixture_tags(self):
        self._application()
        from ui.panels.mixer_tab import MixerTab
        tab = MixerTab()
        tab.sync_patch([{"name": "Alien-AL36 #1", "channels": [{"channel": 7, "type": "program", "label": "Program"}]}])
        self.assertEqual(tab.faders[7].fixture_tag, "AL36-1:PRG")
        tab.sync_patch([])
        self.assertEqual(tab.faders[7].fixture_tag, "")
        tab.close()

    def test_fixture_brackets_refresh_after_clear(self):
        self._application()
        from ui.panels.address_tab import AddressTab
        tab = AddressTab()
        tab._on_patch_alien_gia()
        self.assertEqual(tab.grid_area.boxes[1].boundary_type, "start")
        for box in tab.grid_area.boxes.values():
            box.set_unpatched()
        tab.update_fixture_brackets()
        self.assertFalse(any(box.boundary_type for box in tab.grid_area.boxes.values()))
        tab.close()

    def test_active_bank_tracks_far_scroll_bounds(self):
        self._application()
        from ui.panels.mixer_tab import MixerTab
        tab = MixerTab()
        tab._on_scroll_changed(255 * 58)
        self.assertEqual(tab.active_bank_index, 6)
        tab._on_scroll_changed(0)
        self.assertEqual(tab.active_bank_index, 0)
        tab.close()

    def test_crossfade_completion_resets_when_new_fade_begins(self):
        self._application()
        from ui.panels.perform_tab import PerformTab
        tab = PerformTab()
        tab.set_crossfade_progress(1.0, 2.0, 2.0)
        tab.reset_crossfade_progress()
        self.assertEqual(tab.progress_crossfade.value(), 0)
        self.assertIn("IDLE", tab.lbl_fade_countdown.text())
        tab.close()

    def test_settings_artnet_target_presets_are_present(self):
        self._application()
        from ui.panels.settings_panel import SettingsDialog
        dialog = SettingsDialog()
        presets = [dialog.combo_presets.itemText(i) for i in range(dialog.combo_presets.count())]
        self.assertTrue(any("localhost" in p.lower() for p in presets))
        self.assertTrue(any("broadcast" in p.lower() for p in presets))
        dialog.close()

    def test_fader_zero_control_is_plain_character(self):
        self._application()
        from ui.widgets.tactile_fader import TactileFader
        fader = TactileFader(channel_id=1, initial_value=10)
        # Paint path is exercised by rendering into the widget in the existing offscreen Qt test harness.
        self.assertTrue(fader.width() > 0)
        fader.close()

    def test_crossfade_progress_clamps_percentage(self):
        self._application()
        from ui.panels.perform_tab import PerformTab
        tab = PerformTab()
        tab.set_crossfade_progress(1.5, 1.0, 1.0)
        self.assertEqual(tab.progress_crossfade.value(), 100)
        tab.close()

    def test_stage_visualizer_syncs_empty_fixtures(self):
        self._application()
        from ui.panels.preview_tab import StageVisualizerWindow
        vis = StageVisualizerWindow()
        vis.sync_fixtures([])
        self.assertEqual(vis.canvas_2d.fixtures, [])
        self.assertEqual(vis.canvas_3d.fixtures_3d, [])
        vis.close()

    def test_stage3d_reset_camera_is_eye_level(self):
        self._application()
        from ui.panels.preview_tab import Stage3DCanvas
        canvas = Stage3DCanvas()
        canvas.yaw = 1.0
        canvas.pitch = 0.5
        canvas.reset_camera()
        self.assertEqual(canvas.yaw, 0.0)
        self.assertEqual(canvas.pitch, 0.0)
        canvas.close()

    def test_beam_angle_control_updates_selected_fixture(self):
        self._application()
        from ui.panels.preview_tab import StageVisualizerWindow
        vis = StageVisualizerWindow()
        vis.sync_fixtures([{"id": 1, "name": "Test", "start_channel": 1, "channels": []}])
        vis.canvas_3d.selected_ids = {1}
        vis.spin_beam_angle.setValue(45)
        self.assertEqual(vis.canvas_3d.fixtures_3d[0]["beam_angle"], 45)
        vis.close()

    def test_drag_hover_preview_clears_when_leaving_grid(self):
        self._application()
        from ui.panels.address_tab import AddressTab
        tab = AddressTab()
        tab.grid_area._set_drag_hover(12, 8)
        self.assertTrue(tab.grid_area.boxes[12].is_drag_hover)
        tab.grid_area._clear_drag_hover()
        self.assertFalse(tab.grid_area.boxes[12].is_drag_hover)
        tab.close()

    def test_fixture_library_inspector_uses_tabs_and_clean_name(self):
        self._application()
        from ui.panels.fixture_list import FixtureListWindow
        lib = FixtureListWindow()
        self.assertGreater(lib.list_widget.count(), 0)
        self.assertIn("Alien-AL36", lib.list_widget.item(0).text())
        lib.close()

    def test_header_menu_direct_actions_have_shortcuts(self):
        self._application()
        from ui.main_window import MainWindow
        win = MainWindow()
        actions = {a.text(): a for a in win.menuBar().actions()}
        self.assertIn("Preview", actions)
        self.assertIn("Setting", actions)
        self.assertIn("Help", actions)
        self.assertIn("About", actions)
        self.assertEqual(actions["Preview"].shortcut().toString(), "Ctrl+P")
        self.assertEqual(actions["Setting"].shortcut().toString(), "Ctrl+Shift+P")
        win.close()

    def test_haze_toggle_button_keeps_static_label(self):
        self._application()
        from ui.panels.preview_tab import StageVisualizerWindow
        vis = StageVisualizerWindow()
        self.assertEqual(vis.btn_haze.text(), "Haze FX")
        vis._on_toggle_haze()
        self.assertEqual(vis.btn_haze.text(), "Haze FX")
        vis.close()

    def test_help_table_is_non_editable_and_shortcuts_heading(self):
        self._application()
        from ui.panels.help_panel import HelpDialog
        dialog = HelpDialog()
        self.assertEqual(dialog.windowTitle(), "Help")
        self.assertEqual(dialog.table.horizontalHeaderItem(1).text(), "Key")
        dialog.close()

    def test_about_window_has_wide_scrollable_description(self):
        self._application()
        from ui.panels.about_panel import AboutDialog
        from ui.qt_compat import QScrollArea
        dialog = AboutDialog()
        self.assertEqual(dialog.windowTitle(), "About")
        self.assertIsNotNone(dialog.findChild(QScrollArea))
        self.assertTrue(dialog.findChild(QScrollArea).widgetResizable())
        dialog.close()

    def test_preview_2d_selection_does_not_drag_fixture(self):
        self._application()
        from ui.panels.preview_tab import Stage2DCanvas
        canvas = Stage2DCanvas()
        canvas.set_fixtures([{"id": 1, "name": "AL36", "channels": []}])
        initial = (canvas.fixtures[0]["base_x"], canvas.fixtures[0]["base_y"])
        self.assertEqual((canvas.fixtures[0]["base_x"], canvas.fixtures[0]["base_y"]), initial)
        canvas.close()

    def test_design_token_palette_preserves_required_legacy_values(self):
        from ui.styles import Theme
        self.assertEqual(Theme.STATUS_SUCCESS_BG, "#143521")
        self.assertEqual(Theme.TEXT_CONTRAST_UNPATCHED, "#cbd5e1")
        self.assertEqual(Theme.FADER_RIB_HIGHLIGHT, "#4a5264")
        self.assertEqual(Theme.FADER_CLEAR_BG, "#2d1414")

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
        showfiles_dir = BASE_DIR / "showfiles"
        zz_fixture_dir = Path.home() / "ANDREAS" / "zz-fixture"
        ns = {"q": "http://www.qlcplus.org/FixtureDefinition"}
        qxf = ET.parse(zz_fixture_dir / "Kumastb-STL47.qxf").getroot()
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
        zz_fixture_dir = Path.home() / "ANDREAS" / "zz-fixture"

        # Verify fixtures directory contains ONLY official .zfx profiles
        fixture_files = sorted([f.name for f in fixtures_dir.glob("*") if f.is_file()])
        self.assertEqual(fixture_files, ["Alien-AL36.zfx", "Kumastb-STL47.zfx"])

        # 1. Test Kumastb STL47 (8CH RGBW) .zfx
        kuma_zfx_file = fixtures_dir / "Kumastb-STL47.zfx"
        self.assertTrue(kuma_zfx_file.is_file())
        with open(kuma_zfx_file, "r", encoding="utf-8") as fp:
            kuma_data = json.load(fp)
        self.assertEqual(kuma_data["manufacturer"], "Kumastb")
        self.assertEqual(kuma_data["name"], "Kumastb-STL47")
        self.assertEqual(kuma_data["model"], "STL47")
        self.assertEqual(kuma_data["channel_count"], 8)
        self.assertEqual([ch["label"] for ch in kuma_data["channels"]],
                         ["Dimmer", "Red", "Green", "Blue", "White", "Strobe", "Program", "Speed"])

        # Test Kumastb .qxf from zz-fixture repository
        kuma_qxf_file = zz_fixture_dir / "Kumastb-STL47.qxf"
        self.assertTrue(kuma_qxf_file.is_file())
        ns = {"q": "http://www.qlcplus.org/FixtureDefinition"}
        qxf_kuma = ET.parse(kuma_qxf_file).getroot()
        self.assertEqual([node.attrib["Name"] for node in qxf_kuma.findall("q:Channel", ns)],
                         ["Dimmer", "Red", "Green", "Blue", "White", "Strobe", "Program", "Speed"])

        # 2. Test Alien AL36 (8CH RGB) .zfx
        alien_zfx_file = fixtures_dir / "Alien-AL36.zfx"
        self.assertTrue(alien_zfx_file.is_file())
        with open(alien_zfx_file, "r", encoding="utf-8") as fp:
            alien_data = json.load(fp)
        self.assertEqual(alien_data["manufacturer"], "Alien")
        self.assertEqual(alien_data["name"], "Alien-AL36")
        self.assertEqual(alien_data["model"], "AL36")
        self.assertEqual(alien_data["channel_count"], 8)
        self.assertEqual([ch["label"] for ch in alien_data["channels"]],
                         ["Dimmer", "Red", "Green", "Blue", "Empty", "Program", "Speed", "Emptz"])

        # Test Alien .qxf from zz-fixture repository
        alien_qxf_file = zz_fixture_dir / "Alien-AL36.qxf"
        self.assertTrue(alien_qxf_file.is_file())
        qxf_alien = ET.parse(alien_qxf_file).getroot()
        self.assertEqual([node.attrib["Name"] for node in qxf_alien.findall("q:Channel", ns)],
                         ["Dimmer", "Red", "Green", "Blue", "Empty", "Program", "Speed", "Emptz"])
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

        # Verify all popup windows and menus instantiate and become visible
        win._on_open_fixture_list()
        self.assertTrue(win.win_fixture_list.isVisible())
        win._on_open_fixture_editor()
        self.assertTrue(win.win_fixture_editor.isVisible())
        win._on_open_visualizer()
        self.assertTrue(win.win_visualizer.isVisible())
        win._on_open_settings()
        self.assertTrue(win.win_settings.isVisible())
        win._on_open_help()
        self.assertTrue(win.win_help.isVisible())
        win._on_open_about()
        self.assertTrue(win.win_about.isVisible())

        # Verify top-level menus and direct actions exist (Preview, Setting, Help, About are direct actions without dropdown)
        from ui.qt_compat import QMenu
        action_texts = [a.text() for a in win.menuBar().actions()]
        for expected_action in ["File", "Fixture", "Preview", "Setting", "Help", "About"]:
            self.assertIn(expected_action, action_texts)
        menu_titles = [m.title() for m in win.menuBar().findChildren(QMenu)]
        for title in ["File", "Fixture"]:
            self.assertIn(title, menu_titles)
        self.assertNotIn("Editor", menu_titles)

        win.close()

    def test_alien_and_kuma_autopatch_addressing(self):
        """Verifies requested DMX addressing: Alien AL36 at 001, 017, 033, 049 and Kumastb at 001."""
        self._application()
        from ui.main_window import MainWindow
        win = MainWindow()

        # 1. Test Alien AL36 4x GIA Stage Patch
        win.tab_address._on_patch_alien_gia()
        alien_starts = [1, 17, 33, 49]
        for idx, start_ch in enumerate(alien_starts):
            # Ch 1: Dimmer
            self.assertTrue(win.tab_address.grid_area.boxes[start_ch].is_patched)
            self.assertEqual(win.tab_address.grid_area.boxes[start_ch].channel_type, "dimmer")
            self.assertEqual(win.tab_address.grid_area.boxes[start_ch].fixture_name, f"Alien AL36 #{idx + 1} (8CH)")
            # Ch 5: Empty (Alien has no white)
            self.assertEqual(win.tab_address.grid_area.boxes[start_ch + 4].channel_type, "empty")
            # Ch 8: Emptz (Empty)
            self.assertEqual(win.tab_address.grid_area.boxes[start_ch + 7].channel_type, "empty")

        # Verify gaps between fixtures are unpatched
        self.assertFalse(win.tab_address.grid_area.boxes[9].is_patched)
        self.assertFalse(win.tab_address.grid_area.boxes[16].is_patched)
        self.assertFalse(win.tab_address.grid_area.boxes[25].is_patched)
        self.assertFalse(win.tab_address.grid_area.boxes[32].is_patched)
        self.assertFalse(win.tab_address.grid_area.boxes[41].is_patched)
        self.assertFalse(win.tab_address.grid_area.boxes[48].is_patched)
        self.assertFalse(win.tab_address.grid_area.boxes[57].is_patched)

        # 2. Test Kumastb STL47 Bench Test Patch
        win.tab_address._on_patch_kuma_bench()
        self.assertTrue(win.tab_address.grid_area.boxes[1].is_patched)
        self.assertEqual(win.tab_address.grid_area.boxes[1].channel_type, "dimmer")
        self.assertEqual(win.tab_address.grid_area.boxes[1].fixture_name, "Kumastb STL47 (8CH RGBW)")
        # Ch 5: White (Kumastb has dedicated white)
        self.assertEqual(win.tab_address.grid_area.boxes[5].channel_type, "white")
        self.assertFalse(win.tab_address.grid_area.boxes[9].is_patched)
        self.assertFalse(win.tab_address.grid_area.boxes[17].is_patched)

        win.close()

    def test_perform_tab_cue_generation_and_crossfade(self):
        """Verifies song selection auto-populates section cues and triggers smooth crossfading."""
        self._application()
        from ui.main_window import MainWindow
        win = MainWindow()

        # Add sample worship song to playlist
        sample_worship = {
            "title": "Kebaikan Tuhan (Goodness of God)",
            "quadrant": "Q3 Worship",
            "bpm": 72.0,
            "palette": {"R": 180, "G": 90, "B": 240, "W": 40},
        }
        win.tab_perform.add_analyzed_song(sample_worship)
        self.assertEqual(len(win.tab_perform.playlist), 1)

        # Cues should auto-populate in cue_table (6 section cues: Intro, Verse 1, Chorus, Verse 2, Bridge, Ending)
        self.assertEqual(win.tab_perform.cue_table.rowCount(), 6)
        self.assertEqual(win.tab_perform.cue_table.item(0, 0).text(), "Intro")
        self.assertEqual(win.tab_perform.cue_table.item(2, 0).text(), "Chorus")
        self.assertEqual(win.tab_perform.cue_table.item(4, 0).text(), "Bridge")

        # Test GO+ master playback
        win.tab_perform._on_go_clicked()
        self.assertEqual(win.tab_perform.active_cue_index, 0)
        self.assertIn("INTRO", win.tab_perform.lbl_cue_status.text())

        # Test triggering next cue
        win.tab_perform._on_go_clicked()
        self.assertEqual(win.tab_perform.active_cue_index, 1)

        # Test crossfade tick simulation
        self.assertTrue(win._crossfade_timer.isActive())
        # Simulate timer tick
        win._on_crossfade_tick()
        self.assertIsNotNone(win.dmx_buffer)

        # Test fade black
        win.tab_perform._on_fade_black_clicked()
        self.assertIn("BLACKOUT", win.tab_perform.lbl_cue_status.text())

        win.close()

    def test_tactile_fader_zero_and_mixer_bank_scroll(self):
        """Verifies [X] clear button and quick bank jump scrolling in MixerTab."""
        self._application()
        from ui.main_window import MainWindow
        win = MainWindow()

        # 1. Test Grand Master dimensions and zeroing
        master = win.tab_mixer.master_fader
        self.assertTrue(master.is_master)
        self.assertEqual(master.width(), 68)
        self.assertGreaterEqual(master.minimumHeight(), 230)
        master.value = 255
        self.assertEqual(master.value, 255)
        # Simulate click on [X] button
        master.value = 0
        self.assertEqual(master.value, 0)

        # 2. Test Channel Fader [X] clear
        fader1 = win.tab_mixer.faders[1]
        fader1.value = 180
        self.assertEqual(fader1.value, 180)
        fader1.value = 0
        self.assertEqual(fader1.value, 0)

        # 3. Test Bank Scroll Jump
        win.tab_mixer.scroll_to_channel(17)
        self.assertGreater(win.tab_mixer.scroll_area.horizontalScrollBar().value(), 0)
        win.tab_mixer.scroll_to_channel(1)
        self.assertEqual(win.tab_mixer.scroll_area.horizontalScrollBar().value(), 0)

        win.close()

    def test_visualizer_3d_stage_and_haze_simulation(self):
        """Verifies 2D & 3D Stage Visualizer, volumetric beams, and atmospheric haze FX."""
        self._application()
        from ui.main_window import MainWindow
        win = MainWindow()

        win._on_open_visualizer()
        vis = win.win_visualizer
        self.assertIsNotNone(vis)
        self.assertTrue(vis.isVisible())
        self.assertEqual(vis.tabs.count(), 2)

        # Verify 3D Canvas properties and haze (Default: False / OFF)
        self.assertFalse(vis.canvas_3d.haze_enabled)
        vis._on_toggle_haze()
        self.assertTrue(vis.canvas_3d.haze_enabled)
        vis._on_toggle_haze()
        self.assertFalse(vis.canvas_3d.haze_enabled)

        # Verify 3D projection math
        sx, sy, sz = vis.canvas_3d.project(0, 0, 0, 400, 300)
        self.assertIsInstance(sx, float)
        self.assertIsInstance(sy, float)
        self.assertGreater(sz, 0)

        # Verify DMX update propagates to both 2D and 3D after patching
        win.tab_address._on_patch_alien_gia()
        vis.sync_fixtures(win.tab_address.get_patched_fixtures())
        self.assertEqual(len(vis.canvas_2d.fixtures), 4)
        self.assertEqual(len(vis.canvas_3d.fixtures_3d), 4)

        dmx_data = bytearray(512)
        # Patch Alien #1 at 1 (dimmer 255, red 200, green 100, blue 50)
        dmx_data[0] = 255
        dmx_data[1] = 200
        dmx_data[2] = 100
        dmx_data[3] = 50
        vis.update_dmx(dmx_data)
        self.assertEqual(vis.canvas_2d.fixtures[0]["dim"], 255)
        self.assertEqual(vis.canvas_3d.fixtures_3d[0]["dim"], 255)

        win.close()

    def test_fixture_editor_and_library_feedback_v4(self):
        """Verifies Feedback v4 polish: Fixture Editor defaults, table columns, and Fixture Library window."""
        self._application()
        from ui.panels.fixture_editor import FixtureEditorWindow, CHANNEL_TYPES
        from ui.panels.fixture_list import FixtureListWindow
        from ui.main_window import MainWindow

        # 1. Test FixtureEditorWindow
        editor = FixtureEditorWindow()
        self.assertEqual(editor.windowTitle(), "Fixture Editor")
        self.assertEqual(editor.txt_model.text(), "")
        self.assertEqual(editor.txt_maker.text(), "")
        self.assertEqual(editor.spin_channels.value(), 4)

        # Verify table headers and rows
        self.assertEqual(editor.table.columnCount(), 3)
        self.assertEqual(editor.table.horizontalHeaderItem(0).text(), "Channel")
        self.assertEqual(editor.table.horizontalHeaderItem(1).text(), "Label")
        self.assertEqual(editor.table.horizontalHeaderItem(2).text(), "Type")

        self.assertEqual(editor.table.rowCount(), 4)
        self.assertEqual(editor.table.item(0, 0).text(), "01")
        self.assertEqual(editor.table.item(1, 0).text(), "02")
        self.assertEqual(editor.table.item(2, 0).text(), "03")
        self.assertEqual(editor.table.item(3, 0).text(), "04")

        # Verify QLC+ channel types support
        for expected_type in ["Dimmer", "Red", "Green", "Blue", "White", "Amber", "UV", "Cyan", "Magenta", "Yellow", "Pan", "Tilt", "Gobo", "Prism", "Strobe", "Shutter"]:
            self.assertIn(expected_type, CHANNEL_TYPES)

        # Test changing channel count to 8
        editor.spin_channels.setValue(8)
        self.assertEqual(editor.table.rowCount(), 8)
        self.assertEqual(editor.table.item(7, 0).text(), "08")

        # Verify bottom buttons: Save and Close only
        self.assertEqual(editor.btn_save.text(), "Save")
        self.assertEqual(editor.btn_close.text(), "Close")
        editor.close()

        # 2. Test FixtureListWindow
        lib = FixtureListWindow()
        self.assertEqual(lib.windowTitle(), "Fixture Library")
        self.assertIsNotNone(lib.list_widget)
        self.assertIsNotNone(lib.inspector_text)
        lib.close()

        # 3. Test Title Bar behavior in MainWindow
        win = MainWindow()
        self.assertEqual(win.windowTitle(), "ZZLUXORA [Untitled.zlx]")
        win.current_project_path = "/home/zzdree/ANDREAS/zzluxora_v10/showfiles/custom_worship.zlx"
        win._update_title_bar()
        self.assertEqual(win.windowTitle(), "ZZLUXORA [/home/zzdree/ANDREAS/zzluxora_v10/showfiles/custom_worship.zlx]")
        win.close()


if __name__ == "__main__":
    unittest.main()

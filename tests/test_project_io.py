import os
import tempfile
import unittest
from core.project_io import ProjectIO


class TestProjectIO(unittest.TestCase):
    def test_default_project_creation(self):
        proj = ProjectIO.create_default_project("My Service Sunday")
        self.assertEqual(proj["app"], "ZZLUXORA")
        self.assertEqual(proj["version"], ProjectIO.VERSION)
        self.assertEqual(proj["project_name"], "My Service Sunday")
        self.assertEqual(len(proj["patches"]), 2)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test_proj.zlx")
            original_data = ProjectIO.create_default_project("Test Church Event")
            original_data["target_ip"] = "192.168.4.1"

            save_ok = ProjectIO.save_project(original_data, file_path)
            self.assertTrue(save_ok)
            self.assertTrue(os.path.exists(file_path))

            loaded_data = ProjectIO.load_project(file_path)
            self.assertIsNotNone(loaded_data)
            self.assertEqual(loaded_data["project_name"], "Test Church Event")
            self.assertEqual(loaded_data["target_ip"], "192.168.4.1")

    def test_default_project_uses_runtime_output_defaults(self):
        project = ProjectIO.create_default_project()

        self.assertEqual(project["universe"], 0)
        self.assertEqual(project["master_dimmer"], 255)
        self.assertEqual(project["port"], 6454)
        self.assertEqual(project["cues"], [])

    def test_main_window_project_roundtrip_preserves_cues_port_and_dmx_scale(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch

        from ui.main_window import MainWindow

        cue = {
            "label": "PRAISE",
            "type": "scene",
            "color": {"R": 255, "G": 200, "B": 80, "W": 40},
            "dimmer": 220,
            "fade_time": 1.5,
        }
        song = {"title": "Sunday Service", "bpm": 72.0}

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "roundtrip.zlx")
            save_faders = {channel: SimpleNamespace(value=0) for channel in range(257)}
            save_faders[0].value = 192
            save_faders[1].value = 200
            save_window = SimpleNamespace(
                tab_address=SimpleNamespace(grid_area=SimpleNamespace(boxes={})),
                tab_mixer=SimpleNamespace(
                    faders=save_faders,
                    master_fader=save_faders[0],
                ),
                tab_perform=SimpleNamespace(playlist=[song]),
                tab_page=SimpleNamespace(
                    executor_buttons=[SimpleNamespace(cue_data=cue)],
                ),
                target_ip="192.168.4.1",
                target_port=7777,
                target_universe=2,
                _fixture_channel_offset=MainWindow._fixture_channel_offset,
                _update_title_bar=Mock(),
            )

            with patch("ui.main_window.QMessageBox.information"):
                MainWindow._save_to_path(save_window, file_path)

            saved_project = ProjectIO.load_project(file_path)
            self.assertEqual(saved_project["cues"], [cue])
            self.assertEqual(saved_project["port"], 7777)

            load_faders = {channel: SimpleNamespace(value=0) for channel in range(257)}
            load_window = SimpleNamespace(
                current_project_path="",
                target_port=6454,
                artnet_sender=SimpleNamespace(close=Mock()),
                tab_address=SimpleNamespace(
                    record_undo=Mock(),
                    grid_area=SimpleNamespace(boxes={}),
                    patch_changed=SimpleNamespace(emit=Mock()),
                ),
                tab_perform=SimpleNamespace(
                    playlist=[],
                    playlist_widget=SimpleNamespace(clear=Mock()),
                    add_analyzed_song=Mock(),
                ),
                tab_page=SimpleNamespace(
                    _clear_executors=Mock(),
                    load_cues=Mock(),
                ),
                tab_mixer=SimpleNamespace(
                    faders=load_faders,
                    master_fader=load_faders[0],
                    set_channel_value=lambda channel, value, silent=False: setattr(
                        load_faders[channel], "value", value
                    ),
                ),
                dmx_buffer=bytearray(512),
                _update_title_bar=Mock(),
            )

            with patch("ui.main_window.ArtNetSender") as sender_factory:
                MainWindow.load_project_file(load_window, file_path, notify=False)

            self.assertEqual(load_window.target_port, 7777)
            sender_factory.assert_called_once_with(
                target_ip="192.168.4.1", universe=2, port=7777
            )
            load_window.tab_page.load_cues.assert_called_once_with([cue])
            self.assertEqual(load_window.dmx_buffer[0], 151)


if __name__ == "__main__":
    unittest.main()

"""
Regression tests for defects found during the 15 Oct 2026 cross-repo audit.
Each test encodes a bug that the pre-audit suite failed to catch, so the
defect cannot silently return.
"""

import os
import tempfile
import unittest
import wave

import numpy as np

from core.audio_loader import AudioLoader
from core.artnet_sender import ArtNetSender
from core.models import PatchEntry, ProjectState, FixtureProfile
from core.models import AudioFrameFeatures


class TestModelsAnnotationsResolve(unittest.TestCase):
    """core/models.py annotated List[Dict[str, Any]] without importing Any,
    so any annotation-resolution API raised NameError."""

    def test_all_public_models_have_resolvable_annotations(self):
        import typing

        for cls in (ProjectState, PatchEntry, FixtureProfile, AudioFrameFeatures):
            with self.subTest(model=cls.__name__):
                typing.get_type_hints(cls)

    def test_any_is_bound_in_models_namespace(self):
        import core.models as models

        self.assertTrue(hasattr(models, "Any"))


class TestProjectStateUniverseConsistency(unittest.TestCase):
    """ProjectState defaulted to universe 1 while PatchEntry, ArtNetSender,
    project_io, and the GIA showfile all use universe 0."""

    def test_project_state_defaults_to_universe_zero(self):
        self.assertEqual(ProjectState().universe, 0)

    def test_patch_entry_and_project_state_agree_on_default_universe(self):
        profile = FixtureProfile.create_generic_rgbw()
        entry = PatchEntry(id="p1", name="PAR", profile=profile)
        self.assertEqual(entry.universe, ProjectState().universe)


class TestAudioLoader24Bit(unittest.TestCase):
    """24-bit PCM (sampwidth == 3) was silently mapped to int16, inflating the
    sample count and corrupting the signal."""

    def test_24bit_wav_round_trips_within_one_lsb(self):
        sample_rate = 22050
        count = 1000
        time_axis = np.arange(count) / sample_rate
        reference = (0.5 * np.sin(2.0 * np.pi * 440.0 * time_axis)).astype(np.float32)
        quantised = (reference * 8388607.0).astype(np.int32)

        packed = quantised.astype(np.uint32)
        raw = np.empty((count, 3), dtype=np.uint8)
        raw[:, 0] = packed & 0xFF
        raw[:, 1] = (packed >> 8) & 0xFF
        raw[:, 2] = (packed >> 16) & 0xFF

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tone24.wav")
            with wave.open(path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(3)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(raw.tobytes())

            audio, out_rate = AudioLoader().load_audio(path)

        self.assertEqual(out_rate, sample_rate)
        self.assertEqual(len(audio), count)
        self.assertLess(float(np.max(np.abs(audio - reference))), 2e-4)

    def test_16bit_still_decodes_after_refactor(self):
        """The 24-bit branch must not regress the 16-bit path."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "pcm16.wav")
            samples = np.array([-32768, -16384, 0, 16384, 32767], dtype=np.int16)
            with wave.open(path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                wav_file.writeframes(samples.tobytes())

            audio, _ = AudioLoader().load_audio(path)

        self.assertAlmostEqual(float(audio[0]), -1.0, places=4)
        self.assertAlmostEqual(float(audio[2]), 0.0, places=4)


class TestArtNetPacketIntegrity(unittest.TestCase):
    """blackout() released the lock before sending, and build_packet()
    advanced the sequence counter outside the critical section."""

    def _sender(self):
        sender = ArtNetSender()
        self.addCleanup(sender.close)
        return sender

    def test_blackout_zeroes_every_channel(self):
        sender = self._sender()
        sender.set_channels(1, [255] * 512)
        sender.blackout()
        self.assertEqual(sender.get_all_channels(), bytes(512))

    def test_sequence_increments_and_never_zero(self):
        """Sequence field cycles 1..255 and must never emit 0 (0 disables it)."""
        sender = self._sender()
        seen = [sender.build_packet()[12] for _ in range(255)]
        self.assertNotIn(0, seen)
        self.assertEqual(seen, list(range(1, 256)))
        # One more build must wrap back to 1, not 0.
        self.assertEqual(sender.build_packet()[12], 1)

    def test_packet_length_and_header(self):
        sender = self._sender()
        packet = sender.build_packet()
        self.assertEqual(len(packet), 530)
        self.assertEqual(packet[:8], b"Art-Net\x00")
        self.assertEqual(packet[8:10], b"\x00\x50")  # OpDmx little-endian


class TestArtNetSenderClosedSocketSafety(unittest.TestCase):
    """blackout() used to raise OSError on a closed socket while send_frame()
    returned False for the same condition. Settings replaces the sender on every
    save, so a stale reference can still be asked to black out."""

    def test_blackout_on_closed_socket_returns_false_instead_of_raising(self):
        sender = ArtNetSender()
        sender.close()
        self.assertFalse(sender.blackout())

    def test_send_frame_on_closed_socket_returns_false(self):
        sender = ArtNetSender()
        sender.close()
        self.assertFalse(sender.send_frame())

    def test_blackout_after_settings_swap_does_not_raise(self):
        sender = ArtNetSender()
        sender.blackout()
        sender.close()
        # Simulates the window closing after Settings replaced the sender.
        self.assertFalse(sender.blackout())


class TestProjectIoSchemaCompatibility(unittest.TestCase):
    """ProjectIO once emitted a patch schema ({id,name,profile,...}) that no
    shipped showfile uses, so its output was not interchangeable with files
    produced by the console UI. The canonical schema is
    {start_channel, model, channels:[...]}."""

    def test_default_project_matches_canonical_patch_schema(self):
        from core.project_io import ProjectIO

        patch = ProjectIO.create_default_project()["patches"][0]
        self.assertEqual(sorted(patch.keys()), ["channels", "model", "start_channel"])
        self.assertIsInstance(patch["channels"], list)
        self.assertTrue(all("type" in ch and "index" in ch for ch in patch["channels"]))

    def test_loads_shipped_gia_showfile_and_enumerates_addressing(self):
        import os

        from core.project_io import ProjectIO

        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(repo_root, "showfiles", "gia_deliksari_alien_4x.zlx")
        data = ProjectIO.load_project(path)

        self.assertIsNotNone(data, "GIA showfile must load through ProjectIO")
        patches = ProjectIO.iter_patches(data)
        self.assertEqual(len(patches), 4, "GIA showfile patches 4 Alien AL36 units")

        starts = [int(p["start_channel"]) for p in patches]
        self.assertEqual(starts, [1, 17, 33, 49])

        for patch in patches:
            span = list(ProjectIO.patch_channel_span(patch))
            self.assertEqual(len(span), 8, "each Alien AL36 occupies 8 DMX channels")

    def test_roundtrip_preserves_patch_schema(self):
        import os
        import tempfile

        from core.project_io import ProjectIO

        project = ProjectIO.create_default_project("Roundtrip")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "roundtrip.zlx")
            self.assertTrue(ProjectIO.save_project(project, path))
            loaded = ProjectIO.load_project(path)

        self.assertIsNotNone(loaded)
        self.assertEqual(
            sorted(ProjectIO.iter_patches(loaded)[0].keys()),
            ["channels", "model", "start_channel"],
        )

    def test_rejects_foreign_and_missing_files(self):
        import os
        import tempfile

        from core.project_io import ProjectIO

        self.assertIsNone(ProjectIO.load_project("/nonexistent/path/nowhere.zlx"))
        with tempfile.TemporaryDirectory() as directory:
            foreign = os.path.join(directory, "foreign.zlx")
            with open(foreign, "w", encoding="utf-8") as handle:
                handle.write('{"app": "OTHER", "patches": []}')
            self.assertIsNone(ProjectIO.load_project(foreign))

            broken = os.path.join(directory, "broken.zlx")
            with open(broken, "w", encoding="utf-8") as handle:
                handle.write("{not json")
            self.assertIsNone(ProjectIO.load_project(broken))


if __name__ == "__main__":
    unittest.main()


class TestFixtureNameStandard(unittest.TestCase):
    """Fixture names must follow the v4 standard, in code and in showfiles.

    feedback_v4.md section 2 fixes the official names as Alien-AL36 and
    Kumastb-STL47 and says text like "8ch", "8ch rgb" or "rgbw" is removed so
    the list reads clean. The quick-patch helpers and the shipped showfiles had
    drifted to "Alien AL36 #1 (8CH)" and "Kumastb STL47 (8CH RGBW)", which broke
    the standard in three places at once and went unnoticed because nothing
    checked the names themselves.
    """

    OFFICIAL = {"Alien-AL36", "Kumastb-STL47"}
    BANNED = ("(8CH", "(8ch", "RGBW)", "rgbw)", " 8CH")

    def test_official_fixture_profiles_use_the_standard_names(self):
        from pathlib import Path
        import json
        fixtures = Path(__file__).resolve().parent.parent / "fixtures"
        names = set()
        for path in fixtures.glob("*.zfx"):
            data = json.loads(path.read_text(encoding="utf-8"))
            names.add(data.get("name"))
        self.assertEqual(self.OFFICIAL - names, set(),
                         f"official profiles must exist with the standard names, found {names}")

    def test_quick_patch_writes_standard_names_without_text_qualifiers(self):
        from ui.main_window import MainWindow
        app = self._application() if hasattr(self, "_application") else None
        from ui.qt_compat import HAS_QT, QApplication
        if not HAS_QT:
            self.skipTest("Qt bindings are not installed")
        app = QApplication.instance() or QApplication(["-platform", "offscreen"])

        win = MainWindow()
        try:
            win.tab_address._on_patch_alien_gia()
            names = {f["name"] for f in win.tab_address.get_patched_fixtures()}
            self.assertTrue(names, "the GIA preset must patch fixtures")
            for name in names:
                with self.subTest(name=name):
                    self.assertTrue(name.startswith("Alien-AL36"),
                                    f"expected the standard Alien-AL36 prefix, got {name!r}")
                    for bad in self.BANNED:
                        self.assertNotIn(bad, name,
                                         f"{name!r} still carries the banned qualifier {bad!r}")

            win.tab_address._on_patch_kuma_bench()
            kuma = {f["name"] for f in win.tab_address.get_patched_fixtures()}
            self.assertIn("Kumastb-STL47", kuma)
        finally:
            win.close()

    def test_shipped_showfiles_do_not_carry_banned_qualifiers(self):
        """Only the OFFICIAL fixtures are governed by the naming standard.

        feedback_v4.md section 2 fixes the names of Alien-AL36 and Kumastb-STL47.
        The demo showfile patches a generic "PAR LED", which has no .zfx profile
        and is not covered by that rule, so its descriptive name is left alone -
        an earlier version of this test failed it and was wrong to.
        """
        from pathlib import Path
        import json
        showfiles = Path(__file__).resolve().parent.parent / "showfiles"
        for path in showfiles.glob("*.zlx"):
            data = json.loads(path.read_text(encoding="utf-8"))
            for patch in data.get("patches", []):
                name = patch.get("model") or patch.get("name") or ""
                if not isinstance(name, str) or not name:
                    continue
                # Skip anything that is not an official fixture.
                if name.split(" #")[0] not in self.OFFICIAL:
                    continue
                with self.subTest(showfile=path.name, name=name):
                    for bad in self.BANNED:
                        self.assertNotIn(bad, name,
                                         f"{path.name}: {name!r} carries the banned "
                                         f"qualifier {bad!r}")

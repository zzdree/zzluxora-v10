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


if __name__ == "__main__":
    unittest.main()

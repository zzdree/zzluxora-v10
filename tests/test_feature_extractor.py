import unittest
from unittest.mock import Mock

import numpy as np

from core.feature_extractor import FeatureExtractor
from core.models import EmotionCoordinate


class TestFeatureExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = FeatureExtractor()
        self.sample_rate = self.extractor.sample_rate

    def test_spectral_centroid_tracks_one_kilohertz_tone(self):
        t = np.arange(self.sample_rate) / self.sample_rate
        signal = np.sin(2.0 * np.pi * 1000.0 * t).astype(np.float32)
        stft = self.extractor.stft_engine.compute_stft(signal)
        magnitude = self.extractor.stft_engine.compute_magnitude_spectrogram(stft)

        centroid = self.extractor.stft_engine.compute_spectral_centroid(magnitude)

        self.assertAlmostEqual(float(centroid[len(centroid) // 2]), 1000.0, delta=50.0)

    def test_tempo_estimates_120_bpm_impulse_train(self):
        duration_sec = 8.0
        signal = np.zeros(int(duration_sec * self.sample_rate), dtype=np.float32)
        beat_interval = int(round(self.sample_rate * 60.0 / 120.0))
        signal[np.arange(0, len(signal), beat_interval)] = 1.0

        bpm = self.extractor.estimate_tempo_bpm(signal)

        self.assertAlmostEqual(bpm, 120.0, delta=5.0)

    def test_spectral_flux_is_positive_at_spectral_change(self):
        before = np.zeros((self.extractor.stft_engine.n_bins, 3), dtype=np.float32)
        before[10, :] = 1.0
        changed = before.copy()
        changed[20, 2] = 3.0

        flux = self.extractor.extract_spectral_flux(changed)

        self.assertEqual(float(flux[0]), 0.0)
        self.assertEqual(float(flux[1]), 0.0)
        self.assertGreater(float(flux[2]), 0.0)

    def test_spectral_flux_is_zero_for_constant_spectrum(self):
        spectrum = np.full((self.extractor.stft_engine.n_bins, 5), 2.0, dtype=np.float32)

        flux = self.extractor.extract_spectral_flux(spectrum)

        np.testing.assert_allclose(flux, 0.0, atol=1e-12)

    def test_mfcc_has_thirteen_finite_coefficients_per_frame(self):
        t = np.arange(self.sample_rate) / self.sample_rate
        signal = (0.5 * np.sin(2.0 * np.pi * 440.0 * t)).astype(np.float32)
        stft = self.extractor.stft_engine.compute_stft(signal)
        power = self.extractor.stft_engine.compute_power_spectrogram(stft)

        mfcc = self.extractor.extract_mfcc(power)

        self.assertEqual(mfcc.shape, (13, power.shape[1]))
        self.assertTrue(np.isfinite(mfcc).all())

    def test_rms_matches_windowed_sine_sanity_value(self):
        amplitude = 0.5
        t = np.arange(self.sample_rate) / self.sample_rate
        signal = (amplitude * np.sin(2.0 * np.pi * 440.0 * t)).astype(np.float32)

        rms = self.extractor.stft_engine.compute_rms_energy(signal)
        expected_hann_rms = amplitude * np.sqrt(3.0 / 16.0)

        self.assertAlmostEqual(float(rms[len(rms) // 2]), expected_hann_rms, delta=0.02)

    def test_analysis_populates_mfcc_and_passes_onset_and_mfcc_to_model(self):
        duration = 3.0
        t = np.arange(int(duration * self.sample_rate)) / self.sample_rate
        signal = np.zeros_like(t)
        first = t < 1.5
        signal[first] = 0.3 * np.sin(2.0 * np.pi * 440.0 * t[first])
        signal[~first] = 0.8 * np.sin(2.0 * np.pi * 1200.0 * t[~first])

        model = Mock()
        model.evaluate_frame.return_value = EmotionCoordinate()
        self.extractor.emotion_model = model

        frames = self.extractor.analyze_audio_stream(signal)

        self.assertTrue(frames)
        self.assertTrue(all(len(frame.mfcc_coeffs) == 13 for frame in frames))
        self.assertTrue(all(np.isfinite(frame.mfcc_coeffs).all() for frame in frames))
        calls = [call.kwargs for call in model.evaluate_frame.call_args_list]
        self.assertTrue(all(0.0 <= call['onset_norm'] <= 1.0 for call in calls))
        self.assertTrue(all(0.0 <= call['mfcc_norm'] <= 1.0 for call in calls))
        self.assertTrue(any(call['onset_norm'] > 0.0 for call in calls))
        self.assertTrue(any(call['mfcc_norm'] != 0.5 for call in calls))

    def test_silence_short_audio_and_nonfinite_samples_remain_finite(self):
        for signal in (
            np.zeros(0, dtype=np.float32),
            np.zeros(64, dtype=np.float32),
            np.zeros(4096, dtype=np.float32),
            np.array([0.0, np.nan, np.inf, -np.inf] * 1024, dtype=np.float32),
        ):
            frames = self.extractor.analyze_audio_stream(signal)
            self.assertTrue(frames)
            for frame in frames:
                self.assertTrue(np.isfinite(frame.rms_energy))
                self.assertTrue(np.isfinite(frame.spectral_centroid))
                self.assertTrue(np.isfinite(frame.chroma_vector).all())
                self.assertTrue(np.isfinite(frame.mfcc_coeffs).all())
                self.assertTrue(np.isfinite(frame.emotion.valence))
                self.assertTrue(np.isfinite(frame.emotion.arousal))
                self.assertGreaterEqual(frame.rms_energy, 0.0)
                self.assertLessEqual(frame.rms_energy, 1.0)

    def test_silent_onset_normalization_returns_zero_vector(self):
        magnitude = np.zeros((self.extractor.stft_engine.n_bins, 4), dtype=np.float32)

        onset = self.extractor.extract_onset_strength(magnitude)

        np.testing.assert_array_equal(onset, np.zeros(4, dtype=np.float32))


if __name__ == "__main__":
    unittest.main()

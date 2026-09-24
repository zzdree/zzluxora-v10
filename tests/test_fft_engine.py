import unittest
import numpy as np
from core.fft_engine import STFTEngine


class TestSTFTEngine(unittest.TestCase):
    def test_stft_engine_initialization(self):
        stft = STFTEngine(sample_rate=22050, n_fft=2048, hop_length=512)
        self.assertEqual(stft.n_bins, 1025)
        self.assertAlmostEqual(stft.freq_resolution, 10.7666, places=2)
        self.assertAlmostEqual(stft.fps, 43.066, places=2)
        self.assertEqual(len(stft.window), 2048)

    def test_stft_sine_wave_peak(self):
        sample_rate = 22050
        n_fft = 2048
        hop_length = 512
        stft = STFTEngine(sample_rate=sample_rate, n_fft=n_fft, hop_length=hop_length)

        duration = 1.0
        t = np.arange(int(duration * sample_rate)) / sample_rate
        target_freq = 440.0
        signal = np.sin(2.0 * np.pi * target_freq * t).astype(np.float32)

        stft_matrix = stft.compute_stft(signal)
        mag_spec = stft.compute_magnitude_spectrogram(stft_matrix)

        expected_bin = int(round(target_freq / stft.freq_resolution))
        mid_frame_mag = mag_spec[:, mag_spec.shape[1] // 2]
        peak_bin = int(np.argmax(mid_frame_mag))

        self.assertLessEqual(abs(peak_bin - expected_bin), 1)

    def test_spectral_centroid_bounds(self):
        sample_rate = 22050
        stft = STFTEngine(sample_rate=sample_rate, n_fft=2048, hop_length=512)

        t = np.arange(sample_rate) / sample_rate
        signal = np.sin(2.0 * np.pi * 1000.0 * t).astype(np.float32)

        stft_matrix = stft.compute_stft(signal)
        mag_spec = stft.compute_magnitude_spectrogram(stft_matrix)
        centroids = stft.compute_spectral_centroid(mag_spec)

        mid_centroid = float(centroids[len(centroids) // 2])
        self.assertLess(abs(mid_centroid - 1000.0), 50.0)


if __name__ == "__main__":
    unittest.main()

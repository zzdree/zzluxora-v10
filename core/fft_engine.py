"""
FFT & STFT Mathematical Computation Engine for ZZLUXORA v10.
Implements Discrete Fourier Transform (DFT), Fast Fourier Transform (FFT),
Short-Time Fourier Transform (STFT), and Hann Windowing using pure NumPy.
"""

from __future__ import annotations
import math
from typing import Tuple
import numpy as np


class STFTEngine:
    """
    Mathematical STFT processor optimized for real-time and batch audio feature extraction.
    Default parameters:
        sample_rate = 22050 Hz (MIR standard)
        n_fft       = 2048 samples (Frequency resolution ~10.77 Hz per bin)
        hop_length  = 512 samples  (Time hop ~23.22 ms, ~43.07 FPS aligned with DMX512)
    """

    def __init__(self, sample_rate: int = 22050, n_fft: int = 2048, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_bins = (n_fft // 2) + 1
        self.freq_resolution = sample_rate / n_fft
        self.hop_duration_sec = hop_length / sample_rate
        self.fps = sample_rate / hop_length

        # Precompute Hann window w[n] = 0.5 * (1 - cos(2*pi*n / (N - 1)))
        self.window = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(n_fft) / (n_fft - 1)))

        # Precompute physical frequency for each bin k: f_k = k * fs / N
        self.bin_frequencies = np.arange(self.n_bins) * self.freq_resolution

    def compute_stft(self, signal: np.ndarray) -> np.ndarray:
        """
        Compute Short-Time Fourier Transform (STFT) of a 1D audio signal.
        Returns a complex 2D matrix of shape (n_bins, n_frames).
        """
        if signal.ndim > 1:
            signal = np.mean(signal, axis=0)  # Downmix to mono

        signal_length = len(signal)
        if signal_length < self.n_fft:
            # Zero-pad if signal is shorter than window
            padded = np.zeros(self.n_fft, dtype=np.float32)
            padded[:signal_length] = signal
            signal = padded
            signal_length = self.n_fft

        # Calculate number of frames
        n_frames = 1 + (signal_length - self.n_fft) // self.hop_length
        stft_matrix = np.zeros((self.n_bins, n_frames), dtype=np.complex64)

        for m in range(n_frames):
            start = m * self.hop_length
            end = start + self.n_fft
            frame = signal[start:end] * self.window

            # Compute Fast Fourier Transform (Real-to-Complex FFT)
            # Produces exactly (n_fft // 2 + 1) non-redundant positive frequency bins
            stft_matrix[:, m] = np.fft.rfft(frame, n=self.n_fft)

        return stft_matrix

    def compute_magnitude_spectrogram(self, stft_matrix: np.ndarray) -> np.ndarray:
        """
        Returns |X[m, k]| = sqrt(Re^2 + Im^2).
        """
        return np.abs(stft_matrix)

    def compute_power_spectrogram(self, stft_matrix: np.ndarray) -> np.ndarray:
        """
        Returns S[m, k] = |X[m, k]|^2.
        """
        return np.abs(stft_matrix) ** 2

    def compute_rms_energy(self, signal: np.ndarray) -> np.ndarray:
        """
        Computes Root Mean Square (RMS) energy per frame in time domain.
        RMS[m] = sqrt( (1/N) * sum( (x[n + mH] * w[n])^2 ) )
        """
        if signal.ndim > 1:
            signal = np.mean(signal, axis=0)

        signal_length = len(signal)
        n_frames = max(1, 1 + (signal_length - self.n_fft) // self.hop_length)
        rms_values = np.zeros(n_frames, dtype=np.float32)

        for m in range(n_frames):
            start = m * self.hop_length
            end = start + self.n_fft
            if end <= signal_length:
                windowed_frame = signal[start:end] * self.window
            else:
                windowed_frame = np.zeros(self.n_fft, dtype=np.float32)
                chunk = signal[start:signal_length]
                windowed_frame[:len(chunk)] = chunk * self.window[:len(chunk)]

            mean_square = np.mean(windowed_frame ** 2)
            rms_values[m] = np.sqrt(max(0.0, float(mean_square)))

        return rms_values

    def compute_spectral_centroid(self, magnitude_spec: np.ndarray) -> np.ndarray:
        """
        Computes the spectral centroid (center of mass) for each frame m:
        Centroid[m] = sum( f_k * |X[m, k]| ) / sum( |X[m, k]| )
        """
        n_frames = magnitude_spec.shape[1]
        centroids = np.zeros(n_frames, dtype=np.float32)

        # Vectorized over all bins
        total_magnitudes = np.sum(magnitude_spec, axis=0)
        weighted_frequencies = np.dot(self.bin_frequencies, magnitude_spec)

        # Avoid division by zero on silent frames
        mask = total_magnitudes > 1e-8
        centroids[mask] = weighted_frequencies[mask] / total_magnitudes[mask]

        return centroids

    def get_frame_timestamps(self, n_frames: int) -> np.ndarray:
        """Returns physical timestamps (in seconds) for each frame center."""
        return np.arange(n_frames) * self.hop_duration_sec

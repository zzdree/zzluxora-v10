"""
Acoustic feature extraction for ZZLUXORA v10.
"""

from __future__ import annotations

import math
from typing import List

import numpy as np

from core.color_engine import ColorEngine
from core.emotion_model import EmotionModel
from core.fft_engine import STFTEngine
from core.models import AudioFrameFeatures


class FeatureExtractor:
    """Extract frame-level MIR features and map them to affect and RGBW."""

    N_MELS = 40
    N_MFCC = 13
    _POWER_EPSILON = 1e-10
    _FLUX_EPSILON = 1e-12
    _DEFAULT_TEMPO_BPM = 100.0

    def __init__(self, sample_rate: int = 22050, n_fft: int = 2048, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length

        self.stft_engine = STFTEngine(sample_rate=sample_rate, n_fft=n_fft, hop_length=hop_length)
        self.emotion_model = EmotionModel()
        self.color_engine = ColorEngine()

        self.chroma_filterbank = self._build_chroma_filterbank()
        self.mel_filterbank = self._build_mel_filterbank()
        self.dct_matrix = self._build_dct_matrix()

    @staticmethod
    def _finite_spectrogram(spectrogram: np.ndarray) -> np.ndarray:
        """Return a finite, nonnegative matrix shaped (frequency bins, frames)."""
        values = np.asarray(spectrogram, dtype=np.float64)
        if values.ndim == 1:
            values = values[:, np.newaxis]
        if values.ndim != 2:
            raise ValueError("Spectrogram must be a 1D or 2D array")
        values = np.nan_to_num(values, copy=True, nan=0.0, posinf=0.0, neginf=0.0)
        return np.maximum(values, 0.0)

    @staticmethod
    def _finite_signal(signal: np.ndarray) -> np.ndarray:
        """Convert audio to finite, clipped mono float32 samples."""
        values = np.asarray(signal, dtype=np.float64)
        if values.ndim > 1:
            values = np.mean(values, axis=0)
        if values.ndim != 1:
            raise ValueError("Audio signal must be a 1D mono array")
        values = np.nan_to_num(values, copy=True, nan=0.0, posinf=0.0, neginf=0.0)
        return np.clip(values, -1.0, 1.0).astype(np.float32)

    def _build_chroma_filterbank(self) -> np.ndarray:
        """Project FFT bins in the musical range to 12 semitone classes."""
        freqs = self.stft_engine.bin_frequencies
        filterbank = np.zeros((12, self.stft_engine.n_bins), dtype=np.float32)

        for index, frequency in enumerate(freqs):
            if frequency < 30.0 or frequency > 4000.0:
                continue
            midi_pitch = 12.0 * math.log2(frequency / 440.0) + 69.0
            semitone = int(round(midi_pitch)) % 12
            distance = abs(midi_pitch - round(midi_pitch))
            filterbank[semitone, index] += math.exp(-0.5 * (distance / 0.5) ** 2)

        row_sums = np.sum(filterbank, axis=1, keepdims=True)
        np.divide(filterbank, row_sums, out=filterbank, where=row_sums > 0.0)
        return filterbank

    def extract_chroma(self, magnitude_spec: np.ndarray) -> np.ndarray:
        """Extract a unit-norm 12-bin chroma vector for each frame."""
        magnitude = self._finite_spectrogram(magnitude_spec)
        if magnitude.shape[0] != self.chroma_filterbank.shape[1]:
            raise ValueError("Magnitude spectrogram bin count does not match the configured FFT size")
        chroma = self.chroma_filterbank @ magnitude
        norms = np.linalg.norm(chroma, axis=0, keepdims=True)
        np.divide(chroma, norms, out=chroma, where=norms > 1e-6)
        return np.nan_to_num(chroma, copy=False, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    def _build_mel_filterbank(self) -> np.ndarray:
        """Create 40 triangular filters equally spaced on the Mel scale."""
        def hz_to_mel(frequency: np.ndarray) -> np.ndarray:
            return 2595.0 * np.log10(1.0 + frequency / 700.0)

        def mel_to_hz(mel: np.ndarray) -> np.ndarray:
            return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

        mel_bounds = hz_to_mel(np.array([0.0, self.sample_rate / 2.0]))
        mel_points = np.linspace(mel_bounds[0], mel_bounds[1], self.N_MELS + 2)
        hz_points = mel_to_hz(mel_points)
        frequencies = self.stft_engine.bin_frequencies
        filterbank = np.zeros((self.N_MELS, self.stft_engine.n_bins), dtype=np.float64)

        for index in range(self.N_MELS):
            lower, center, upper = hz_points[index:index + 3]
            rising = (frequencies - lower) / max(center - lower, np.finfo(float).eps)
            falling = (upper - frequencies) / max(upper - center, np.finfo(float).eps)
            filterbank[index] = np.maximum(0.0, np.minimum(rising, falling))

        return filterbank

    def _build_dct_matrix(self) -> np.ndarray:
        """Build the unscaled DCT-II defined in the MFCC equation."""
        coefficients = np.arange(self.N_MFCC, dtype=np.float64)[:, np.newaxis]
        mel_indices = np.arange(1, self.N_MELS + 1, dtype=np.float64)[np.newaxis, :]
        return np.cos(np.pi * coefficients * (mel_indices - 0.5) / self.N_MELS)

    def extract_mfcc(self, power_spectrogram: np.ndarray) -> np.ndarray:
        """Compute 13 MFCCs from power, Mel energies, log power, and DCT-II."""
        power = self._finite_spectrogram(power_spectrogram)
        if power.shape[0] != self.mel_filterbank.shape[1]:
            raise ValueError("Power spectrogram bin count does not match the configured FFT size")
        mel_power = self.mel_filterbank @ power
        log_mel_power = np.log(np.maximum(mel_power, self._POWER_EPSILON))
        mfcc = self.dct_matrix @ log_mel_power
        return np.nan_to_num(mfcc, copy=False, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    def extract_spectral_flux(self, magnitude_spectrogram: np.ndarray) -> np.ndarray:
        """Sum positive frame-to-frame magnitude differences across frequency bins."""
        magnitude = self._finite_spectrogram(magnitude_spectrogram)
        flux = np.zeros(magnitude.shape[1], dtype=np.float64)
        if magnitude.shape[1] > 1:
            positive_differences = np.maximum(magnitude[:, 1:] - magnitude[:, :-1], 0.0)
            flux[1:] = np.sum(positive_differences, axis=0)
        return np.nan_to_num(flux, copy=False, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    def extract_onset_strength(self, magnitude_spectrogram: np.ndarray) -> np.ndarray:
        """Normalize positive spectral flux by its track peak; silence maps to zero."""
        flux = self.extract_spectral_flux(magnitude_spectrogram)
        peak = float(np.max(flux)) if flux.size else 0.0
        if not math.isfinite(peak) or peak <= self._FLUX_EPSILON:
            return np.zeros_like(flux)
        return np.clip(flux / peak, 0.0, 1.0).astype(np.float32)

    @staticmethod
    def _normalize_mfcc_contrast(mfcc: np.ndarray) -> np.ndarray:
        """Min-max normalize frame-wise mean absolute c1-c12, excluding energy c0."""
        if mfcc.shape[1] == 0:
            return np.zeros(0, dtype=np.float32)
        contrast = np.mean(np.abs(mfcc[1:, :]), axis=0)
        minimum = float(np.min(contrast))
        maximum = float(np.max(contrast))
        scale = max(1.0, abs(minimum), abs(maximum))
        if maximum - minimum <= 1e-6 * scale:
            return np.full(contrast.shape, 0.5, dtype=np.float32)
        return np.clip((contrast - minimum) / (maximum - minimum), 0.0, 1.0).astype(np.float32)

    def estimate_tempo_bpm(self, signal: np.ndarray) -> float:
        """Estimate tempo from an STFT spectral-flux envelope autocorrelation."""
        audio = self._finite_signal(signal)
        if audio.size < 2 * self.sample_rate:
            return self._DEFAULT_TEMPO_BPM

        magnitude = self.stft_engine.compute_magnitude_spectrogram(
            self.stft_engine.compute_stft(audio)
        )
        onset = self.extract_spectral_flux(magnitude).astype(np.float64)
        if onset.size < 2 or float(np.max(onset)) <= self._FLUX_EPSILON:
            return self._DEFAULT_TEMPO_BPM

        onset -= np.mean(onset)
        if float(np.dot(onset, onset)) <= self._FLUX_EPSILON:
            return self._DEFAULT_TEMPO_BPM

        # FFT autocorrelation avoids quadratic cost on full-length songs.
        fft_size = 1 << (2 * onset.size - 1).bit_length()
        spectrum = np.fft.rfft(onset, n=fft_size)
        autocorrelation = np.fft.irfft(spectrum * np.conjugate(spectrum), n=fft_size)[:onset.size]

        seconds_per_frame = self.hop_length / self.sample_rate
        min_lag = max(1, int(math.ceil(60.0 / (190.0 * seconds_per_frame))))
        max_lag = min(
            onset.size - 1,
            int(math.floor(60.0 / (50.0 * seconds_per_frame))),
        )
        if min_lag > max_lag:
            return self._DEFAULT_TEMPO_BPM

        # Search inclusive bounds, then select the strongest local autocorrelation peak.
        candidates = [
            lag for lag in range(min_lag, max_lag + 1)
            if autocorrelation[lag] >= autocorrelation[lag - 1]
            and (lag == max_lag or autocorrelation[lag] >= autocorrelation[lag + 1])
        ]
        if not candidates:
            candidates = list(range(min_lag, max_lag + 1))
        peak_lag = max(candidates, key=lambda lag: autocorrelation[lag])
        peak_value = float(autocorrelation[peak_lag])
        if not math.isfinite(peak_value) or peak_value <= self._FLUX_EPSILON:
            return self._DEFAULT_TEMPO_BPM

        # Resolve common half-time ambiguity when a shorter harmonic peak is nearly as strong.
        # Lag quantization is one STFT frame, so allow that much deviation from an integer multiple.
        for lag in candidates:
            if lag >= peak_lag:
                break
            multiple = round(peak_lag / lag)
            if (
                2 <= multiple <= 4
                and abs(peak_lag - multiple * lag) <= multiple
                and autocorrelation[lag] >= 0.70 * peak_value
            ):
                peak_lag = lag
                break

        bpm = 60.0 / (peak_lag * seconds_per_frame)
        return float(np.clip(bpm, 50.0, 190.0))

    def analyze_audio_stream(self, signal: np.ndarray) -> List[AudioFrameFeatures]:
        """Compute per-frame audio features and map them to emotion and RGBW."""
        audio = self._finite_signal(signal)
        stft_matrix = self.stft_engine.compute_stft(audio)
        magnitude = self.stft_engine.compute_magnitude_spectrogram(stft_matrix)
        power = self.stft_engine.compute_power_spectrogram(stft_matrix)
        n_frames = magnitude.shape[1]

        rms = np.nan_to_num(self.stft_engine.compute_rms_energy(audio), nan=0.0, posinf=0.0, neginf=0.0)
        centroids = np.nan_to_num(
            self.stft_engine.compute_spectral_centroid(magnitude), nan=0.0, posinf=0.0, neginf=0.0
        )
        chroma = self.extract_chroma(magnitude)
        mfcc = self.extract_mfcc(power)
        onset_norm = self.extract_onset_strength(magnitude)
        mfcc_norm = self._normalize_mfcc_contrast(mfcc)
        timestamps = self.stft_engine.get_frame_timestamps(n_frames)
        tempo_bpm = self.estimate_tempo_bpm(audio)

        rms_max = float(np.max(rms)) if rms.size and np.max(rms) > 0.0 else 1.0
        centroid_max = float(np.max(centroids)) if centroids.size and np.max(centroids) > 0.0 else 5000.0
        frames: List[AudioFrameFeatures] = []

        for index in range(n_frames):
            time_sec = float(timestamps[index]) if index < timestamps.size else index * self.stft_engine.hop_duration_sec
            cur_rms = float(rms[index]) if index < rms.size else 0.0
            cur_centroid = float(centroids[index]) if index < centroids.size else 0.0
            rms_norm = float(np.clip(cur_rms / rms_max, 0.0, 1.0))
            centroid_norm = float(np.clip(cur_centroid / centroid_max, 0.0, 1.0))
            frame_chroma = chroma[:, index].tolist()
            frame_mfcc = mfcc[:, index].tolist()
            frame_onset = float(onset_norm[index]) if index < onset_norm.size else 0.0
            frame_mfcc_norm = float(mfcc_norm[index]) if index < mfcc_norm.size else 0.5

            emotion = self.emotion_model.evaluate_frame(
                rms_norm=rms_norm,
                centroid_norm=centroid_norm,
                chroma_12=frame_chroma,
                tempo_bpm=tempo_bpm,
                onset_norm=frame_onset,
                mfcc_norm=frame_mfcc_norm,
            )
            color = self.color_engine.process_frame(emotion, rms_energy=rms_norm, master_dimmer=1.0)
            frames.append(AudioFrameFeatures(
                frame_index=index,
                time_sec=time_sec,
                rms_energy=rms_norm,
                spectral_centroid=cur_centroid,
                chroma_vector=frame_chroma,
                mfcc_coeffs=frame_mfcc,
                emotion=emotion,
                color=color,
            ))

        return frames

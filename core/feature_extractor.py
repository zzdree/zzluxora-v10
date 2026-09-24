"""
Acoustic Feature Extraction Pipeline for ZZLUXORA v10.
Computes RMS Energy, Spectral Centroid, Chroma STFT, and MFCCs
directly from raw audio arrays using STFTEngine, EmotionModel, and ColorEngine.
"""

from __future__ import annotations
import math
from typing import List, Tuple
import numpy as np
from core.fft_engine import STFTEngine
from core.emotion_model import EmotionModel
from core.color_engine import ColorEngine
from core.models import AudioFrameFeatures, ColorRGBW, EmotionCoordinate


class FeatureExtractor:
    """
    End-to-end MIR feature extractor and lighting parameter generator.
    """

    def __init__(self, sample_rate: int = 22050, n_fft: int = 2048, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length

        self.stft_engine = STFTEngine(sample_rate=sample_rate, n_fft=n_fft, hop_length=hop_length)
        self.emotion_model = EmotionModel()
        self.color_engine = ColorEngine()

        # Build Chroma filterbank matrix (12, n_bins)
        self.chroma_filterbank = self._build_chroma_filterbank()

    def _build_chroma_filterbank(self) -> np.ndarray:
        """
        Constructs a (12, n_bins) filterbank matrix projecting FFT magnitude bins
        to 12 chromatic semitones (C, C#, D, ..., B).
        """
        n_bins = self.stft_engine.n_bins
        freqs = self.stft_engine.bin_frequencies
        fb = np.zeros((12, n_bins), dtype=np.float32)

        # Focus on musical range 30 Hz - 4000 Hz
        for k, f in enumerate(freqs):
            if f < 30.0 or f > 4000.0:
                continue
            # MIDI note number: p = 12 * log2(f / 440) + 69
            midi_pitch = 12.0 * math.log2(f / 440.0) + 69.0
            semitone = int(round(midi_pitch)) % 12
            # Gaussian bell curve around bin center
            center_midi = round(midi_pitch)
            dist = abs(midi_pitch - center_midi)
            weight = math.exp(-0.5 * (dist / 0.5) ** 2)
            fb[semitone, k] += weight

        # Normalize filterbank rows
        for c in range(12):
            row_sum = np.sum(fb[c, :])
            if row_sum > 0:
                fb[c, :] /= row_sum

        return fb

    def extract_chroma(self, magnitude_spec: np.ndarray) -> np.ndarray:
        """
        Extracts 12-dimensional Chroma representation: (12, n_frames).
        """
        chroma = np.dot(self.chroma_filterbank, magnitude_spec)
        # Normalize per frame
        norms = np.linalg.norm(chroma, axis=0, keepdims=True)
        norms[norms < 1e-6] = 1.0
        return chroma / norms

    def estimate_tempo_bpm(self, signal: np.ndarray) -> float:
        """
        Estimates global musical tempo (BPM) via autocorrelation of onset envelope.
        """
        if len(signal) < self.sample_rate * 2:
            return 100.0  # Default fallback for short audio

        # Subsample signal for fast autocorrelation
        step = int(self.sample_rate / 100.0)
        envelope = np.abs(signal[::step])
        envelope = envelope - np.mean(envelope)

        autocorr = np.correlate(envelope, envelope, mode="full")
        autocorr = autocorr[len(autocorr) // 2:]

        # Search range for BPM: 60 to 180 BPM
        min_lag = int(100.0 * 60.0 / 180.0)  # lag at 180 BPM
        max_lag = int(100.0 * 60.0 / 60.0)   # lag at 60 BPM

        if max_lag >= len(autocorr):
            max_lag = len(autocorr) - 1

        if min_lag < max_lag:
            peak_lag = min_lag + int(np.argmax(autocorr[min_lag:max_lag]))
            if peak_lag > 0:
                bpm = 100.0 * 60.0 / peak_lag
                return float(max(50.0, min(190.0, bpm)))

        return 100.0

    def analyze_audio_stream(self, signal: np.ndarray) -> List[AudioFrameFeatures]:
        """
        Executes full analysis pipeline across all frames of the audio signal.
        Returns a list of AudioFrameFeatures ready for DMX streaming and timeline display.
        """
        # 1. Compute STFT & Spectrogram
        stft_matrix = self.stft_engine.compute_stft(signal)
        mag_spec = self.stft_engine.compute_magnitude_spectrogram(stft_matrix)
        n_frames = mag_spec.shape[1]

        # 2. Extract Acoustic Features
        rms = self.stft_engine.compute_rms_energy(signal)
        centroids = self.stft_engine.compute_spectral_centroid(mag_spec)
        chroma = self.extract_chroma(mag_spec)
        timestamps = self.stft_engine.get_frame_timestamps(n_frames)
        tempo_bpm = self.estimate_tempo_bpm(signal)

        # Normalize features across track
        rms_max = float(np.max(rms)) if len(rms) > 0 and np.max(rms) > 0 else 1.0
        centroid_max = float(np.max(centroids)) if len(centroids) > 0 and np.max(centroids) > 0 else 5000.0

        frames: List[AudioFrameFeatures] = []

        for m in range(n_frames):
            t = float(timestamps[m]) if m < len(timestamps) else m * self.stft_engine.hop_duration_sec
            cur_rms = float(rms[m]) if m < len(rms) else 0.0
            cur_centroid = float(centroids[m]) if m < len(centroids) else 1000.0
            cur_chroma = chroma[:, m].tolist()

            rms_norm = max(0.0, min(1.0, cur_rms / rms_max))
            centroid_norm = max(0.0, min(1.0, cur_centroid / centroid_max))

            # Evaluate Emotion Coordinates (Valence, Arousal)
            emotion = self.emotion_model.evaluate_frame(
                rms_norm=rms_norm,
                centroid_norm=centroid_norm,
                chroma_12=cur_chroma,
                tempo_bpm=tempo_bpm
            )

            # Generate Physical RGBW Color
            color = self.color_engine.process_frame(emotion, rms_energy=rms_norm, master_dimmer=1.0)

            frames.append(AudioFrameFeatures(
                frame_index=m,
                time_sec=t,
                rms_energy=rms_norm,
                spectral_centroid=cur_centroid,
                chroma_vector=cur_chroma,
                emotion=emotion,
                color=color
            ))

        return frames

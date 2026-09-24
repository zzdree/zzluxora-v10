"""
Valence-Arousal (Russell Circumplex Model) Affective Engine for ZZLUXORA v10.
Maps computational acoustic features into a continuous 2D emotional coordinate space:
- Valence (V) in [-1.0, +1.0]: Solemn/Sorrowful (-1) to Joyous/Exalted (+1)
- Arousal (A) in [-1.0, +1.0]: Calm/Quiet (-1) to Energetic/Dynamic (+1)
"""

from __future__ import annotations
import math
from typing import Dict, List, Optional
import numpy as np
from core.models import EmotionCoordinate


class EmotionModel:
    """
    Computes 2D Valence-Arousal coordinates from normalized audio features.
    Configured specifically for Christian Sacred / Worship music dynamics:
    - Praise segments: High Tempo (120-160 BPM), High RMS, Major Chords -> Q1 (High Valence, High Arousal)
    - Worship segments: Slow Tempo (60-85 BPM), Gentle RMS, Minor/Suspended -> Q3/Q4 (Low/Med Valence, Low Arousal)
    """

    # Krumhansl-Schmuckler key profiles for Major and Minor mode correlation
    MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], dtype=np.float32)
    MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17], dtype=np.float32)

    def __init__(self,
                 valence_weights: Optional[Dict[str, float]] = None,
                 arousal_weights: Optional[Dict[str, float]] = None):
        # Default scientifically balanced feature weights
        self.w_valence = valence_weights or {
            "mode_ratio": 0.50,       # Major vs minor harmony
            "spectral_centroid": 0.30,# Timbre brightness
            "mfcc_contrast": 0.20     # Harmonic texture
        }
        self.w_arousal = arousal_weights or {
            "rms_energy": 0.50,       # Loudness / volume
            "tempo_bpm": 0.30,        # Beat tempo
            "onset_strength": 0.20    # Percussive transient impact
        }

    def compute_mode_ratio(self, chroma_vector: np.ndarray) -> float:
        """
        Computes tonal mode polarity from a 12-dimensional Chroma vector.
        Returns a score in [-1.0, +1.0] where +1.0 is strongly Major, -1.0 is strongly Minor.
        """
        if chroma_vector is None or len(chroma_vector) != 12:
            return 0.0

        c = np.array(chroma_vector, dtype=np.float32)
        norm = np.linalg.norm(c)
        if norm < 1e-6:
            return 0.0
        c = c / norm

        # Correlate with all 12 transpositions of Major and Minor profiles
        max_major_corr = -1.0
        max_minor_corr = -1.0

        major_norm = self.MAJOR_PROFILE / np.linalg.norm(self.MAJOR_PROFILE)
        minor_norm = self.MINOR_PROFILE / np.linalg.norm(self.MINOR_PROFILE)

        for shift in range(12):
            shifted_c = np.roll(c, -shift)
            corr_maj = float(np.dot(shifted_c, major_norm))
            corr_min = float(np.dot(shifted_c, minor_norm))
            if corr_maj > max_major_corr:
                max_major_corr = corr_maj
            if corr_min > max_minor_corr:
                max_minor_corr = corr_min

        denom = max_major_corr + max_minor_corr
        if denom < 1e-6:
            return 0.0

        # Contrast score scaled to [-1.0, +1.0]
        mode_polarity = (max_major_corr - max_minor_corr) / denom
        return max(-1.0, min(1.0, mode_polarity * 2.0))

    def evaluate_frame(self,
                       rms_norm: float,
                       centroid_norm: float,
                       chroma_12: Sequence[float],
                       tempo_bpm: float = 100.0,
                       onset_norm: float = 0.5,
                       mfcc_norm: float = 0.5) -> EmotionCoordinate:
        """
        Evaluates a single temporal frame and returns (Valence, Arousal) coordinates.
        All normalized inputs are expected in range [0.0, 1.0].
        Tempo BPM typically in range [50.0, 180.0].
        """
        # 1. Mode polarity in [-1.0, 1.0]
        mode_score = self.compute_mode_ratio(np.array(chroma_12))

        # Centroid mapped from [0, 1] to [-1, 1]
        centroid_score = 2.0 * max(0.0, min(1.0, centroid_norm)) - 1.0
        mfcc_score = 2.0 * max(0.0, min(1.0, mfcc_norm)) - 1.0

        # Calculate Valence
        valence = (
            self.w_valence["mode_ratio"] * mode_score +
            self.w_valence["spectral_centroid"] * centroid_score +
            self.w_valence["mfcc_contrast"] * mfcc_score
        )

        # 2. Arousal calculation
        # Normalize Tempo [50, 170] -> [-1, 1]
        tempo_clamped = max(50.0, min(170.0, tempo_bpm))
        tempo_score = 2.0 * ((tempo_clamped - 50.0) / 120.0) - 1.0

        rms_score = 2.0 * max(0.0, min(1.0, rms_norm)) - 1.0
        onset_score = 2.0 * max(0.0, min(1.0, onset_norm)) - 1.0

        arousal = (
            self.w_arousal["rms_energy"] * rms_score +
            self.w_arousal["tempo_bpm"] * tempo_score +
            self.w_arousal["onset_strength"] * onset_score
        )

        return EmotionCoordinate(
            valence=max(-1.0, min(1.0, float(valence))),
            arousal=max(-1.0, min(1.0, float(arousal)))
        )

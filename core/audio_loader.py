"""
Audio Loading & Synthesis Engine for ZZLUXORA v10.
Supports loading .wav/.mp3 files with automatic resampling and mono downmixing,
plus synthetic audio generation for unit testing and offline calibration.
"""

from __future__ import annotations
import math
import os
import wave
from typing import Optional, Tuple
import numpy as np


class AudioLoader:
    """
    Robust audio file reader and signal preprocessor.
    Standard target: 22,050 Hz Mono float32 array in range [-1.0, 1.0].
    """

    def __init__(self, target_sample_rate: int = 22050):
        self.target_sample_rate = target_sample_rate

    def load_wav_native(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Loads standard PCM WAV file using Python's standard library `wave`.
        Requires zero external C-dependencies.
        """
        with wave.open(file_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_bytes = wf.readframes(n_frames)

        if sampwidth == 2:
            dtype = np.int16
            max_val = 32768.0
        elif sampwidth == 1:
            dtype = np.uint8
            max_val = 128.0
        elif sampwidth == 3:
            # 24-bit PCM: sign-extend three little-endian bytes into int32.
            raw_24 = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
            audio_24 = raw_24[:, 0] | (raw_24[:, 1] << 8) | (raw_24[:, 2] << 16)
            audio_24 = np.where(audio_24 >= 0x800000, audio_24 - 0x1000000, audio_24)
            audio = (audio_24.astype(np.float32)) / 8388608.0
            return self._finalize(audio, n_channels, framerate)
        elif sampwidth == 4:
            dtype = np.int32
            max_val = 2147483648.0
        else:
            raise ValueError(
                f"Unsupported WAV sample width: {sampwidth} bytes "
                f"(supported: 1, 2, 3, 4). Refusing to guess a dtype."
            )

        audio = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float32)

        if sampwidth == 1:
            audio = (audio - 128.0) / max_val
        else:
            audio = audio / max_val

        return self._finalize(audio, n_channels, framerate)

    def _finalize(self, audio: np.ndarray, n_channels: int, framerate: int) -> Tuple[np.ndarray, int]:
        """Downmix to mono and resample to the target rate."""
        # Downmix stereo to mono
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels)
            audio = np.mean(audio, axis=1)

        # Simple linear resample if sample rate differs
        if framerate != self.target_sample_rate and len(audio) > 0:
            target_length = int(len(audio) * self.target_sample_rate / framerate)
            audio = np.interp(
                np.linspace(0, len(audio), target_length, endpoint=False),
                np.arange(len(audio)),
                audio
            ).astype(np.float32)

        return audio, self.target_sample_rate

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Loads an audio file using the first available decoder that succeeds:
        1. soundfile (if installed) - covers .wav, .flac, .ogg, and any container
           it recognises regardless of extension
        2. native wave parser - PCM .wav only

        librosa is intentionally not used; the DSP/MIR engine is pure NumPy.

        The soundfile branch only falls through to the native parser when the
        file is one soundfile cannot decode. Real I/O failures (missing file,
        permission denied, path is a directory) and resource exhaustion are
        re-raised as-is, because swallowing them turned a readable diagnosis
        into a misleading "please install soundfile" message even when
        soundfile was present and the actual cause was a broken file.
        """
        ext = os.path.splitext(file_path)[1].lower()

        soundfile_failure: Optional[Exception] = None
        try:
            import soundfile as sf
        except ImportError:
            sf = None

        if sf is not None:
            try:
                data, sr = sf.read(file_path, dtype="float32")
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                if sr != self.target_sample_rate:
                    target_length = int(len(data) * self.target_sample_rate / sr)
                    data = np.interp(
                        np.linspace(0, len(data), target_length, endpoint=False),
                        np.arange(len(data)),
                        data,
                    ).astype(np.float32)
                return data, self.target_sample_rate
            except (OSError, RuntimeError, ValueError) as exc:
                # soundfile reports an undecodable container as a LibsndfileError
                # (a RuntimeError subclass) or ValueError; keep that so the native
                # parser can still try a .wav. Any other exception class is a real
                # fault and must not be hidden.
                soundfile_failure = exc
            except MemoryError:
                raise

        if ext == ".wav":
            try:
                return self.load_wav_native(file_path)
            except (wave.Error, EOFError):
                if soundfile_failure is not None:
                    raise RuntimeError(
                        f"Cannot decode audio file {file_path}. "
                        f"soundfile reported: {soundfile_failure}"
                    ) from soundfile_failure
                raise

        if soundfile_failure is not None:
            raise RuntimeError(
                f"Cannot decode audio file {file_path}. "
                f"soundfile reported: {soundfile_failure}"
            ) from soundfile_failure

        raise RuntimeError(
            f"Cannot decode audio file {file_path}. "
            f"Please install soundfile or convert to PCM WAV."
        )

    @staticmethod
    def generate_synthetic_praise_beat(duration_sec: float = 4.0, sample_rate: int = 22050, bpm: float = 130.0) -> np.ndarray:
        """
        Generates a synthetic upbeat praise signal (Major chord + energetic 130 BPM beat)
        for testing and calibration without external audio files.
        """
        total_samples = int(duration_sec * sample_rate)
        t = np.arange(total_samples) / sample_rate
        signal = np.zeros(total_samples, dtype=np.float32)

        # C Major Triad: C4 (261.63 Hz), E4 (329.63 Hz), G4 (392.00 Hz)
        c4 = 0.25 * np.sin(2.0 * np.pi * 261.63 * t)
        e4 = 0.20 * np.sin(2.0 * np.pi * 329.63 * t)
        g4 = 0.20 * np.sin(2.0 * np.pi * 392.00 * t)
        signal += c4 + e4 + g4

        # Add 130 BPM kick/snare pulse transients
        beat_interval = int(sample_rate * (60.0 / bpm))
        for beat_start in range(0, total_samples, beat_interval):
            beat_len = min(int(sample_rate * 0.08), total_samples - beat_start)
            decay = np.exp(-np.linspace(0, 10, beat_len))
            # Low kick frequency 60 Hz
            kick = 0.6 * np.sin(2.0 * np.pi * 60.0 * np.arange(beat_len) / sample_rate) * decay
            signal[beat_start:beat_start + beat_len] += kick.astype(np.float32)

        # Normalize
        max_abs = np.max(np.abs(signal))
        if max_abs > 0:
            signal /= max_abs

        return signal

    @staticmethod
    def generate_synthetic_worship_ambient(duration_sec: float = 4.0, sample_rate: int = 22050) -> np.ndarray:
        """
        Generates a synthetic gentle worship ambient signal (A Minor Chord + soft pad)
        for testing contemplative and solemn emotional responses.
        """
        total_samples = int(duration_sec * sample_rate)
        t = np.arange(total_samples) / sample_rate

        # A Minor Triad: A3 (220.0 Hz), C4 (261.63 Hz), E4 (329.63 Hz)
        a3 = 0.30 * np.sin(2.0 * np.pi * 220.00 * t)
        c4 = 0.25 * np.sin(2.0 * np.pi * 261.63 * t)
        e4 = 0.20 * np.sin(2.0 * np.pi * 329.63 * t)

        # Gentle envelope fade-in/fade-out
        envelope = 0.5 * (1.0 - np.cos(np.pi * t / duration_sec))
        signal = (a3 + c4 + e4) * envelope

        # Normalize
        max_abs = np.max(np.abs(signal))
        if max_abs > 0:
            signal /= max_abs

        return signal.astype(np.float32)

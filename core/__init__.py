"""
ZZLUXORA v10 Core Package.
Provides mathematical audio processing, FFT/STFT engine, affective modeling,
color space transformation, and Art-Net DMX512 communication.
"""

from core.models import (
    ChannelType,
    FixtureChannel,
    FixtureProfile,
    PatchEntry,
    ColorRGBW,
    EmotionCoordinate,
    AudioFrameFeatures,
)
from core.fft_engine import STFTEngine
from core.color_engine import ColorEngine
from core.emotion_model import EmotionModel
from core.artnet_sender import ArtNetSender
from core.audio_loader import AudioLoader
from core.feature_extractor import FeatureExtractor
from core.project_io import ProjectIO

__all__ = [
    "ChannelType",
    "FixtureChannel",
    "FixtureProfile",
    "PatchEntry",
    "ColorRGBW",
    "EmotionCoordinate",
    "AudioFrameFeatures",
    "STFTEngine",
    "ColorEngine",
    "EmotionModel",
    "ArtNetSender",
    "AudioLoader",
    "FeatureExtractor",
    "ProjectIO",
]

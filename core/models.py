"""
Data models for ZZLUXORA v10.
Zero-GUI dependency — uses pure Python dataclasses and type hints.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ChannelType(str, Enum):
    DIMMER = "dimmer"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"
    AMBER = "amber"
    UV = "uv"
    STROBE = "strobe"
    PAN = "pan"
    TILT = "tilt"
    SPEED = "speed"
    MACRO = "macro"
    EMPTY = "empty"


@dataclass
class FixtureChannel:
    index: int  # 1-based index within fixture
    type: ChannelType
    label: str
    default_value: int = 0
    min_value: int = 0
    max_value: int = 255


@dataclass
class FixtureProfile:
    id: str
    name: str
    manufacturer: str
    channel_count: int
    channels: List[FixtureChannel] = field(default_factory=list)

    @classmethod
    def create_generic_rgbw(cls, name: str = "Generic PAR RGBW 4CH") -> FixtureProfile:
        return cls(
            id="generic_rgbw_4ch",
            name=name,
            manufacturer="Generic",
            channel_count=4,
            channels=[
                FixtureChannel(1, ChannelType.RED, "Red"),
                FixtureChannel(2, ChannelType.GREEN, "Green"),
                FixtureChannel(3, ChannelType.BLUE, "Blue"),
                FixtureChannel(4, ChannelType.WHITE, "White"),
            ]
        )

    @classmethod
    def create_generic_dimmer_rgbw(cls, name: str = "Generic PAR RGBW 8CH") -> FixtureProfile:
        return cls(
            id="generic_rgbw_8ch",
            name=name,
            manufacturer="Generic",
            channel_count=8,
            channels=[
                FixtureChannel(1, ChannelType.DIMMER, "Master Dimmer", default_value=255),
                FixtureChannel(2, ChannelType.STROBE, "Strobe", default_value=0),
                FixtureChannel(3, ChannelType.RED, "Red"),
                FixtureChannel(4, ChannelType.GREEN, "Green"),
                FixtureChannel(5, ChannelType.BLUE, "Blue"),
                FixtureChannel(6, ChannelType.WHITE, "White"),
                FixtureChannel(7, ChannelType.MACRO, "Color Macro"),
                FixtureChannel(8, ChannelType.SPEED, "Macro Speed"),
            ]
        )


@dataclass
class PatchEntry:
    id: str
    name: str
    profile: FixtureProfile
    universe: int = 0
    start_channel: int = 1  # 1-512
    x_pos: float = 0.5  # 0.0 to 1.0 (stage position)
    y_pos: float = 0.5  # 0.0 to 1.0 (stage position)

    @property
    def end_channel(self) -> int:
        return self.start_channel + self.profile.channel_count - 1


@dataclass
class ColorRGBW:
    red: int = 0      # 0-255
    green: int = 0    # 0-255
    blue: int = 0     # 0-255
    white: int = 0    # 0-255
    dimmer: float = 1.0  # 0.0-1.0

    def to_dmx_bytes(self) -> Tuple[int, int, int, int]:
        """Apply dimmer and return (R, G, B, W) as integers in range 0-255."""
        d = max(0.0, min(1.0, self.dimmer))
        r = int(round(max(0, min(255, self.red)) * d))
        g = int(round(max(0, min(255, self.green)) * d))
        b = int(round(max(0, min(255, self.blue)) * d))
        w = int(round(max(0, min(255, self.white)) * d))
        return (r, g, b, w)


@dataclass
class EmotionCoordinate:
    valence: float = 0.0   # -1.0 (Solemn/Sad) to +1.0 (Joyous/Happy)
    arousal: float = 0.0   # -1.0 (Calm/Peaceful) to +1.0 (Energetic/Excited)

    @property
    def quadrant(self) -> str:
        if self.valence >= 0 and self.arousal >= 0:
            return "Q1_PRAISE_HIGH"
        elif self.valence < 0 and self.arousal >= 0:
            return "Q2_INTENSE_REVERENCE"
        elif self.valence < 0 and self.arousal < 0:
            return "Q3_DEEP_WORSHIP"
        else:
            return "Q4_PEACE_INTIMACY"


@dataclass
class AudioFrameFeatures:
    frame_index: int
    time_sec: float
    rms_energy: float
    spectral_centroid: float
    chroma_vector: List[float] = field(default_factory=lambda: [0.0] * 12)
    mfcc_coeffs: List[float] = field(default_factory=lambda: [0.0] * 13)
    emotion: EmotionCoordinate = field(default_factory=EmotionCoordinate)
    color: ColorRGBW = field(default_factory=ColorRGBW)


@dataclass
class ProjectState:
    project_name: str = "Untitled.zlx"
    target_ip: str = "127.0.0.1"
    universe: int = 1
    master_dimmer: int = 255
    patches: List[PatchEntry] = field(default_factory=list)
    songs: List[Dict[str, Any]] = field(default_factory=list)
    is_dirty: bool = False


"""
Color Engine for ZZLUXORA v10.
Implements:
1. Valence-Arousal (Russell 2D) to HSV color space mapping
2. HSV to Standard sRGB conversion
3. Physical 4-Channel RGBW decomposition algorithm for stage PAR LEDs
"""

from __future__ import annotations
import math
from typing import Tuple
from core.models import ColorRGBW, EmotionCoordinate


class ColorEngine:
    """
    Translates affective coordinates (Valence, Arousal) and acoustic energy (RMS)
    into physical 4-channel DMX values (Red, Green, Blue, White).
    """

    @staticmethod
    def emotion_to_hsv(emotion: EmotionCoordinate, rms_energy: float, master_dimmer: float = 1.0) -> Tuple[float, float, float]:
        """
        Maps (Valence, Arousal) to Hue (0-360 deg) and Saturation (0.0-1.0),
        and RMS energy to Value/Brightness (0.0-1.0).

        Polar mapping:
        - Angle theta = atan2(Arousal, Valence) in radians
        - Radius r = sqrt(Valence^2 + Arousal^2) in [0.0, sqrt(2)]
        """
        v = max(-1.0, min(1.0, emotion.valence))
        a = max(-1.0, min(1.0, emotion.arousal))

        # Angle in degrees [0.0, 360.0)
        theta_rad = math.atan2(a, v)
        hue_deg = math.degrees(theta_rad) % 360.0

        # Saturation proportional to emotion intensity/distance from origin
        # Neutral center (0, 0) has softer saturation, extremes have full saturation
        dist = math.sqrt(v * v + a * a)
        saturation = max(0.2, min(1.0, dist / math.sqrt(2.0)))

        # Value/Brightness derived from acoustic RMS energy scaled by master dimmer
        rms_clamped = max(0.0, min(1.0, rms_energy))
        value = max(0.0, min(1.0, rms_clamped * master_dimmer))

        return (hue_deg, saturation, value)

    @staticmethod
    def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        """
        Converts HSV (h in 0-360, s in 0-1, v in 0-1) to 8-bit RGB (0-255).
        """
        h = h % 360.0
        s = max(0.0, min(1.0, s))
        v = max(0.0, min(1.0, v))

        c = v * s
        x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
        m = v - c

        if 0.0 <= h < 60.0:
            r_prime, g_prime, b_prime = c, x, 0.0
        elif 60.0 <= h < 120.0:
            r_prime, g_prime, b_prime = x, c, 0.0
        elif 120.0 <= h < 180.0:
            r_prime, g_prime, b_prime = 0.0, c, x
        elif 180.0 <= h < 240.0:
            r_prime, g_prime, b_prime = 0.0, x, c
        elif 240.0 <= h < 300.0:
            r_prime, g_prime, b_prime = x, 0.0, c
        else:
            r_prime, g_prime, b_prime = c, 0.0, x

        r = int(round((r_prime + m) * 255.0))
        g = int(round((g_prime + m) * 255.0))
        b = int(round((b_prime + m) * 255.0))

        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    @staticmethod
    def rgb_to_physical_rgbw(r: int, g: int, b: int, dimmer: float = 1.0) -> ColorRGBW:
        """
        Physical 4-Channel RGBW Decomposition Algorithm for Stage PAR LEDs.

        Standard PAR LEDs have independent Red, Green, Blue, and White emitters.
        If R+G+B are full and W is also full, color saturation collapses (washout).
        By extracting the common minimum W = min(R, G, B) into the dedicated White emitter
        and subtracting it from R, G, B, we maintain exact chromaticity while leveraging
        the high-efficiency pure phosphor white LED.

        Formulas:
            W = min(R, G, B)
            R' = R - W
            G' = G - W
            B' = B - W
        """
        r_clamp = max(0, min(255, r))
        g_clamp = max(0, min(255, g))
        b_clamp = max(0, min(255, b))

        # Extract pure white component
        w = min(r_clamp, g_clamp, b_clamp)
        r_pure = r_clamp - w
        g_pure = g_clamp - w
        b_pure = b_clamp - w

        return ColorRGBW(
            red=r_pure,
            green=g_pure,
            blue=b_pure,
            white=w,
            dimmer=max(0.0, min(1.0, dimmer))
        )

    def process_frame(self, emotion: EmotionCoordinate, rms_energy: float, master_dimmer: float = 1.0) -> ColorRGBW:
        """
        Full pipeline: Emotion + RMS -> HSV -> RGB -> Physical RGBW.
        """
        h, s, v = self.emotion_to_hsv(emotion, rms_energy, master_dimmer)
        r, g, b = self.hsv_to_rgb(h, s, v)
        return self.rgb_to_physical_rgbw(r, g, b, dimmer=1.0)

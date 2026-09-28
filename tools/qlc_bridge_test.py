"""
qlc_bridge_test.py — Art-Net Loopback Bridge Test for QLC+ Simulation
Sends continuous DMX512 frames to 127.0.0.1:6454 (Universe 0) to verify
that QLC+ Simple Desk / Virtual Console faders move in real time without physical hardware.
Integrated with ColorEngine (Russell 2D V-A plane & physical RGBW decomposition)
and official fixtures: Kumastb STL47 (8CH RGBW) & Alien AL36 (8CH RGB).
"""

import sys
import time
import math
import argparse
from pathlib import Path

# Ensure root directory in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.artnet_sender import ArtNetSender
from core.models import EmotionCoordinate, ColorRGBW
from core.color_engine import ColorEngine


def run_fader_test(target_ip: str = "127.0.0.1", duration: float = 30.0, fixture_model: str = "kumastb"):
    model_name = "Kumastb STL47 (8CH RGBW)" if fixture_model == "kumastb" else "Alien AL36 (8CH RGB)"
    is_rgbw = (fixture_model == "kumastb")

    print("=" * 76)
    print("🎛️  ZZLUXORA ➔ QLC+ ART-NET LOOPBACK BRIDGE TEST (SITL)")
    print("=" * 76)
    print(f"Target Host      : {target_ip}:6454 (UDP Art-Net)")
    print(f"Target Universe  : 0 (maps to Universe 1 in QLC+)")
    print(f"Active Fixture   : {model_name}")
    print(f"Fixture Count    : 4 Units (32 DMX Channels total, 8-CH footprint)")
    print(f"Color Pipeline   : Russell 2D Plane (V, A) ➔ HSV ➔ Physical {'RGBW' if is_rgbw else 'RGB'}")
    print(f"Transmission FPS : 43.07 FPS (Standard DMX refresh)")
    print("-" * 76)
    print("Petunjuk Pengaturan di QLC+:")
    print("1. Buka QLC+ ➔ Buka workspace /home/zzdree/ANDREAS/zzluxora_test.qxw")
    print("   atau buka tab 'Inputs/Outputs', Universe 1 centang 'Input' ArtNet 127.0.0.1.")
    print("2. Buka Tab 'Simple Desk' atau 'Virtual Console' di QLC+.")
    print("3. Fader channel 1 s.d. 32 akan bergerak real-time mengikuti emosi audio!")
    print("=" * 76)
    print("Memulai transmisi paket Art-Net (Tekan Ctrl+C untuk berhenti)...\n")

    sender = ArtNetSender(target_ip=target_ip, universe=0)
    start_time = time.time()
    frame_count = 0

    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            t = elapsed * 1.5

            channels_data = []

            # Simulate dynamic audio mood cycle (Praise Q1 -> Worship Q3)
            # Valence and Arousal sinusoidal orbital trajectory
            v = math.sin(t * 0.7)
            a = math.cos(t * 0.9)
            rms = (math.sin(t * 1.8) + 1.0) * 0.4 + 0.2  # RMS dynamic energy

            emotion = EmotionCoordinate(valence=v, arousal=a)
            h, s, val = ColorEngine.emotion_to_hsv(emotion, rms_energy=rms, master_dimmer=1.0)
            base_r, base_g, base_b = ColorEngine.hsv_to_rgb(h, s, val)

            # Generate 4 fixtures with phase offsets
            for fix_idx in range(4):
                offset_rad = fix_idx * 0.5
                fix_v = math.sin(t * 0.7 + offset_rad)
                fix_a = math.cos(t * 0.9 + offset_rad)
                fix_rms = max(0.1, min(1.0, rms + math.sin(t * 2.0 + offset_rad) * 0.2))

                fix_emo = EmotionCoordinate(valence=fix_v, arousal=fix_a)
                fh, fs, fval = ColorEngine.emotion_to_hsv(fix_emo, rms_energy=fix_rms, master_dimmer=1.0)
                fr, fg, fb = ColorEngine.hsv_to_rgb(fh, fs, fval)

                master_dim = int(round(fval * 255.0))

                if is_rgbw:
                    # Kumastb STL47: Physical 4-Channel RGBW Decomposition
                    rgbw = ColorEngine.rgb_to_physical_rgbw(fr, fg, fb, dimmer=1.0)
                    r, g, b, w = rgbw.to_dmx_bytes()
                    # 8-CH: Dimmer, Red, Green, Blue, White, Strobe, Program, Speed
                    fix_channels = [master_dim, r, g, b, w, 0, 0, 0]
                else:
                    # Alien AL36: 8-CH RGB (Ch 5 Empty, Ch 8 Emptz)
                    # 8-CH: Dimmer, Red, Green, Blue, Empty, Program, Speed, Emptz
                    fix_channels = [master_dim, fr, fg, fb, 0, 0, 0, 0]

                channels_data.extend(fix_channels)

            sender.set_channels(1, channels_data)
            sender.send_frame()
            frame_count += 1

            # Monitor readout
            if is_rgbw:
                r1, g1, b1, w1 = channels_data[1], channels_data[2], channels_data[3], channels_data[4]
                status_str = f"FIX1 (CH1-5): [DIM:{channels_data[0]:3d} R:{r1:3d} G:{g1:3d} B:{b1:3d} W:{w1:3d}]"
            else:
                r1, g1, b1 = channels_data[1], channels_data[2], channels_data[3]
                status_str = f"FIX1 (CH1-4): [DIM:{channels_data[0]:3d} R:{r1:3d} G:{g1:3d} B:{b1:3d}]"

            print(f"\r[Art-Net TX] Frame {frame_count:04d} | Mood: (V:{v:+.2f}, A:{a:+.2f}) | {status_str} | Time: {elapsed:.1f}s", end="", flush=True)

            time.sleep(1.0 / 43.07)

    except KeyboardInterrupt:
        print("\n\nPengujian dihentikan oleh user.")
    finally:
        print("\nMemadamkan fader (Blackout)...")
        sender.blackout()
        sender.close()
        print("✓ Seluruh kanal DMX di-reset ke 0. Sesi selesai.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ZZLUXORA Art-Net Loopback Bridge Test for QLC+")
    parser.add_argument("--ip", default="127.0.0.1", help="Target Art-Net IP address (default: 127.0.0.1)")
    parser.add_argument("--duration", type=float, default=30.0, help="Test duration in seconds (default: 30)")
    parser.add_argument("--fixture", choices=["kumastb", "alien"], default="kumastb",
                        help="Fixture model to simulate: 'kumastb' (8CH RGBW) or 'alien' (8CH RGB)")
    args = parser.parse_args()

    run_fader_test(target_ip=args.ip, duration=args.duration, fixture_model=args.fixture)

"""
qlc_bridge_test.py — Art-Net Loopback Bridge Test for QLC+ Simulation
Sends continuous DMX512 frames to 127.0.0.1:6454 (Universe 0) to verify
that QLC+ Simple Desk / Virtual Console faders move in real time without physical hardware.
"""

import sys
import time
import math
from pathlib import Path

# Ensure root directory in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.artnet_sender import ArtNetSender

def run_fader_test(target_ip: str = "127.0.0.1", duration: float = 30.0):
    print("=" * 70)
    print("🎛️  ZZLUXORA ➔ QLC+ ART-NET LOOPBACK BRIDGE TEST")
    print("=" * 70)
    print(f"Target Host      : {target_ip}:6454")
    print(f"Target Universe  : 0 (maps to Universe 1 in QLC+)")
    print(f"Target Fixtures  : 4x PAR LED RGBW (Channels 1 s.d. 16)")
    print(f"Transmission FPS : 43.07 FPS (Standard DMX refresh)")
    print("-" * 70)
    print("Petunjuk Pengaturan di QLC+:")
    print("1. Buka QLC+ ➔ Tab 'Inputs/Outputs'.")
    print("2. Pada Universe 1, centang kolom 'Input' pada baris 'ArtNet' (127.0.0.1).")
    print("3. Buka Tab 'Simple Desk' di QLC+.")
    print("4. Perhatikan fader channel 1 s.d. 16 akan bergerak otomatis naik-turun!")
    print("=" * 70)
    print("Memulai transmisi paket Art-Net (Tekan Ctrl+C untuk berhenti)...\n")

    sender = ArtNetSender(target_ip=target_ip, universe=0)
    start_time = time.time()
    frame_count = 0

    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            t = elapsed * 2.0  # speed

            # Generate smooth sinusoidal waves for 4 fixtures (16 channels)
            # Fixture 1: Ch 1-4 (R, G, B, W)
            r1 = int((math.sin(t) + 1.0) * 127.5)
            g1 = int((math.sin(t + 2.0) + 1.0) * 127.5)
            b1 = int((math.sin(t + 4.0) + 1.0) * 127.5)
            w1 = int((math.sin(t * 0.5) + 1.0) * 60.0)

            # Fixture 2: Ch 5-8
            r2 = int((math.sin(t + 1.0) + 1.0) * 127.5)
            g2 = int((math.sin(t + 3.0) + 1.0) * 127.5)
            b2 = int((math.sin(t + 5.0) + 1.0) * 127.5)
            w2 = int((math.sin(t * 0.5 + 1.0) + 1.0) * 60.0)

            # Fixture 3: Ch 9-12
            r3 = int((math.sin(t + 2.0) + 1.0) * 127.5)
            g3 = int((math.sin(t + 4.0) + 1.0) * 127.5)
            b3 = int((math.sin(t) + 1.0) * 127.5)
            w3 = int((math.sin(t * 0.5 + 2.0) + 1.0) * 60.0)

            # Fixture 4: Ch 13-16
            r4 = int((math.sin(t + 3.0) + 1.0) * 127.5)
            g4 = int((math.sin(t + 5.0) + 1.0) * 127.5)
            b4 = int((math.sin(t + 1.0) + 1.0) * 127.5)
            w4 = int((math.sin(t * 0.5 + 3.0) + 1.0) * 60.0)

            sender.set_channels(1, [r1, g1, b1, w1, r2, g2, b2, w2, r3, g3, b3, w3, r4, g4, b4, w4])
            sender.send_frame()
            frame_count += 1

            # Real-time console monitor
            print(f"\r[Art-Net TX] Frame {frame_count:04d} | "
                  f"PAR1 (CH1-4): [{r1:3d}, {g1:3d}, {b1:3d}, {w1:3d}] | "
                  f"PAR2 (CH5-8): [{r2:3d}, {g2:3d}, {b2:3d}, {w2:3d}] | "
                  f"Time: {elapsed:.1f}s", end="", flush=True)

            time.sleep(1.0 / 43.0)

    except KeyboardInterrupt:
        print("\n\nPengujian dihentikan oleh user.")
    finally:
        print("\nMemadamkan fader (Blackout)...")
        sender.blackout()
        sender.close()
        print("✓ Seluruh kanal DMX di-reset ke 0. Sesi selesai.")

if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    run_fader_test(target_ip=ip, duration=dur)

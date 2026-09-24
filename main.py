"""
ZZLUXORA v10.0.0 — Flagship Stage Lighting Control & Autonomous Audio-Reactive Engine
Developed for S1 Teknik Komputer FT Universitas Negeri Semarang (UNNES).
Peneliti: Andreas Restuawanta Christwara (NIM: 5312422036)
Dosen Pembimbing: Mario Norman Syah, S.Pd., M.Eng. (NIP: 199304212024061001)
"""

from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path

# Ensure root directory in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core import (
    STFTEngine,
    ColorEngine,
    EmotionModel,
    ArtNetSender,
    AudioLoader,
    FeatureExtractor,
    ProjectIO,
)


def run_cli_demo(target_ip: str = "127.0.0.1", duration: float = 3.0) -> None:
    """Runs a standalone demonstration of the core FFT & Art-Net lighting engine."""
    print("=" * 70)
    print("⚡ ZZLUXORA v10.0.0 — CORE ENGINE STANDALONE RUNTIME")
    print("   Autonomous Audio-Reactive Stage Lighting Architecture")
    print("=" * 70)
    print(f"Target Art-Net Node IP : {target_ip}:6454 (Universe 0)")
    print(f"Sample Rate / Window   : 22,050 Hz | N_FFT = 2048 | Hop = 512 (~43.07 FPS)")

    loader = AudioLoader()
    print("\n[1/3] Generating synthetic Praise & Worship acoustic stream...")
    signal = loader.generate_synthetic_praise_beat(duration_sec=duration)
    print(f"      Signal generated: {len(signal):,} audio samples (~{duration} seconds)")

    print("\n[2/3] Executing STFT & Feature Extraction Pipeline (FFT/Chroma/Centroid/RMS)...")
    extractor = FeatureExtractor()
    t0 = time.time()
    frames = extractor.analyze_audio_stream(signal)
    t_elapsed = time.time() - t0
    print(f"      Analyzed {len(frames)} frames in {t_elapsed * 1000.0:.2f} ms ({len(frames) / t_elapsed:.1f} fps speedup)")

    print("\n[3/3] Streaming Art-Net 4 DMX512 frames to network...")
    artnet = ArtNetSender(target_ip=target_ip, universe=0)
    print("      Stream started (Press Ctrl+C to stop)...")

    try:
        for idx, f in enumerate(frames):
            # Patch to PAR LED channels 1-4
            artnet.set_channels(1, [f.color.red, f.color.green, f.color.blue, f.color.white])
            artnet.send_frame()

            bar = "█" * int(f.rms_energy * 20)
            bar = bar.ljust(20, "░")
            print(f"\rFrame {idx+1:03d}/{len(frames):03d} [{f.time_sec:.2f}s] "
                  f"RMS: [{bar}] | "
                  f"Centroid: {f.spectral_centroid:4.0f}Hz | "
                  f"Valence: {f.emotion.valence:+0.2f} | "
                  f"Arousal: {f.emotion.arousal:+0.2f} | "
                  f"RGBW: ({f.color.red:3d}, {f.color.green:3d}, {f.color.blue:3d}, {f.color.white:3d})",
                  end="", flush=True)
            time.sleep(1.0 / 43.0)
    except KeyboardInterrupt:
        print("\n\nUser interrupted stream.")
    finally:
        print("\n\nExecuting Blackout command...")
        artnet.blackout()
        artnet.close()
        print("✓ All DMX channels reset to 0. Session complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="ZZLUXORA v10 Stage Lighting Control Console")
    parser.add_argument("--cli", action="store_true", help="Run standalone CLI engine demonstration")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Target Art-Net node IP (default: 127.0.0.1)")
    parser.add_argument("--duration", type=float, default=4.0, help="Demo duration in seconds")
    args = parser.parse_args()

    # If --cli or DISPLAY is not available, run CLI
    if args.cli or "DISPLAY" not in os.environ:
        run_cli_demo(target_ip=args.ip, duration=args.duration)
    else:
        # Check if PySide6 is available for GUI
        try:
            from PySide6.QtWidgets import QApplication
            from ui.main_window import ZZLuxoraMainWindow
            app = QApplication(sys.argv)
            window = ZZLuxoraMainWindow()
            window.show()
            sys.exit(app.exec())
        except ImportError:
            print("PySide6 not installed in current environment. Running CLI engine mode...")
            run_cli_demo(target_ip=args.ip, duration=args.duration)


if __name__ == "__main__":
    main()

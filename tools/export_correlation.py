#!/usr/bin/env python3
"""
export_correlation.py - Ekspor fitur audio per-frame dan hitung korelasi Pearson
terhadap keluaran kanal algoritmik, untuk mengisi Tabel 4.4 dan Tabel 4.5 Bab 4.

Alat ini melengkapi CSV 41-kolom pada protokol uji lapangan: CSV tersebut hanya
memuat telemetri jaringan/DMX (run_id..notes) dan TIDAK memuat fitur audio
maupun kanal keluaran. Tabel 4.5 memerlukan pasangan fitur audio -> kanal
keluaran, sehingga diperlukan artefak tersendiri.

Sumber data: mesin ZZLUXORA v10 sendiri (FeatureExtractor.analyze_audio_stream),
yang bersifat deterministik. Ini adalah validasi PERANGKAT LUNAK, bukan
pengukuran lapangan; nyatakan hal itu saat mengisi Bab 4.

Keluaran:
    <outdir>/<lagu>_frames.csv   - satu baris per frame: fitur + kanal keluaran
    <outdir>/<lagu>_repeat.json  - hasil uji pengulangan (Tabel 4.4)
    <outdir>/correlation.csv     - matriks Pearson fitur x kanal (Tabel 4.5)

Penggunaan:
    python3 tools/export_correlation.py data/audio/*.wav --outdir out/
    python3 tools/export_correlation.py data/audio/lagu.wav --repeats 3
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np

# Impor mesin dari repo perangkat lunak. Tambahkan akar repo ke sys.path agar
# skrip dapat dijalankan langsung dari folder tools/.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from core.audio_loader import AudioLoader
    from core.feature_extractor import FeatureExtractor
except ImportError as exc:  # pragma: no cover - pesan arahan
    print(
        f"Gagal mengimpor mesin ZZLUXORA dari {_REPO_ROOT}.\n"
        f"Detail: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(1)

FEATURE_COLUMNS = ("bpm_track", "rms_energy", "spectral_centroid")
OUTPUT_COLUMNS = ("dimmer", "r", "g", "b", "w")

# Catatan metodologis untuk Tabel 4.5:
# 1. `bpm_track` adalah SKALAR per lagu, bukan nilai per-frame. Korelasi Pearson
#    frame-level antara BPM dan kanal keluaran karena itu tidak bermakna
#    (vektor konstan -> r = 0). Laporkan BPM sebagai deskriptif per lagu, dan
#    bila korelasi BPM diperlukan, hitung pada tingkat lagu lintas lagu
#    (satu titik data per lagu), bukan per frame.
# 2. `dimmer` pada ColorRGBW selalu 1.0 (lihat ColorEngine.process_frame);
#    kecerahan sesungguhnya dibawa oleh komponen Value HSV, bukan oleh field
#    dimmer. Kolom `dimmer` di sini tetap diekspor untuk kelengkapan, tetapi
#    korelasinya terhadap fitur akan selalu 0 karena vektor konstan.
# 3. `spectral_centroid_signed` disediakan sebagai padanan ternormalisasi agar
#    korelasi timbre dapat dibaca; nilai mentah Hz juga tetap diekspor.


def analyse_once(file_path: Path) -> List[Dict[str, float]]:
    """Jalankan pipeline penuh sekali; kembalikan baris per-frame."""
    loader = AudioLoader()
    signal, _sr = loader.load_audio(str(file_path))
    extractor = FeatureExtractor()
    frames = extractor.analyze_audio_stream(signal)
    bpm = extractor.estimate_tempo_bpm(signal)

    rows: List[Dict[str, float]] = []
    for frame in frames:
        rows.append({
            "frame_index": frame.frame_index,
            "time_sec": round(frame.time_sec, 6),
            "bpm_track": round(float(bpm), 6),
            "rms_energy": round(float(frame.rms_energy), 8),
            "spectral_centroid": round(float(frame.spectral_centroid), 6),
            "dimmer": round(float(frame.color.dimmer), 6),
            "r": int(frame.color.red),
            "g": int(frame.color.green),
            "b": int(frame.color.blue),
            "w": int(frame.color.white),
        })
    return rows


def signature(rows: Sequence[Dict[str, float]]) -> Dict[str, Any]:
    """Ringkasan deterministik untuk uji pengulangan (Tabel 4.4)."""
    rms_sum = float(np.sum([r["rms_energy"] for r in rows]))
    centroid_sum = float(np.sum([r["spectral_centroid"] for r in rows]))
    first = rows[0] if rows else {}
    return {
        "frame_count": len(rows),
        "rms_sum": round(rms_sum, 6),
        "centroid_sum": round(centroid_sum, 6),
        "first_frame_rgbw": [first.get("r", 0), first.get("g", 0), first.get("b", 0), first.get("w", 0)],
    }


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    """Koefisien korelasi Pearson; None bila salah satu vektor konstan.

    Mengembalikan None (bukan 0.0) ketika vektor tidak bervariasi, agar sel
    yang tidak bermakna tidak tampak seperti korelasi nol yang nyata.
    """
    ax = np.asarray(x, dtype=np.float64)
    ay = np.asarray(y, dtype=np.float64)
    if ax.size < 2 or ay.size < 2:
        return None
    if ax.std() < 1e-12 or ay.std() < 1e-12:
        return None
    return float(np.corrcoef(ax, ay)[0, 1])


def write_frames(out_path: Path, rows: Sequence[Dict[str, float]]) -> None:
    fieldnames = ["frame_index", "time_sec", *FEATURE_COLUMNS, *OUTPUT_COLUMNS]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("audio", nargs="+", type=Path, help="Berkas audio lagu terpilih")
    parser.add_argument("--outdir", type=Path, default=Path("out"), help="Folder keluaran")
    parser.add_argument("--repeats", type=int, default=1, help="Jumlah pengulangan untuk uji determinisme (Tabel 4.4)")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    correlation_rows: List[Dict[str, Any]] = []

    for audio_path in args.audio:
        if not audio_path.is_file():
            print(f"Dilewati (tidak ada): {audio_path}", file=sys.stderr)
            continue

        print(f"Memproses {audio_path.name} ...", file=sys.stderr)
        runs = [analyse_once(audio_path) for _ in range(max(1, args.repeats))]
        rows = runs[0]

        write_frames(args.outdir / f"{audio_path.stem}_frames.csv", rows)

        # Tabel 4.4 - uji pengulangan
        sigs = [signature(r) for r in runs]
        identical = all(s == sigs[0] for s in sigs)
        repeat_report = {
            "file": str(audio_path),
            "repeats": len(runs),
            "identical": identical,
            "signatures": sigs,
            "note": "Perbedaan keluaran teramati: 0" if identical else "Ada perbedaan; periksa sebelum melaporkan",
        }
        (args.outdir / f"{audio_path.stem}_repeat.json").write_text(
            json.dumps(repeat_report, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Tabel 4.5 - matriks korelasi
        for feature in FEATURE_COLUMNS:
            entry: Dict[str, Any] = {"file": audio_path.name, "feature": feature}
            feature_values = [r[feature] for r in rows]
            for channel in OUTPUT_COLUMNS:
                channel_values = [r[channel] for r in rows]
                value = pearson(feature_values, channel_values)
                entry[channel] = "" if value is None else round(value, 6)
            correlation_rows.append(entry)

    if correlation_rows:
        corr_path = args.outdir / "correlation.csv"
        fieldnames = ["file", "feature", *OUTPUT_COLUMNS]
        with corr_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in correlation_rows:
                writer.writerow(row)
        print(f"Matriks korelasi (Tabel 4.5) -> {corr_path}", file=sys.stderr)

    print("Selesai. Isi Tabel 4.4 dari *_repeat.json dan Tabel 4.5 dari correlation.csv.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

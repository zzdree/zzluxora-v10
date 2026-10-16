#!/usr/bin/env python3
"""
fetch_test_audio.py - Unduh bahan uji audio NYATA untuk penelitian Bab 4.

Sepuluh berkas di data/audio/ bersifat SINTETIS (dibangkitkan
tools/generate_benchmark_audio.py, durasi seragam 12,00 detik). Materi itu sah
untuk pengujian perangkat lunak, tetapi tidak memadai untuk penilaian persepsi
(H1) yang menuntut rekaman lagu rohani sesungguhnya.

Alat ini mengunduh rekaman nyata dari tautan yang diberikan, mengonversinya ke
format yang sama dengan mesin ZZLUXORA (mono, 22050 Hz, PCM WAV) melalui
core.youtube_importer - rantai yang sama dengan tombol impor di GUI, sehingga
tidak ada jalur konversi kedua yang perlu dipercaya.

Bab 4 4.1.2 menuntut "identitas serta izin pemakaian materi dicatat". Karena
itu setiap unduhan menghasilkan sidecar <slug>.provenance.json yang memuat
tautan sumber, judul yang dilaporkan penyedia, tanggal pengambilan, dan hash
berkas. Sidecar inilah yang dilampirkan saat konsultasi pembimbing; pertanyaan
izin pemakaian materi adalah keputusan pembimbing, bukan keputusan alat ini.

Penggunaan:
    # Tulis daftar di satu berkas: satu baris "slug<TAB>url"
    python3 tools/fetch_test_audio.py --manifest daftar_lagu.txt

    # Atau langsung dari baris perintah
    python3 tools/fetch_test_audio.py --slug gms-nyalakan-apimu --url <tautan>

    # Tujuan bawaan data/audio_real/ agar tidak menimpa berkas sintetis
    python3 tools/fetch_test_audio.py --manifest daftar_lagu.txt --outdir data/audio_real

Keluaran:
    <outdir>/<slug>.wav                 - mono 22050 Hz PCM WAV
    <outdir>/<slug>.provenance.json     - sumber, tanggal, hash, durasi nyata
    <outdir>/fetch_report.json          - ringkasan seluruh unduhan sesi ini
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core import youtube_importer as yt  # noqa: E402


class ManifestError(ValueError):
    """Baris daftar tidak dapat dibaca."""


def parse_manifest(path: Path) -> List[Dict[str, str]]:
    """Baca berkas daftar: satu baris "slug<TAB>url", abaikan kosong dan komentar."""
    entries: List[Dict[str, str]] = []
    for nomor, baris in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        teks = baris.strip()
        if not teks or teks.startswith("#"):
            continue
        bagian = [p.strip() for p in teks.split("\t") if p.strip()]
        if len(bagian) != 2:
            raise ManifestError(
                f"{path.name} baris {nomor}: butuh 'slug<TAB>url', ditemukan {len(bagian)} kolom"
            )
        slug, url = bagian
        validasi_slug(slug, f"{path.name} baris {nomor}")
        entries.append({"slug": slug, "url": url})
    if not entries:
        raise ManifestError(f"{path.name}: tidak ada entri yang dapat dibaca")
    return entries


def validasi_slug(slug: str, konteks: str) -> None:
    """Slug menjadi nama berkas, jadi batasi ke karakter yang aman."""
    aman = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if not slug or set(slug.lower()) - aman:
        raise ManifestError(
            f"{konteks}: slug {slug!r} tidak aman sebagai nama berkas "
            "(pakai huruf kecil, angka, tanda hubung, atau garis bawah)"
        )


def hash_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as berkas:
        for potongan in iter(lambda: berkas.read(1 << 20), b""):
            digest.update(potongan)
    return digest.hexdigest()


def periksa_audio(path: Path) -> Dict[str, Any]:
    """Baca properti nyata berkas hasil, bukan asumsi dari pengaturan konversi."""
    with wave.open(str(path), "rb") as w:
        kanal = w.getnchannels()
        laju = w.getframerate()
        lebar = w.getsampwidth()
        bingkai = w.getnframes()
        durasi = bingkai / laju if laju else 0.0
    return {
        "channels": kanal,
        "sample_rate": laju,
        "sample_width_bytes": lebar,
        "frames": bingkai,
        "duration_seconds": round(durasi, 4),
        "mono_22050": kanal == 1 and laju == yt.TARGET_SAMPLE_RATE,
    }


def unduh_satu(entri: Dict[str, str], outdir: Path, force: bool) -> Dict[str, Any]:
    """Unduh satu lagu dan tulis sidecar provenance. Tidak pernah menimpa tanpa force."""
    slug, url = entri["slug"], entri["url"]
    tujuan = outdir / f"{slug}.wav"
    sidecar = outdir / f"{slug}.provenance.json"
    hasil: Dict[str, Any] = {"slug": slug, "url": url, "status": "gagal", "pesan": ""}

    if tujuan.exists() and not force:
        hasil["pesan"] = f"{tujuan.name} sudah ada (pakai --force untuk menimpa)"
        return hasil

    try:
        jalur = yt.download_and_convert(
            url,
            outdir,
            progress=lambda persen, pesan: print(f"    [{persen:3d}%] {pesan}"),
        )
    except yt.YouTubeImportError as exc:
        hasil["pesan"] = str(exc)
        return hasil

    # youtube_importer menamai berkas dari judul video, jadi pindahkan ke slug
    # yang kita kendalikan agar daftar berkas bab 4 stabil dan dapat dirujuk.
    jalur = Path(jalur)
    if jalur != tujuan:
        if tujuan.exists():
            tujuan.unlink()
        jalur.replace(tujuan)

    properti = periksa_audio(tujuan)
    provenance = {
        "slug": slug,
        "source_url": url,
        "provider": "YouTube",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256": hash_sha256(tujuan),
        "file": tujuan.name,
        **properti,
        "note": (
            "Rekaman NYATA, bukan materi sintetis. Identitas dan izin pemakaian "
            "materi wajib dicatat dan disetujui pembimbing sebelum dipakai untuk "
            "penilaian persepsi pada Bab 4."
        ),
    }
    sidecar.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    hasil.update({"status": "berhasil", "pesan": "", "file": tujuan.name, **properti})
    return hasil


def bangun_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unduh bahan uji audio nyata untuk penelitian Bab 4 ZZLUXORA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Contoh berkas daftar:\n"
            "  # slug<TAB>url\n"
            "  gms-nyalakan-apimu\thttps://www.youtube.com/watch?v=...\n"
        ),
    )
    parser.add_argument("--manifest", type=Path, help="Berkas daftar 'slug<TAB>url'")
    parser.add_argument("--slug", help="Slug untuk pemakaian --url langsung")
    parser.add_argument("--url", help="Tautan tunggal, dipakai bersama --slug")
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("data/audio_real"),
        help="Direktori tujuan (bawaan: data/audio_real)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help=(
            "Jalankan pemeriksaan mandiri: laporkan properti semua berkas di "
            "--outdir dan tandai durasi seragam 12,00 detik sebagai materi sintetis"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Timpa berkas yang sudah ada (bawaan: lewati dan laporkan)",
    )
    return parser


def kumpulkan_entri(args: argparse.Namespace) -> List[Dict[str, str]]:
    entri: List[Dict[str, str]] = []
    if args.manifest:
        entri.extend(parse_manifest(args.manifest))
    if args.url or args.slug:
        if not (args.url and args.slug):
            raise ManifestError("--url dan --slug harus dipakai bersama")
        validasi_slug(args.slug, "--slug")
        entri.append({"slug": args.slug, "url": args.url})
    if not entri:
        raise ManifestError("butuh --manifest, atau --slug bersama --url")
    return entri


def jalankan_self_test(outdir: Path) -> int:
    """Laporkan properti berkas audio di outdir dan tandai materi sintetis.

    Materi bawaan generate_benchmark_audio.py seragam 12,00 detik. Durasi yang
    berbeda-beda adalah bukti cepat bahwa materi yang dipakai adalah rekaman
    nyata, bukan berkas bangkitan.
    """
    berkas = sorted(p for p in outdir.glob("*.wav"))
    if not berkas:
        print(f"tidak ada berkas .wav di {outdir}", file=sys.stderr)
        return 1

    print(f"Memeriksa {len(berkas)} berkas di {outdir}\n")
    print(f"{'berkas':44s} {'durasi':>9s} {'laju':>7s} {'kanal':>5s}  dugaan")
    seragam = 0
    for p in berkas:
        try:
            info = periksa_audio(p)
        except wave.Error as exc:
            print(f"{p.name[:44]:44s} {'-':>9s} {'-':>7s} {'-':>5s}  BUKAN WAV SAH: {exc}")
            continue
        durasi = info["duration_seconds"]
        dugaan = "SINTETIS (12,00 s)" if abs(durasi - 12.0) < 0.005 else "nyata/kustom"
        if abs(durasi - 12.0) < 0.005:
            seragam += 1
        print(
            f"{p.name[:44]:44s} {durasi:8.2f}s {info['sample_rate']:7d} "
            f"{info['channels']:5d}  {dugaan}"
        )

    print(
        f"\n{seragam} dari {len(berkas)} berkas berdurasi tepat 12,00 s. "
        "Materi sintetis TIDAK memadai untuk penilaian persepsi (Bab 4 4.1.2)."
    )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = bangun_parser().parse_args(argv)

    if args.self_test:
        return jalankan_self_test(args.outdir)

    try:
        entri = kumpulkan_entri(args)
    except ManifestError as exc:
        print(f"kesalahan: {exc}", file=sys.stderr)
        return 2

    status = yt.check_dependencies()
    if any(not s.available for s in status):
        print(yt.dependency_report(), file=sys.stderr)
        return 2

    args.outdir.mkdir(parents=True, exist_ok=True)
    print(f"Tujuan: {args.outdir.resolve()}")
    print(f"Jumlah lagu: {len(entri)}\n")

    laporan: List[Dict[str, Any]] = []
    for urutan, satu in enumerate(entri, 1):
        print(f"[{urutan}/{len(entri)}] {satu['slug']}")
        hasil = unduh_satu(satu, args.outdir, args.force)
        laporan.append(hasil)
        if hasil["status"] == "berhasil":
            print(
                f"    OK  {hasil['duration_seconds']:.2f} s  "
                f"{hasil['sample_rate']} Hz  {hasil['channels']} kanal\n"
            )
        else:
            print(f"    GAGAL  {hasil['pesan']}\n", file=sys.stderr)

    (args.outdir / "fetch_report.json").write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "outdir": str(args.outdir),
                "entries": laporan,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    berhasil = [h for h in laporan if h["status"] == "berhasil"]
    print(f"Selesai: {len(berhasil)}/{len(laporan)} berhasil.")
    if berhasil:
        print("Durasi nyata (bukti materi bukan sintetis - yang sintetis seragam 12,00 s):")
        for h in berhasil:
            print(f"  {h['slug']:32s} {h['duration_seconds']:8.2f} s")
    if len(berhasil) != len(laporan):
        print("Sebagian gagal; periksa pesan di atas.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

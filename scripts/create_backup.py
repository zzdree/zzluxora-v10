#!/usr/bin/env python3
"""
create_backup.py - Ekspor seluruh bank hindsight ke satu berkas arsip, lalu
konversi ke memlog SQLite.

Konteks: hindsight-api memuat dua model ML lokal dan memuncak di sekitar 1,1 GB
RAM. Di laptop 3,6 GB itu tidak dapat berjalan bersamaan dengan sesi kerja lain,
sehingga API sering dihentikan sistem. Skrip ini memastikan data tidak hanya
hidup di dalam server itu.

Hasil:
  memory-backup/<bank>-bank.zip   arsip asli dari hindsight (dapat dipulihkan)
  memory/memlog.db                basis data SQLite untuk pencarian harian

Penggunaan:
    python3 scripts/create_backup.py                     # semua bank
    python3 scripts/create_backup.py --base-url http://127.0.0.1:8888
    python3 scripts/create_backup.py --skip-hindsight    # hanya konversi arsip lama
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hindsight_to_memlog  # noqa: E402
import memlog  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = REPO_ROOT.parent / "memory-backup"
DEFAULT_BASE_URL = "http://127.0.0.1:8888"
EXPORT_TIMEOUT_SEC = 300
POLL_INTERVAL_SEC = 5


def request_json(url: str, payload: dict | None = None, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def api_reachable(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=8) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def list_banks(base_url: str) -> list[str]:
    payload = request_json(f"{base_url}/v1/default/banks", timeout=30)
    banks = payload if isinstance(payload, list) else payload.get("banks", [])
    names = []
    for item in banks:
        if isinstance(item, dict):
            name = item.get("bank_id") or item.get("id")
            if name:
                names.append(name)
    return names


def export_bank(base_url: str, bank: str, target_dir: Path) -> Path | None:
    """Queue an export, wait for it, and download the resulting archive."""
    query = "include_data=true&include_bank_config=true&include_history=true"
    job = request_json(f"{base_url}/v1/default/banks/{bank}/transfer/export?{query}", {})
    operation_id = job.get("operation_id")
    if not operation_id:
        print(f"  {bank}: ekspor tidak menghasilkan operation_id", file=sys.stderr)
        return None

    deadline = time.time() + EXPORT_TIMEOUT_SEC
    while time.time() < deadline:
        status = request_json(
            f"{base_url}/v1/default/banks/{bank}/operations/{operation_id}", timeout=30
        )
        state = status.get("status")
        if state == "completed":
            meta = status.get("result_metadata") or {}
            download_url = meta.get("download_url")
            if not download_url:
                print(f"  {bank}: selesai tanpa download_url", file=sys.stderr)
                return None
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{bank}-bank.zip"
            with urllib.request.urlopen(
                f"{base_url}{download_url}", timeout=180
            ) as response:
                target.write_bytes(response.read())
            return target
        if state in ("failed", "cancelled"):
            print(f"  {bank}: ekspor {state}: {status.get('error_message')}", file=sys.stderr)
            return None
        time.sleep(POLL_INTERVAL_SEC)

    print(f"  {bank}: ekspor melewati batas waktu {EXPORT_TIMEOUT_SEC}s", file=sys.stderr)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Arsipkan hindsight lalu konversi ke memlog.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--db", type=Path, default=memlog.DEFAULT_DB)
    parser.add_argument("--backup-dir", type=Path, default=BACKUP_DIR)
    parser.add_argument("--skip-hindsight", action="store_true",
                        help="lewati ekspor; hanya konversi arsip yang sudah ada")
    args = parser.parse_args()

    if not args.skip_hindsight:
        if not api_reachable(args.base_url):
            print(f"hindsight-api tidak menjawab di {args.base_url}.", file=sys.stderr)
            print("jalankan dulu:", file=sys.stderr)
            print("  cd ../hindsight && set -a && . ./.env.local/hindsight.env && set +a", file=sys.stderr)
            print("  nohup ~/ANDREAS/.venv-hindsight/bin/hindsight-api > /tmp/hs.log 2>&1 &", file=sys.stderr)
            print("atau pakai --skip-hindsight untuk mengonversi arsip yang sudah ada.", file=sys.stderr)
            return 1

        banks = list_banks(args.base_url)
        if not banks:
            print("tidak ada bank yang ditemukan", file=sys.stderr)
            return 1
        print(f"mengarsipkan {len(banks)} bank -> {args.backup_dir}")
        for bank in banks:
            produced = export_bank(args.base_url, bank, args.backup_dir)
            if produced:
                print(f"  {bank:<22} {produced.stat().st_size:>8} bytes")
    else:
        print("melewati ekspor hindsight")

    archives = sorted(args.backup_dir.glob("*.zip"))
    if not archives:
        print(f"tidak ada arsip di {args.backup_dir}", file=sys.stderr)
        return 1

    print()
    print(f"mengonversi {len(archives)} arsip -> {args.db}")
    conn = memlog.connect(args.db)
    try:
        total_docs = total_facts = 0
        for archive in archives:
            bank = archive.name.replace("-bank.zip", "").replace(".zip", "")
            docs, facts = hindsight_to_memlog.import_bank(conn, archive, bank)
            total_docs += docs
            total_facts += facts
            print(f"  {bank:<22} {docs:>3} dokumen, {facts:>3} fakta")
        print()
        print(f"selesai: {total_docs} dokumen + {total_facts} fakta di {args.db}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
hindsight_to_memlog.py - Impor ekspor hindsight (bank .zip) ke memlog SQLite.

Hindsight menyimpan tiap catatan sebagai satu dokumen berisi original_text,
tags, dan daftar facts hasil ekstraksi LLM. Memlog menyimpan catatan datar, jadi
konverter ini memetakan:

    dokumen  -> satu catatan (judul diambil dari baris pertama, isi = original_text)
    faktum   -> satu catatan tambahan (isi = pernyataan faktum)

Faktum disertakan karena hampir semua nilai pencarian ada di sana: hasil
ekstraksi jauh lebih ringkas daripada teks aslinya, dan itulah yang akan
mencocokkan pertanyaan singkat.

Penggunaan:
    python3 scripts/hindsight_to_memlog.py <bank.zip> [...] --db memory/memlog.db
    python3 scripts/hindsight_to_memlog.py /path/memory-backup/*.zip
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memlog  # noqa: E402  (module lives next to this script)


def title_from_text(text: str, fallback: str) -> str:
    """Use the first meaningful line as the title, truncated to a sane length."""
    for line in (text or "").splitlines():
        stripped = line.strip().lstrip("#").strip()
        if len(stripped) >= 8:
            return stripped[:80]
    return fallback


def load_documents(zip_path: Path) -> list[dict]:
    documents: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(tmp)
        for doc_file in sorted(Path(tmp).glob("documents/*.json")):
            try:
                documents.append(json.loads(doc_file.read_text(encoding="utf-8")))
            except (OSError, ValueError) as exc:
                print(f"  lewati {doc_file.name}: {exc}", file=sys.stderr)
    return documents


def import_bank(conn: sqlite3.Connection, zip_path: Path, bank_name: str) -> tuple[int, int]:
    documents = load_documents(zip_path)
    added = 0
    facts_added = 0

    for index, doc in enumerate(documents, start=1):
        text = (doc.get("original_text") or "").strip()
        if not text:
            continue
        tags = doc.get("tags") or []
        tag_string = " ".join(str(t) for t in tags)
        created = doc.get("created_at") or memlog.now_iso()
        title = title_from_text(text, f"{bank_name} dokumen {index}")

        exists = conn.execute(
            "SELECT 1 FROM notes WHERE bank = ? AND title = ? AND created_at = ?",
            (bank_name, title, created),
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO notes (bank, title, body, tags, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (bank_name, title, text, tag_string, created, created),
            )
            added += 1

        # Facts carry the distilled statements, which is what a short query matches.
        for fact_index, fact in enumerate(doc.get("facts") or [], start=1):
            statement = (fact.get("text") or fact.get("statement") or "").strip()
            if not statement:
                continue
            fact_title = f"{title} - fakta {fact_index}"[:80]
            # Deduplicate on the statement itself, not on the title. Titles are
            # derived from the document and several facts share a prefix, so a
            # title check rejected almost every fact after the first.
            already = conn.execute(
                "SELECT 1 FROM notes WHERE bank = ? AND body = ?",
                (bank_name, statement),
            ).fetchone()
            if already:
                continue
            fact_type = fact.get("fact_type") or fact.get("type") or ""
            conn.execute(
                "INSERT INTO notes (bank, title, body, tags, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (bank_name, fact_title, statement,
                 f"{tag_string} {fact_type}".strip(), created, created),
            )
            facts_added += 1

    conn.commit()
    return added, facts_added


def main() -> int:
    parser = argparse.ArgumentParser(description="Impor ekspor hindsight ke memlog.")
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--db", type=Path, default=memlog.DEFAULT_DB)
    parser.add_argument("--bank", help="paksa nama bank (bawaan: nama berkas zip)")
    args = parser.parse_args()

    conn = memlog.connect(args.db)
    try:
        total_docs = total_facts = 0
        for archive in args.archives:
            if not archive.is_file():
                print(f"tidak ada: {archive}", file=sys.stderr)
                continue
            bank = args.bank or archive.name.replace("-bank.zip", "").replace(".zip", "")
            docs, facts = import_bank(conn, archive, bank)
            total_docs += docs
            total_facts += facts
            print(f"  {bank:<22} {docs} dokumen, {facts} fakta")
        print()
        print(f"total: {total_docs} dokumen + {total_facts} fakta diimpor ke {args.db}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

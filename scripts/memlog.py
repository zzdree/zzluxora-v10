#!/usr/bin/env python3
"""
memlog.py - Memori agen berbasis SQLite dengan pencarian teks penuh (FTS5).

Dibuat sebagai alternatif ringan untuk hindsight-api, yang memuat dua model ML
lokal (embedding + reranker) dan memuncak di sekitar 1,1 GB RAM. Skrip ini
memakai SQLite FTS5 dari pustaka standar Python: tanpa server, tanpa model,
tanpa dependensi tambahan, dan tanpa proses latar.

Kemampuan:
  - simpan catatan bernama (bank + judul + isi + tag)
  - cari dengan sintaks FTS5 (AND, OR, NOT, frasa "kutipan", prefix*)
  - tampilkan, sunting, dan hapus catatan
  - ekspor seluruh basis ke JSON dan impor kembali

Pencarian bersifat leksikal (kata kunci), bukan semantik. Untuk ingatan yang
ditulis dengan istilah serupa, hasilnya setara; untuk parafrase jauh, hasilnya
lebih lemah daripada embedding. Sebagai gantinya ia hemat RAM dan langsung
jalan.

Penggunaan:
    python3 scripts/memlog.py add --bank zzluxora --title "Tombol netral" \
        --tag desain --body "Tombol aksi wajib abu-abu; warna hanya untuk makna."
    python3 scripts/memlog.py search "tombol netral" --bank zzluxora
    python3 scripts/memlog.py show 1
    python3 scripts/memlog.py list --bank zzluxora
    python3 scripts/memlog.py export backup.json
    python3 scripts/memlog.py import backup.json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_DB = Path(__file__).resolve().parent.parent / "memory" / "memlog.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    bank       TEXT NOT NULL,
    title      TEXT NOT NULL,
    body       TEXT NOT NULL,
    tags       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_bank ON notes(bank);

-- FTS5 keeps an inverted index so search is instant without loading the corpus
-- into memory. content='notes' makes it an external-content table, so the text
-- is stored once and the index stays in sync through triggers.
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title, body, tags,
    content='notes', content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, title, body, tags)
    VALUES (new.id, new.title, new.body, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, body, tags)
    VALUES ('delete', old.id, old.title, old.body, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, body, tags)
    VALUES ('delete', old.id, old.title, old.body, old.tags);
    INSERT INTO notes_fts(rowid, title, body, tags)
    VALUES (new.id, new.title, new.body, new.tags);
END;
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cmd_add(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    stamp = now_iso()
    cur = conn.execute(
        "INSERT INTO notes (bank, title, body, tags, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (args.bank, args.title, args.body, " ".join(args.tag or []), stamp, stamp),
    )
    conn.commit()
    print(f"disimpan: id={cur.lastrowid} bank={args.bank} judul={args.title!r}")
    return 0


def _fts_query(raw: str) -> str:
    """Make a plain query searchable, without breaking real FTS5 syntax.

    Two things forced this, both found by testing the queries an agent would
    actually type, not the ones that look tidy:

    1. A bare `foo bar` in FTS5 is a PHRASE, so it matches only where the words
       are adjacent. Someone typing `timezone kalender` means "both terms", and
       an empty result reads as "no such note" rather than "wrong syntax".
    2. A hyphen is FTS5's NOT operator. `next-server` parses as `next NOT
       server` and fails with `no such column: server`. So every note whose
       title or tag used a hyphen (anti-slop, next-server, 6-Minggu) was
       unfindable by the term most likely to be typed.

    Each term is therefore quoted, which makes FTS5 treat it as literal text,
    and bare terms are joined with AND. Explicit AND/OR/NOT and existing quoted
    phrases pass through, so a caller who knows FTS5 keeps full control.
    """
    if not raw.strip():
        return raw
    if any(op in f' {raw.upper()} ' for op in (" AND ", " OR ", " NOT ")):
        return raw

    # Split on whitespace, but keep a quoted run together: a phrase the caller
    # wrote on purpose must not be torn into separate AND-ed words.
    parts: list[str] = []
    for token in raw.split():
        token = token.strip()
        if not token:
            continue
        if token.endswith('*') and not token.startswith('"'):
            parts.append(token)          # prefix search, syntax already correct
        elif token.startswith('"'):
            parts.append(token)          # opening quote; the loop below closes it
        else:
            parts.append(f'"{token}"')

    # Re-join anything that opened a quote but was split across a space.
    joined: list[str] = []
    open_run: str | None = None
    for part in parts:
        if open_run is not None:
            open_run += " " + part
            if part.endswith('"'):
                joined.append(open_run)
                open_run = None
            continue
        if part.startswith('"') and not (len(part) > 1 and part.endswith('"')):
            open_run = part
            continue
        joined.append(part)
    if open_run is not None:
        joined.append(open_run)
    parts = joined

    if not parts:
        return raw
    return " AND ".join(parts)


def cmd_search(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    # FTS5 syntax passes through unchanged: AND/OR/NOT, "phrases", prefix*.
    # A bare multi-word query is joined with AND so it means "all of these".
    sql = (
        "SELECT n.id, n.bank, n.title, n.tags, n.updated_at, "
        "       snippet(notes_fts, 1, '[', ']', ' ... ', 12) AS excerpt, "
        "       bm25(notes_fts) AS score "
        "FROM notes_fts JOIN notes n ON n.id = notes_fts.rowid "
        "WHERE notes_fts MATCH ?"
    )
    params: list = [_fts_query(args.query)]
    if args.bank:
        sql += " AND n.bank = ?"
        params.append(args.bank)
    sql += " ORDER BY score LIMIT ?"
    params.append(args.limit)

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as exc:
        print(f"sintaks pencarian ditolak FTS5: {exc}", file=sys.stderr)
        print('petunjuk: bungkus frasa dengan kutip, mis. "tombol netral"', file=sys.stderr)
        return 1

    if not rows:
        print("tidak ada catatan yang cocok")
        return 0

    print(f"{len(rows)} hasil:")
    for row in rows:
        print()
        print(f"  [{row['id']}] {row['title']}  (bank={row['bank']}, {row['updated_at'][:10]})")
        if row["tags"]:
            print(f"       tag: {row['tags']}")
        print(f"       {row['excerpt']}")
    return 0


def cmd_show(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (args.id,)).fetchone()
    if row is None:
        print(f"catatan id={args.id} tidak ada", file=sys.stderr)
        return 1
    print(f"id     : {row['id']}")
    print(f"bank   : {row['bank']}")
    print(f"judul  : {row['title']}")
    print(f"tag    : {row['tags'] or '-'}")
    print(f"dibuat : {row['created_at']}")
    print(f"diubah : {row['updated_at']}")
    print()
    print(row["body"])
    return 0


def cmd_list(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    sql = "SELECT id, bank, title, tags, updated_at FROM notes"
    params: list = []
    if args.bank:
        sql += " WHERE bank = ?"
        params.append(args.bank)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(args.limit)
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        print("belum ada catatan")
        return 0
    for row in rows:
        print(f"  [{row['id']:>3}] {row['updated_at'][:10]}  {row['bank']:<22} {row['title']}")
    print()
    print(f"total ditampilkan: {len(rows)}")
    return 0


def cmd_edit(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    row = conn.execute("SELECT id FROM notes WHERE id = ?", (args.id,)).fetchone()
    if row is None:
        print(f"catatan id={args.id} tidak ada", file=sys.stderr)
        return 1
    sets, params = [], []
    if args.title is not None:
        sets.append("title = ?")
        params.append(args.title)
    if args.body is not None:
        sets.append("body = ?")
        params.append(args.body)
    if args.tag is not None:
        sets.append("tags = ?")
        params.append(" ".join(args.tag))
    if not sets:
        print("tidak ada perubahan diminta", file=sys.stderr)
        return 1
    sets.append("updated_at = ?")
    params.append(now_iso())
    params.append(args.id)
    conn.execute(f"UPDATE notes SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    print(f"diperbarui: id={args.id}")
    return 0


def cmd_delete(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    cur = conn.execute("DELETE FROM notes WHERE id = ?", (args.id,))
    conn.commit()
    if cur.rowcount == 0:
        print(f"catatan id={args.id} tidak ada", file=sys.stderr)
        return 1
    print(f"dihapus: id={args.id}")
    return 0


def cmd_export(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    rows = conn.execute("SELECT * FROM notes ORDER BY id").fetchall()
    payload = {
        "exported_at": now_iso(),
        "count": len(rows),
        "notes": [dict(row) for row in rows],
    }
    Path(args.path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"diekspor {len(rows)} catatan -> {args.path}")
    return 0


def cmd_import(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    data = json.loads(Path(args.path).read_text(encoding="utf-8"))
    notes = data.get("notes", [])
    added = 0
    for note in notes:
        exists = conn.execute(
            "SELECT 1 FROM notes WHERE bank = ? AND title = ? AND created_at = ?",
            (note.get("bank", "default"), note.get("title", ""), note.get("created_at", "")),
        ).fetchone()
        if exists:
            continue
        stamp = note.get("created_at") or now_iso()
        conn.execute(
            "INSERT INTO notes (bank, title, body, tags, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (note.get("bank", "default"), note.get("title", "(tanpa judul)"),
             note.get("body", ""), note.get("tags", ""), stamp,
             note.get("updated_at") or stamp),
        )
        added += 1
    conn.commit()
    skipped = len(notes) - added
    print(f"diimpor {added} catatan, dilewati {skipped} (sudah ada)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Memori agen ringan berbasis SQLite FTS5.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"berkas basis data (bawaan: {DEFAULT_DB})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="simpan catatan baru")
    p_add.add_argument("--bank", required=True)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--body", required=True)
    p_add.add_argument("--tag", action="append", help="ulangi untuk beberapa tag")
    p_add.set_defaults(func=cmd_add)

    p_search = sub.add_parser("search", help="cari catatan (sintaks FTS5)")
    p_search.add_argument("query")
    p_search.add_argument("--bank")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.set_defaults(func=cmd_search)

    p_show = sub.add_parser("show", help="tampilkan satu catatan")
    p_show.add_argument("id", type=int)
    p_show.set_defaults(func=cmd_show)

    p_list = sub.add_parser("list", help="daftar catatan terbaru")
    p_list.add_argument("--bank")
    p_list.add_argument("--limit", type=int, default=30)
    p_list.set_defaults(func=cmd_list)

    p_edit = sub.add_parser("edit", help="ubah catatan")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--title")
    p_edit.add_argument("--body")
    p_edit.add_argument("--tag", action="append")
    p_edit.set_defaults(func=cmd_edit)

    p_del = sub.add_parser("delete", help="hapus catatan")
    p_del.add_argument("id", type=int)
    p_del.set_defaults(func=cmd_delete)

    p_exp = sub.add_parser("export", help="ekspor ke JSON")
    p_exp.add_argument("path")
    p_exp.set_defaults(func=cmd_export)

    p_imp = sub.add_parser("import", help="impor dari JSON")
    p_imp.add_argument("path")
    p_imp.set_defaults(func=cmd_import)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    conn = connect(args.db)
    try:
        return args.func(conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

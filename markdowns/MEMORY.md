# Memori Agen: memlog (SQLite) menggantikan hindsight-api

## Ringkasan keputusan

`hindsight-api` memuat **dua model ML lokal** (embedding `bge-small-en-v1.5` dan reranker `ms-marco-MiniLM-L-6`) sehingga memuncak di **1.149 MB RAM**. Di laptop ini (3,6 GB total) API tidak dapat berjalan bersamaan dengan sesi kerja lain, dan berulang kali dihentikan sistem karena kehabisan memori. Sebagai gantinya dipakai **memlog**, pencarian berbasis **SQLite FTS5** dari pustaka standar Python.

| | hindsight-api | memlog |
|---|---|---|
| Puncak RAM | 1.149 MB | **14 MB** |
| Proses latar | Ya (server + PostgreSQL) | Tidak (dipanggil saat perlu) |
| Dependensi | model ML, pgvector, PostgreSQL | **nol** (sqlite3 dari stdlib) |
| Waktu mulai | 60 detik | instan |
| Pencarian | semantik (embedding) | leksikal (FTS5 + BM25) |

Konsekuensi yang diterima: pencarian leksikal lemah pada parafrase jauh. Untuk catatan yang ditulis dengan istilah serupa, hasilnya setara. Ini dianggap memadai karena catatan proyek cenderung memakai istilah teknis yang konsisten.

## Perintah harian

```bash
cd ~/ANDREAS/zzluxora_v10

# simpan catatan
python3 scripts/memlog.py add --bank zzluxora --title "Judul singkat" \
    --tag desain --body "Isi catatan yang ingin diingat."

# cari (sintaks FTS5: AND, OR, NOT, "frasa", prefix*)
python3 scripts/memlog.py search "tombol netral"
python3 scripts/memlog.py search '"blok penuh"' --bank zzluxora

# lihat, daftar, sunting, hapus
python3 scripts/memlog.py show 12
python3 scripts/memlog.py list --bank zzluxora --limit 20
python3 scripts/memlog.py edit 12 --body "Isi baru"
python3 scripts/memlog.py delete 12

# pindahkan isi basis data
python3 scripts/memlog.py export /tmp/memlog.json
python3 scripts/memlog.py import /tmp/memlog.json
```

Basis data berada di `memory/memlog.db`.

## Mengarsipkan hindsight (kalau ingin memperbarui)

Skrip ini mengekspor seluruh bank hindsight, mengunduh arsipnya, lalu mengonversinya ke memlog. Perlu API hindsight hidup; kalau API mati, skrip memberi tahu cara menyalakannya.

```bash
# 1. nyalakan hindsight (butuh ~800 MB RAM, hentikan sesi lain dulu)
cd ~/ANDREAS/hindsight
set -a && . ./.env.local/hindsight.env && set +a
nohup ~/ANDREAS/.venv-hindsight/bin/hindsight-api > /tmp/hs.log 2>&1 &

# 2. tunggu sampai menjawab
until curl -sf -o /dev/null http://127.0.0.1:8888/health; do sleep 5; done

# 3. arsipkan + konversi
cd ~/ANDREAS/zzluxora_v10
python3 scripts/create_backup.py

# 4. opsional: hentikan hindsight untuk membebaskan RAM
pkill -f hindsight-api
```

Kalau arsip sudah ada dan hanya ingin mengonversi ulang:

```bash
python3 scripts/create_backup.py --skip-hindsight
```

Arsip asli tersimpan di `../memory-backup/<bank>-bank.zip`, jadi data tetap dapat dipulihkan ke hindsight nanti bila diperlukan.

## Pemulihan ke hindsight

Arsip `<bank>-bank.zip` adalah format transfer resmi hindsight. Untuk memulihkan:

```bash
curl -X POST "http://127.0.0.1:8888/v1/default/banks/<bank>/transfer/import" \
     -F "file=@../memory-backup/<bank>-bank.zip"
```

## Keterbatasan yang diketahui

- **Pencarian leksikal, bukan semantik.** Query yang memakai kata yang sama sekali berbeda dari catatan tidak akan cocok. Tambahkan tag saat menyimpan untuk memperlebar jalan masuk.
- **Tidak ada ekstraksi fakta otomatis.** Hindsight memecah catatan panjang menjadi fakta lewat LLM; memlog menyimpan apa adanya. Fakta hasil ekstraksi hindsight yang sudah ada tetap ikut terimpor dari arsip.
- **Tidak ada konsolidasi.** Tidak ada proses latar yang menggabungkan catatan serupa. Deduplikasi hanya saat impor, berdasarkan isi fakta.

## Berkas

| Berkas | Fungsi |
|---|---|
| `scripts/memlog.py` | alat memori: tambah, cari, lihat, sunting, hapus, ekspor, impor |
| `scripts/hindsight_to_memlog.py` | konverter arsip hindsight ke memlog |
| `scripts/create_backup.py` | arsipkan semua bank hindsight lalu konversi |
| `memory/memlog.db` | basis data catatan |
| `../memory-backup/*.zip` | arsip asli hindsight |

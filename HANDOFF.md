# HANDOFF.md - Briefing Agent Berikutnya

Dokumen ini untuk agent yang melanjutkan pekerjaan ZZLUXORA. Baca ini dulu sebelum menyentuh apa pun.

**Terakhir diperbarui:** 16 Oktober 2026
**Oleh:** sesi audit UI + migrasi memori

---

## 1. Status Sekarang

| | |
|---|---|
| Software `zzdree/zzluxora-v10` | HEAD **`d06469f`**, working tree **bersih**, sinkron `origin/main` |
| Naskah `zzdree/script` | HEAD **`0027d3d`** plus koreksi naskah belum di-commit, lihat §2b |
| Test suite | **151 lulus** (127 unittest + 24 pytest) |
| Anti-slop | **167 berkas, 0 error, 0 warning** |
| Audit | FASE 8 tuntas: 18 defect diperbaiki |

### Perintah wajib

```bash
cd ~/ANDREAS/zzluxora_v10

# uji (WAJIB pakai wrapper ini, bukan unittest langsung)
PYTHONPATH=$PWD/tools python3 tools/run_tests_guarded.py

# anti-slop
node scripts/check-anti-slop.js --summary

# memori
python3 scripts/memlog.py search "kata kunci"
```

**Kenapa wrapper?** Tanpa itu, pengujian memunculkan popup `QMessageBox` di layar operator (beberapa jalur yang diuji memang berakhir dengan dialog, mis. penyimpanan berkas). `tools/_autodialog_guard.py` menetralkannya lebih dulu.

---

## 2. Yang Sudah Selesai (jangan dikerjakan ulang)

**FASE 8 audit menyeluruh.** 18 defect diperbaiki, masing-masing direproduksi dulu lalu dikunci uji regresi. Yang paling penting:

- **Alat analisis sempat mengarang bukti.** Audio diam dan berkas 0-sampel dilaporkan `"C Major (Praise character)"` + `Q3_DEEP_WORSHIP`. Kini tonality digerbangi energi kroma → `"No tonal content"` + kuadran `Idle`. **Ini kritis untuk Bab 4 skripsi:** tanpa perbaikan ini, tabel bisa memuat klaim tonalitas palsu.
- **Alamat DMX rusak saat simpan** (rumus modulo-8): fixture di DMX 18 tertulis 17, 9 dari 15 posisi. Kini 0 dari 15.
- **Visualizer 3D:** lantai panggung, beam cone, dan floor pool **tidak terlihat sama sekali** pada pitch bawaan tepat 0 radian (poligon berluas nol). Kini pitch 15 derajat.
- **Tombol FLASH:** melepas tombol memadamkan panggung dan mengunci kanal warna.
- **BLACKOUT:** sempat mengirim frame basi ke rig; tidak memadamkan 256 fader kanal.
- **Fixture Editor:** menghapus label saat jumlah kanal diubah; save kehilangan `id`/`model`/`type`; widget bocor 24→264; tidak melacak perubahan belum disimpan.
- **Pintasan konsol mati saat jendela popup terbuka.**
- **Impor YouTube** rusak 3 lapis + sukses palsu via audio sintetis.

Rincian lengkap: `markdowns/ROADMAP.md` bagian **FASE 8**.

---

## 2b. Audit Adversarial 16 Okt 2026 (di luar FASE 8)

Audit 14 agen lintas kode, firmware, dan naskah. Setiap temuan diuji dua lensa
(refutasi + reproduksi) dan dinyatakan kukuh hanya bila keduanya gagal membantah.
**Tujuh defect diperbaiki**, suite 129 -> 151 test, semuanya lulus:

Komit `bc2846b` (lima defect pertama):

1. `save_project` memotong berkas tujuan lebih dulu lalu menulis bertahap, sehingga
   kegagalan di tengah menghancurkan showfile (1973 byte menjadi 51 byte rusak).
   Kini atomik (temp + fsync + `os.replace`); jalur GUI disamakan.
2. `.zlx` dimuat tanpa gerbang skema, sehingga berkas QLC+ atau `target_ip`
   `"not-an-ip"` diterima dan Art-Net dikirim ke alamat tak valid. Kini lewat
   `ProjectIO.validate_payload()`.
3. BLACKOUT tidak menghentikan crossfade; panggung menyala kembali 23 ms kemudian.
4. RESET DMX lalu PLAY mengirim look lama (fader nol, buffer masih terisi).
5. Worker QThread YouTubeDialog bocor dan bisa dimusnahkan saat masih berjalan.

Dua bug tambahan ditemukan saat memperbaiki di atas: `_refresh_dependency_line()`
dipanggil sebelum `btn_download` dibuat (dialog YouTube melempar `AttributeError`
setiap dibuka), dan `QDialog.reject()` mematikan proses di bawah plugin offscreen.

Komit `d06469f` (dua defect terakhir, keduanya menyentuh kebenaran hasil):

6. **`Mode_score` memakai cosine, bukan Pearson** (`core/emotion_model.py`). Kedua
   profil Krumhansl 0,9495 serupa di bawah cosine, sehingga skor terkurung di
   ±0,1782 padahal naskah menjanjikan skala ±1; bobot terbesar Valence (0,50)
   praktis lumpuh. Kini vektor dipusatkan sebelum dikorelasi (Pearson sejati):
   skor untuk profil Mayor persis naik dari +0,0373 ke +0,2124, batas atas dari
   0,1782 ke 0,6123, dan masukan rusak tidak lagi melempar `ValueError`.
7. **Kanal putih terbuang ke fixture tanpa emitor putih** (`ui/main_window.py`).
   Palet worship mellow `(67,38,0,178)` sampai ke Alien AL36 sebagai R+G+B = 105
   alih-alih 639, dan cue putih murni menjadi `(0,0,0)` alias padam total. W kini
   dilipat kembali ke R/G/B bila tak ada kanal yang dapat menerimanya.

### ⚠️ KEPUTUSAN PEMBIMBING YANG MASIH DIBUTUHKAN (Keputusan 9)

Perbaikan #6 **tidak cukup** untuk menepati klaim naskah. Setelah diukur, akar
masalahnya ternyata **normalisasi relatif per-lagu**, bukan bobot suku mode:

- Setiap lagu selalu memuat frame dengan `SC_norm = 1,0` (miliknya sendiri),
  sehingga rerata `SC_norm` pada sepuluh berkas uji adalah **0,66–0,84** dan skor
  centroid selalu positif. Kontribusi centroid + MFCC terukur **+0,214 sampai
  +0,352**.
- Akibatnya **`V` positif untuk SEMUA lagu**, termasuk tiga lagu bermodus minor.
- **Menaikkan bobot mode tidak menolong:** pada bobot 0,80 pun (diuji) tiga lagu
  minor tetap `V > 0`, sebab suku mode hanya mampu ±0,61.

Naskah sudah diberi catatan kejujuran di `script_math_model.md` Bagian [2] dan
[3.2], serta Bab 2, dan Keputusan 9 (beserta Keputusan 10) sudah ditambahkan ke
`script/markdowns/script_konsultasi_pembimbing.md`. **Yang belum diputuskan:**
apakah normalisasi tetap relatif per-lagu (aman, naskah dibatasi pada perubahan
relatif) atau diubah ke skala absolut (klaim antar-lagu benar-benar berlaku, tetapi
**seluruh angka warna Bab 4 harus diregenerasi**). Ini keputusan metodologi Pak
Mario, bukan keputusan implementasi.

### Status angka Bab 4 setelah perbaikan #6

Angka pada Tabel 4.5 dan RGBW frame pertama Tabel 4.4 sudah diselaraskan dengan
mesin Pearson (RMS/centroid rata-rata **tidak berubah**, hanya dua koefisien
bergeser berarti). Tabel 4.6 (`V`/`A` per lagu) **belum diisi** karena masih
menunggu pemilihan lagu final; nilainya akan ikut mesin Pearson saat diisi.

## 3. Yang BELUM Dikerjakan

### Butuh hardware (FASE 6)
- Uji lapangan ESP32 + 4 unit PAR LED Alien AL36 di GIA Deliksari (DMX 1/17/33/49).
- Ukur laju DMX fisik. Firmware sudah diperbaiki ke penjadwalan absolut `esp_timer` (`DMX_PERIOD_US=23220`), tetapi **belum ada pengukuran nyata** — sebelumnya `vTaskDelay(22)` relatif menghasilkan ~22 fps, bukan 44.
- Ukur latensi end-to-end dan packet loss. Rencana: `script/markdowns/script_fase6_execution.md`.
- Build installer Windows 11 di Acer Swift 3 (PyInstaller + Inno Setup).

### Naskah skripsi (repo `script`)
- Bab 4 dan 5 masih kerangka: **71 + 9 penanda `[BELUM*]`**.
- **8 `[PERLU PERSETUJUAN DOSEN PEMBIMBING]`** sebagai action item untuk Pak Mario. Sudah dirangkum di `script/markdowns/script_konsultasi_pembimbing.md`.
- 🔥 **Keputusan belum diambil:** 10 WAV di `data/audio/` **sintetis** (dibuat `tools/generate_benchmark_audio.py`, seragam 12,00 detik) tetapi dinamai band nyata. Bab 4 §4.1.2 mewajibkan lagu asli untuk penilaian persepsi. Blok transparansi sudah ada, tetapi pilihan metodologisnya belum.
- Olah data lapangan: `tools/analyze_field_data.py` (CSV 41 kolom → tabel Bab 4).
- Bridge korelasi fitur audio: `tools/export_correlation.py`.

### Sisa temuan low (belum ditindak)
Tidak ada yang mendesak. Beberapa `except Exception: pass` yang sengaja (probe opsional, tutup socket) versus satu yang bermasalah (`audio_loader.py:109` menelan kegagalan decode lalu pindah format diam-diam).

---

## 4. Jebakan yang Harus Diketahui

### Qt: QLabel mewarisi background global
`CONSOLE_QSS` memuat `QWidget { background-color: ... }` yang **diwarisi setiap QLabel**. Setiap QLabel di atas widget berwarna WAJIB diberi `background: transparent`, kalau tidak ia menggambar persegi gelap yang menutupi warna induknya. Inilah yang membuat sel grid DMX tampak outline selama ini, bukan blok penuh.

### Preferensi desain owner
- **Tombol aksi WAJIB netral** abu-abu. Warna hanya untuk MAKNA, bukan hiasan. Doktrin `DESIGN.md` 10% Accent Rule: hijau = transmisi/simpan/aksi utama, merah = blackout/clear destruktif, amber = master dimmer/tab aktif, cyan = rail fader/telemetri. Tersisa 4 tombol berwarna, semuanya berdoktrin.
- **Elemen berwarna harus BLOK PENUH**, bukan outline.
- UI konsol sengaja "jadul" demi stabilitas. Kata owner: *"software profesional harusnya clean ui nya, biasanya malah kayak ui jadul sih, soalnya kan ngejar stabilitas"*.

### Ukur dulu, jangan menebak
Dua dugaan awal soal bug sel DMX **terbukti salah** saat diukur (QSS lokal ternyata bekerja; rule global ternyata tidak menimpa). Yang menemukan akar masalah adalah sampel piksel langsung. Teknik yang bekerja: `w.grab().save()` lalu baca piksel; hitung kontras dari token; hitung sebaran hue; click-through semua elemen.

### RAM hanya 3,6 GB
Jangan jalankan hal berat bersamaan. Lihat bagian memori di bawah.

---

## 5. Memori

### Lokasi catatan
- **Memori Claude** (otomatis): `~/.claude/projects/-home-zzdree-ANDREAS/memory/` — 22 berkas, indeks di `MEMORY.md`.
- **Memlog** (SQLite, **pengganti hindsight**): `~/ANDREAS/zzluxora_v10/memory/memlog.db` — 118 catatan (66 zzluxora, 42 gia, 9 script, 1 percobaan).

```bash
cd ~/ANDREAS/zzluxora_v10
python3 scripts/memlog.py search "kata kunci"
python3 scripts/memlog.py add --bank zzluxora --title "..." --tag ... --body "..."
python3 scripts/memlog.py list --limit 20
```

### Kenapa bukan hindsight lagi
`hindsight-api` memuat dua model ML lokal sehingga memuncak **1.149 MB RAM** dan berulang kali di-OOM di laptop ini. Pengganti `memlog` memakai SQLite FTS5: **14 MB**, nol dependensi, mulai instan.

Tidak bisa diringankan: 9router punya 40 model tetapi **0 embedding**, dan reranker tidak punya opsi mati.

Data lama **sudah diarsipkan** ke `~/ANDREAS/memory-backup/*.zip` (18 dokumen + 99 fakta dari 3 bank) dan dikonversi ke memlog. Panduan lengkap: `markdowns/MEMORY.md`.

Kalau perlu memperbarui arsip hindsight, API harus hidup (~800 MB RAM, hentikan sesi lain dulu):
```bash
cd ~/ANDREAS/hindsight && set -a && . ./.env.local/hindsight.env && set +a
nohup ~/ANDREAS/.venv-hindsight/bin/hindsight-api > /tmp/hs.log 2>&1 &
until curl -sf -o /dev/null http://127.0.0.1:8888/health; do sleep 5; done
cd ~/ANDREAS/zzluxora_v10 && python3 scripts/create_backup.py
```

### Pelajaran dari sesi lalu
Skrip probe pernah memunculkan popup `QMessageBox` berulang di layar owner yang sedang bekerja, padahal ia tidak menjalankan aplikasi. Itu mengganggu dan membingungkan. **Selalu pakai wrapper berpengaman**; kalau menulis skrip probe sendiri, impor `_autodialog_guard` sebagai baris pertama dengan `PYTHONPATH=<repo>/tools`.

---

## 6. Berkas Penting

| Berkas | Isi |
|---|---|
| `CLAUDE.md` | aturan proyek, design system, status uji |
| `DESIGN.md` + `PRODUCT.md` | doktrin desain (Impeccable, "The Obsidian Control Deck") |
| `markdowns/ROADMAP.md` | FASE 1-8, rincian 18 defect audit |
| `markdowns/TEST_PLAN.md` | matriks uji, Level 1-5, suite UT-01..UT-12 |
| `markdowns/MEMORY.md` | cara pakai memlog, arsip, pemulihan |
| `tools/run_tests_guarded.py` | perintah uji resmi |
| `tools/_autodialog_guard.py` | penetral dialog |
| `scripts/check-anti-slop.js` | pemindai mutu |
| `scripts/memlog.py` | memori agen |
| `../script/markdowns/script_plans.md` | status naskah skripsi |
| `../script/markdowns/script_konsultasi_pembimbing.md` | agenda konsultasi dospem |

---

## 7. Langkah Pertama yang Disarankan

1. Baca dokumen ini, lalu `markdowns/ROADMAP.md` bagian FASE 8 dan `markdowns/MEMORY.md`.
2. Verifikasi keadaan: `PYTHONPATH=$PWD/tools python3 tools/run_tests_guarded.py` (harus 151 lulus).
3. Cari konteks relevan: `python3 scripts/memlog.py search "<topik>"`.
4. Tanya owner mau lanjut ke mana. Pilihan yang tersedia: **(a)** kerjakan naskah Bab 4/5 dan keputusan audio, **(b)** siapkan FASE 6 saat hardware tersedia, **(c)** test manual aplikasi lalu perbaiki temuan yang muncul.

**Jangan** memulai dengan mengaudit ulang area yang sudah tuntas di FASE 8. Semua defect di sana sudah direproduksi dan dikunci uji regresi.

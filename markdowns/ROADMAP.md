# 🗺️ ROADMAP.md — Big Plan v3 Execution Roadmap (ZZLUXORA v10)

**Peta Jalan Rekayasa Perangkat Lunak & Tahapan Implementasi Terstruktur**  
*Basis: Feedback v3 & Standar Konsol grandMA2 / grandMA3 onPC / QLC+*

---

## 📌 Rencana Induk Rekayasa (Big Plan v3 Phases)

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      PETA JALAN PENGEMBANGAN v10                       │
├────────────────────────────────────────────────────────────────────────┤
│  FASE 1: Identitas Visual, Logo Arial Black Italic, & Asset [SELESAI] │
│  FASE 2: Rombak Shell (Native QMenuBar, Program Bar)       [SELESAI]  │
│  FASE 3: Jendela Pop-up Non-Modal Independen              [SELESAI]   │
│  FASE 4: Restrukturisasi 6 Tab Workspaces & Clean State    [SELESAI]  │
│  FASE 5: Pengujian Software-in-the-Loop (SITL QLC+)        [TERUJI]   │
│  FASE 6: Pengujian Lapangan (ESP32 + PAR LED) & Packaging  [SIAP]     │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 🚀 FASE 1: Identitas Visual & Asset Deployment (STATUS: TUNTAS 100%)
- [x] **Logo Resmi Anti-Slop:** Huruf kapital "ZZ" (Arial Black Italic, solid black #000000, pure white #ffffff, no glow, rasio 1:1 di `ui/assets/logo_zz.png`).
- [x] **Asset Multi-Format:** Mengonversi asset ke multi-size icon (`.ico` 16x16 s.d. 256x256) untuk integrasi OS window title bar dan taskbar.
- [x] **Aplikasi Identitas:** Mengikat logo resmi ke `setWindowIcon()` dan `setWindowTitle("ZZLUXORA [Untitled.zlx]")`.

---

### 🎛️ FASE 2: Rombak Total Shell & Header (STATUS: TUNTAS 100%)
- [x] **Eliminasi Sidebar Total:** Menghapus navigasi vertikal samping (`sidebar.py`) guna membebaskan area kerja horizontal.
- [x] **Header Desktop Bersih:**
  * **OS Window Title Bar:** Memuat logo resmi `ZZ` + Judul format bersih `ZZLUXORA [NamaFile.zlx]`.
  * **Menu Bar (Native QMenuBar):** Pure native menu bar (`[File]` `[Fixture]` `[Editor]` `[Preview]` `[Setting]` `[Help]` `[About]`).
  * **Program View Bar:** 6 tab workspace di kiri, status Art-Net + tombol Blackout + tombol Play/Stop toggle di kanan.
- [x] **Transmisi Play-Gated:** Paket DMX hanya dikirimkan ketika tombol PLAY aktif.
- [x] **Pemberian Shortcut Global:**
  * `Ctrl+O`: Open Project
  * `Ctrl+S`: Save Project
  * `Ctrl+Shift+S`: Save As Project
  * `Space`: Play/Stop Toggle Art-Net
  * `Escape` / `B`: Blackout
  * `Ctrl+Z` / `Ctrl+Shift+Z`: Global Undo / Redo

---

### 🪟 FASE 3: Implementasi Jendela Pop-up Mandiri (STATUS: TUNTAS 100%)
- [x] **Fixture List Window:**
  * Jendela independen non-modal dengan tombol *Minimize, Maximize, Close*.
  * Memuat pustaka fixture `.zfx` / JSON.
  * Mendukung aksi **Drag and Drop** langsung ke sel grid Tab Address.
- [x] **Fixture Definition Editor Window:**
  * Jendela editor profil lampu terisolasi berstandar QLC+ Fixture Editor.
  * Menubar mandiri: File -> Open, Save, Save As (`.zfx` / `.json`).
  * Profil Fixture Sample 8-CH (`fixtures/generic_par_rgbw_8ch.json` dan `.zfx`).
- [x] **Stage Visualizer Window:**
  * Jendela visualizer panggung non-modal (dapat dipindah ke second monitor FOH).
  * Tab 2D: Tampak depan panggung dengan pendaran cahaya lingkaran RGBW dinamis.
- [x] **Network Setting Dialog:**
  * Pemindaian otomatis adapter jaringan lokal.
  * Preset wajib: `127.0.0.1` (SITL QLC+), `192.168.4.1` (ESP32 AP), Custom IP, Universe 0.
- [x] **Help & About Windows:**
  * Help: Panduan penggunaan & tabel shortcut keyboard lengkap.
  * About: Keterangan resmi skripsi (Andreas, NIM 5312422036, Dospem Mario Norman Syah, S.Pd., M.Eng., UNNES).

---

### 📑 FASE 4: Restrukturisasi 6 Tab Workspaces (STATUS: TUNTAS 100%)
- [x] **Clean Initial State:** Seluruh tab dimulai dalam kondisi 100% kosong tanpa demo otomatis yang membingungkan operator.
- [x] **Berkas Demo Khusus:** `fixtures/demo_church_worship.zlx` disediakan untuk memuat demo kapan saja via `File -> Open Project...`.
- [x] **Tab 1 — Address:**
  * Matriks 256 kanal DMX (maksimal 24 kolom horizontal, sel compact 46x46px).
  * Tag fungsi teknis (`DIM`, `RED`, `GRN`, `BLU`, `WHT`, `STR`).
  * Tombol [CLEAR PATCH], [AUTO PATCH (4 PAR)], [UNDO], [REDO].
- [x] **Tab 2 — Analyze (Core Skripsi):**
  * Pemuat audio multi-format (`.wav`, `.mp3`, `.flac`, `.ogg`).
  * Input tautan YouTube via dialog pop-up mandiri (`YouTubeDialog`).
  * Analisis asinkron berbasis `QThread`: area analisis diburamkan tanpa freeze.
  * Progress bar saintifik dengan teks penjelasan proses DSP real-time.
- [x] **Tab 3 — Result:**
  * Dashboard metrik audio lagu rohani.
  * Visualisasi koordinat afektif Russell 2D Plane ($V, A$), BPM, akord Chroma, kuadran mood.
  * Tombol [RE-ANALYZE] dan [EXPORT TO PERFORM].
- [x] **Tab 4 — Perform:**
  * Manajemen playlist urutan lagu pertunjukan live ([MOVE UP], [MOVE DOWN], [DELETE]).
  * Pengaturan section cues dan transisi fade.
  * Tombol [GENERATE EXECUTORS] mengonversi playlist ke Tab Page secara otomatis.
- [x] **Tab 5 — Page:**
  * Halaman tombol eksekutor virtual interaktif bergaya grandMA & QLC+ (dimulai bersih).
  * Tombol cue (Praise, Worship, Verse, Chorus) dan Flash Strobe.
- [x] **Tab 6 — Mixer:**
  * Meja fader virtual 257 fader: 1 Grand Master Dimmer + 256 Kanal DMX.
  * Fader taktil grandMA (tinggi 190px, lebar 52px, cap bertakik 30x18, rel ber-LED menyala, garis skala analog).
  * Tombol [RESET DMX], [FULL MASTER], [REFRESH].

---

### 🔄 FASE 5: Verifikasi Software-in-the-Loop (STATUS: TERUJI)
- [x] Pengujian streaming paket DMX 43 FPS dari ZZLUXORA v10 ke QLC+ via Art-Net `127.0.0.1:6454` Universe 0.
- [x] Verifikasi Play-gated packet transmission: transmisi hanya terjadi saat tombol PLAY menyala.
- [x] Pengujian Blackout seketika memadamkan seluruh output DMX ke 0.
- [x] 14 dari 14 unit test di `tests/` lulus 100%.

---

### ⚡ FASE 6: Pengujian Lapangan Hardware & Deployment (SIAP DIJALANKAN)
- [ ] Uji coba koneksi Wi-Fi ke SoftAP ESP32 (`192.168.4.1`) di laptop ASUS X407MA.
- [ ] Uji coba pengontrolan fisik 4 unit PAR LED RGBW via kabel DMX512 XLR 3-pin di Gereja GIA Deliksari.
- [ ] Build installer executable Windows 11 (`.exe` via Inno Setup) di laptop Acer Swift 3.
- [ ] Sinkronisasi penuh ke repositori GitHub `zzdree/zzluxora-v10` sebagai Single Source of Truth.

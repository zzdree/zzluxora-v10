# 📋 PRD.md — ZZLUXORA v10 Product Requirements Document

**Dokumen Kebutuhan Produk: Sistem Pengendali Pencahayaan Panggung Cerdas Berbasis Analisis Audio**  
*Versi Produk: v10.0.0 (Flagship Next-Gen) | Target Rilis: September 2026*  
*Peneliti: Andreas Restuawanta Christwara (NIM: 5312422036) | Pembimbing: Mario Norman Syah, S.Pd., M.Eng.*

---

## 📌 1. Ringkasan Eksekutif (Executive Summary)

**ZZLUXORA v10** adalah perangkat lunak konsol tata cahaya panggung (*stage lighting console*) berstandar industri yang mengintegrasikan pemrosesan sinyal audio digital (*Digital Signal Processing* / DSP) berbasis **Short-Time Fourier Transform (STFT)**, ekstraksi fitur akustik (*Music Information Retrieval* / MIR), dan **Model Afektif Russell 2D Plane (Valence-Arousal)** untuk mengotomatiskan perancangan pencahayaan panggung lagu rohani secara dinamis dan ekspresif.

Aplikasi mentransmisikan data pencahayaan menggunakan protokol standar internasional **Art-Net 4 DMX512** melalui jaringan UDP port 6454 menuju node mikrokontroler **ESP32** di panggung fisik atau menuju simulator **QLC+** dalam pengujian *Software-in-the-Loop* (SITL).

---

## 🎯 2. Konteks Pengguna & Lingkungan Operasional

- **Pengguna Utama:** Operator tata cahaya panggung (*lighting engineer* / operator FOH) dan tim multimedia gereja di Gereja GIA Deliksari Semarang.
- **Karakteristik Pengoperasian:**
  * Lingkungan pencahayaan redup/gelap (*Front of House*).
  * Kebutuhan respon cepat dan keandalan tinggi (tidak boleh freeze/crash saat pertunjukan berlangsung).
  * Transisi instan antara lagu riang/sukacita (*praise*) dan lagu khidmat/penyembahan (*worship*).
- **Perangkat Keras Target:**
  * Laptop Pengembang: ASUS VivoBook X407MA (Linux Mint 64-bit, resolusi 1366×768).
  * Laptop Panggung / Server: Acer Swift 3 (Windows 11 64-bit, resolusi 1920×1080).
  * Hardware Node: ESP32 DevKit V1 + Modul MAX485 + LCD 16x2 + Lampu PAR LED RGBW.

---

## ⚙️ 3. Kebutuhan Fungsional (Functional Requirements)

### 3.1. Peluncuran & Header Navigation
- **FR-01 (Instant Cold Launch & Clean Blank State):**
  Aplikasi wajib terbuka secara instan tanpa splash screen (*zero splashscreen*), waktu pemuatan awal < 500 ms. Kondisi awal 100% kosong (tanpa demo otomatis yang membingungkan operator). File demo mandiri disediakan di `fixtures/demo_church_worship.zlx`.
- **FR-02 (Desktop Header Standard — No In-Window Title Frame):**
  * OS Window Title Bar: Memuat logo resmi `ZZ` (Arial Black Italic, solid black #000000, pure white #ffffff, no glow) dan judul format bersih: `ZZLUXORA [NamaProject.zlx]`.
  * Baris 1: Pure Native `QMenuBar` (`File`, `Fixture`, `Editor`, `Preview`, `Setting`, `Help`, `About`) tanpa duplikasi logo/nama.
  * Baris 2: Program View Bar (Sisi kiri memuat 6 tab workspace, sisi kanan memuat badge status Art-Net, tombol Blackout, dan tombol Play/Stop toggle).
- **FR-03 (Art-Net Status Badge & Play-Gated Transmission):**
  * Status badge: Hijau (*Connected/Transmitting*) saat streaming paket DMX aktif, Merah (*Disconnected/Idle*) saat berhenti. Klik pada status badge langsung membuka dialog pengaturan jaringan (*Setting*).
  * **Play-Gated Rule:** Paket UDP Art-Net **HANYA DIKIRIMKAN ketika tombol PLAY aktif** (`is_transmitting == True`). Ketika Play belum ditekan, pergerakan fader hanya memperbarui GUI internal tanpa memancarkan paket ke jaringan.
- **FR-04 (Master Blackout):**
  Menekan tombol Blackout menurunkan nilai Grand Master Fader seketika menjadi 0, memadamkan seluruh output lampu (jika Play aktif, memancarkan paket nol instan).

### 3.2. Manajemen Berkas & Jendela Eksternal
- **FR-05 (Manajemen Project .zlx):**
  * Format berkas `.zlx` (JSON terstruktur terkompresi).
  * Menu File memfasilitasi `Open Project... (Ctrl+O)`, `Save Project (Ctrl+S)`, `Save As Project... (Ctrl+Shift+S)`, dan `Exit`.
  * Memuat berkas demo resmi `fixtures/demo_church_worship.zlx` secara otomatis merestorasi seluruh patch, playlist, cues, dan faders.
- **FR-06 (Fixture List Floating Window):**
  * Membuka jendela pop-up independen non-modal (bisa di-resize, minimize, maximize, close).
  * Menampilkan pustaka lampu yang tersimpan di `fixtures/`.
  * Mendukung aksi **Drag and Drop** langsung dari daftar ke kotak pada Tab Address.
- **FR-07 (Fixture Definition Editor Floating Window):**
  * Jendela pop-up berstandar QLC+ Fixture Definition Editor dengan menubar mandiri (*Open, Save, Save As*).
  * Format profil lampu: `.zfx` (JSON).
  * Profil Fixture Sample Resmi 8-CH (`fixtures/generic_par_rgbw_8ch.json` dan `.zfx`):
    Ch 1 Dimmer, Ch 2 Red, Ch 3 Green, Ch 4 Blue, Ch 5 White, Ch 6 Strobe, Ch 7 Program, Ch 8 Speed.
- **FR-08 (Detachable Multi-Screen Stage Visualizer):**
  * Jendela visualizer non-modal dapat dipindahkan ke monitor sekunder / FOH.
  * Menyediakan Visualizer 2D (Tampak Depan Panggung dengan pendaran PAR LED dinamis).
- **FR-09 (Network & Art-Net Configuration):**
  * Jendela pengaturan jaringan non-modal dengan pemindaian IP otomatis.
  * Preset wajib: `127.0.0.1` (Localhost SITL QLC+), `192.168.4.1` (ESP32 SoftAP), dan `Custom IP`.
  * Konfigurasi Universe 0 (Art-Net SubUni 0x00) dan sinkronisasi laju transmisi 43.07 FPS (~23 ms).
- **FR-10 (Help & About Dialogs):**
  * Help: Panduan operasional dan daftar lengkap tabel keyboard shortcuts (non-modal).
  * About: Informasi akademik lengkap (Nama, NIM: 5312422036, Prodi, Jurusan, Fakultas, UNNES, Dospem: Mario Norman Syah, S.Pd., M.Eng., Judul Skripsi).

### 3.3. Enam Tab Utama Program (Workspaces)
- **FR-11 (Tab 1 — Address):**
  * Grid matriks 256 kanal DMX (maksimal 24 kolom horizontal per baris, scroll vertikal, sel 46×46px).
  * Kotak kosong: abu-abu gelap dengan nomor kanal di sudut kanan atas.
  * Kotak terisi: warna latar sesuai jenis fungsi kanal (Merah, Hijau, Biru, Putih, Amber Dimmer, Kuning Strobe), label fungsi teknis (`DIM`, `RED`, `GRN`, `BLU`, `WHT`, `STR`) di tengah kotak, nomor kanal tetap di kanan atas.
  * Tombol [CLEAR PATCH] dengan dialog konfirmasi keamanan.
  * Fitur Riwayat: Undo (`Ctrl+Z`) dan Redo (`Ctrl+Shift+Z` / `Ctrl+Y`).
- **FR-12 (Tab 2 — Analyze - Core Engine Skripsi):**
  * Pemuat berkas audio lokal (`.mp3`, `.wav`, `.flac`, `.ogg`).
  * Input tautan YouTube dengan pengunduh dan pengonversi audio otomatis via pop-up dialog khusus (`YouTubeDialog`).
  * Tombol [ANALYZE] dan [REMOVE SONG] (dinonaktifkan jika belum ada audio yang dimuat).
  * Proses analisis asinkron non-blocking (`QThread`): area analisis diberi efek visual blur/dimmed tanpa mengunci antarmuka.
  * Menampilkan progress bar dan teks penjelasan saintifik tahapan DSP yang sedang berlangsung secara real-time.
- **FR-13 (Tab 3 — Result):**
  * Menampilkan daftar lagu hasil analisis dengan urutan terstruktur.
  * Menampilkan koordinat afektif Russell 2D ($V, A$), BPM, estimasi akord Chroma, kuadran mood (Praise vs Worship), dan palet warna HSV-RGBW.
  * Tombol [RE-ANALYZE] dan tombol [EXPORT TO PERFORM].
- **FR-14 (Tab 4 — Perform):**
  * Manajemen urutan playlist lagu pertunjukan live (tombol [MOVE UP], [MOVE DOWN], [DELETE]).
  * Pemetaan cue pencahayaan otomatis berbasis struktur lagu (Intro, Verse, Chorus, Bridge, Outro).
  * Pengaturan durasi transisi (*fade time*) dan kecepatan *chase*.
  * Tombol [GENERATE EXECUTORS] mengonversi playlist menjadi tombol eksekutor otomatis di Tab Page.
- **FR-15 (Tab 5 — Page):**
  * Halaman tombol eksekutor virtual interaktif (ala grandMA2/grandMA3 & Virtual Console QLC+).
  * Dimulai bersih 100% kosong (tanpa demo otomatis). Tombol digenerate via Perform Tab atau load demo project.
  * Tombol trigger instan untuk suasana Praise, Worship, Verse, Chorus, dan Flash Strobe.
- **FR-16 (Tab 6 — Mixer):**
  * Meja fader virtual 257 fader fisik: 1 Grand Master Dimmer (paling kiri) + 256 Kanal DMX (1 s.d. 256).
  * Desain fader bergaya grandMA: *tactile ribbed cap* (lebar 30px, tinggi 18px, compact 190px fader height untuk kenyamanan 768p dan 1080p), *illuminated groove rail* (LED menyala di belakang cap), dan skala garis kalibrasi analog.
  * Nilai fader 0–255 dengan slider vertikal dan scrollbar horizontal halus.
  * Tombol: [RESET DMX], [FULL MASTER], [REFRESH].

---

## 🚀 4. Kebutuhan Non-Fungsional (Non-Functional Requirements)

1. **Latensi & Kecepatan:**
   * Latensi pemrosesan audio-ke-DMX < 25 milidetik.
   * Laju transmisi paket UDP Art-Net stabil pada $43.07\text{ FPS}$ (interval $\approx 23.22\text{ ms}$).
2. **Keandalan & Thread Safety:**
   * Proses analisis audio STFT dan pengunduhan YouTube wajib berjalan di thread terpisah (`QThread` / Worker) agar GUI tidak pernah mengalami kondisi *Not Responding* (ANR).
3. **Kompatibilitas Lintas Sistem Operasi:**
   * 100% berjalan identik di Linux Mint 21+ dan Windows 10/11 64-bit tanpa modifikasi kode sumber melalui `ui/qt_compat.py`.
4. **Kepatuhan Protokol DMX:**
   * Konstruksi paket biner Art-Net 4 mematuhi spesifikasi ArtDmx 530 byte:
     `"Art-Net\0"` (8B) + OpCode `0x5000` (2B, LE) + ProtVer `14` (2B, BE) + Sequence (1B) + Physical (1B) + SubNet/Net/Universe (2B) + Length `512` (2B, BE) + Data DMX (512B).

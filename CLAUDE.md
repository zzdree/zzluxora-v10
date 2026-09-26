# 🎛️ CLAUDE.md — ZZLUXORA v10 (Next-Gen Production Stage Lighting Console)

Panduan arsitektur, instruksi pengembangan, dan konteks operasional untuk **ZZLUXORA v10.0.0** (GrandMA Industrial Console Architecture — Anti-Slop Professional Edition).

---

## 📌 1. Ikhtisar & Identitas Proyek

- **Nama Aplikasi:** **ZZLUXORA** (v10.0.0 Flagship Next-Gen)
- **Repositori:** `https://github.com/zzdree/zzluxora-v10.git` (Branch: `main`)
- **Peneliti / Pengembang:** Andreas Restuawanta Christwara (`NIM: 5312422036`)
- **Dosen Pembimbing:** Mario Norman Syah, S.Pd., M.Eng. (`NIP: 199304212024061001`)
- **Institusi:** Program Studi S1 Teknik Komputer, Fakultas Teknik, Universitas Negeri Semarang (UNNES)
- **Karakter Desain:** Modern-minimalis industri panggung pertunjukan (mengadopsi estetika **grandMA2 / grandMA3 onPC** dan utilitas **QLC+**).
- **Format Showfile Project:** `.zlx` (JSON showfile).
- **Format Fixture Profile:** `.zfx` (JSON profil fixture).
- **Format Profil Fixture:** `.zfx` (JSON profil lampu berstandar QLC+).

---

## 🏗️ 2. Arsitektur Perangkat Lunak (Clean Modular Architecture — Feedback v3)

Aplikasi dibangun menggunakan **Python 3.10+** dan **Universal Qt6 Compatibility Layer (`ui/qt_compat.py`)** yang mendukung **PySide6** maupun **PyQt6** secara transparan:

```text
zzluxora_v10/
├── core/                      # PURE PYTHON ENGINE (ZERO-GUI DEPENDENCY)
│   ├── __init__.py
│   ├── audio_loader.py        # Pemuat audio multi-format (.wav, .mp3, .flac, .ogg)
│   ├── fft_engine.py          # Implementasi STFT (Hann Window, N=2048, H=512, fs=22050, 43.07 FPS)
│   ├── feature_extractor.py   # Ekstraksi RMS, Spectral Centroid, Chroma 12-semitone, MFCC, Flux
│   ├── emotion_model.py       # Model Afektif Russell 2D Plane (Valence-Arousal)
│   ├── color_engine.py        # Konversi (V, A, RMS) -> HSV -> RGB -> Physical 4-Kanal RGBW
│   ├── artnet_sender.py       # Transmisi UDP socket Port 6454 ke Node DMX (530-byte ArtDmx, Universe 0)
│   ├── models.py              # Data structures: Fixture, Patch, Scene, Chase, ProjectState
│   └── project_io.py          # Serialisasi & Deserialisasi berkas .zlx & .zfx
│
├── ui/                        # USER INTERFACE (PYSIDE6 / PYQT6 DUAL-BINDING COMPATIBLE)
│   ├── __init__.py
│   ├── qt_compat.py           # Universal Qt6 binding compatibility layer with automatic enum promotion
│   ├── styles.py              # Pure Dark Grey (#1e2024 - #282c34), high-contrast white text, master QSS
│   ├── icons.py               # Vektor SVG icons & custom painter helpers
│   ├── assets/                # Asset resmi logo & icon (logo_zz.png 1024x1024, logo_zz.ico multi-size)
│   ├── main_window.py         # Root window, pure native QMenuBar, program view bar, telemetry, blackout
│   ├── panels/
│   │   ├── address_tab.py     # Grid DMX Address 256 kanal (maks 24 kolom horizontal, color-coded, 46x46)
│   │   ├── analyze_tab.py     # Core skripsi audio analyzer, YouTube downloader, non-blocking DSP
│   │   ├── result_tab.py      # Metrik afektif Russell 2D, kuadran mood, export to perform
│   │   ├── perform_tab.py     # Live show controller, playlist reordering, cue transitions
│   │   ├── page_tab.py        # Virtual executor sheet (clean blank start, flash triggers)
│   │   ├── mixer_tab.py       # 257 Slider fader (1 Grand Master + 256 DMX) grandMA style (190px compact)
│   │   ├── fixture_list.py    # Floating window: Drawer fixture & drag-and-drop patching
│   │   ├── fixture_editor.py  # Floating window: QLC+ style fixture definition editor (.zfx)
│   │   ├── preview_tab.py     # Floating window: Visualizer panggung 2D multi-screen support
│   │   ├── settings_panel.py  # Floating window: Konfigurasi IP Art-Net (127.0.0.1, 192.168.4.1, Custom)
│   │   ├── help_panel.py      # Floating window: Panduan penggunaan & tabel keyboard shortcuts
│   │   └── about_panel.py     # Floating window: Lembar informasi akademis & identitas pengembang
│   └── widgets/
│       ├── tactile_fader.py   # Custom grandMA fader widget (rel LED menyala, cap bertakik, garis kalibrasi)
│       └── youtube_dialog.py  # Pop-up mandiri pengunduh audio YouTube ke data/audio/ lokal
│
├── markdowns/                 # 7 DOKUMEN REKAYASA SISTEMATIS LENGKAP
│   ├── DESIGN.md              # Spesifikasi sistem desain grandMA, token, responsivitas 768p/1080p
│   ├── PRD.md                 # Product Requirements Document & spesifikasi fungsional
│   ├── ARCHITECTURE.md        # Arsitektur sistem, threading model, & skema data
│   ├── COMPONENT_SPEC.md      # Spesifikasi detail setiap komponen antarmuka
│   ├── STATE_MANAGEMENT.md    # Global QUndoStack, DMX buffer, & Art-Net state machine
│   ├── TEST_PLAN.md           # Rencana pengujian berjenjang (Unit, SITL, Lapangan)
│   └── ROADMAP.md             # Rencana aksi eksekusi Big Plan v3 bertahap
│
├── fixtures/                  # Preset profil lampu & berkas demo
│   ├── demo_church_worship.zlx # Berkas proyek demo resmi (bisa dibuka via File -> Open Project...)
│   ├── generic_par_rgbw_8ch.zfx # Profil fixture 8-CH (Dimmer, Red, Green, Blue, White, Strobe, Program, Speed)
│   ├── generic_par_rgbw_8ch.zfx
│   ├── generic_par_rgbw_4ch.json
│   └── qlcplus_template.qxw   # Template SITL loopback QLC+
│
├── tests/                     # Unit testing & verification (14 tests pass 100%)
│   ├── test_core_engine.py
│   └── test_ui_components.py
├── requirements.txt           # Dependensi pustaka Python
├── README.md                  # Dokumentasi proyek
└── main.py                    # Entry point aplikasi (Instant launch, clean blank start)
```

---

## 🎨 3. Spesifikasi UI/UX & Standar Mutu (Feedback v3 Full Alignment)

1. **Peluncuran Instan (Zero Splashscreen) & Clean Initial State:**
   - Aplikasi terbuka seketika (*instant cold launch* < 500 ms) menyerupai QLC+, tanpa jeda splash screen.
   - Tampilan awal 100% kosong (*clean blank state* tanpa demo otomatis). Berkas demo mandiri disediakan di `fixtures/demo_church_worship.zlx`.
2. **Transmisi Art-Net Play-Gated:**
   - Paket UDP Art-Net Port 6454 **HANYA DIKIRIMKAN ketika tombol PLAY aktif** (`is_transmitting == True`). Ketika Play belum ditekan, pergerakan fader hanya memperbarui GUI internal tanpa memancarkan paket ke jaringan.
3. **Hierarki Header Desktop Standar:**
   - **OS Window Title Bar:** Memuat logo resmi `ZZ` (Arial Black Italic, solid black, pure white, no glow) dan judul format bersih: `ZZLUXORA [NamaProject.zlx]`.
   - **Main Menu Bar (Native QMenuBar):** Pure menu bar (`File`, `Fixture`, `Editor`, `Preview`, `Setting`, `Help`, `About`) tanpa duplikasi logo/nama app di dalamnya.
   - **Program View Bar:** Sisi kiri memuat 6 tab workspace, sisi kanan memuat badge status Art-Net (klik membuka Setting), tombol Blackout, dan tombol Play/Stop toggle.
4. **Desain Anti-Slop (No Emojis & Industrial Console Look):**
   - Bebas dari emoji di tombol/header.
   - Menggunakan pemisah teknis standar konsol: pipa `|` atau titik dua `:`, tanpa em-dash dekoratif `—`.
   - Kode channel visual di Tab Address: `DIM`, `RED`, `GRN`, `BLU`, `WHT`, `STR`.
5. **Jendela Pop-up Mandiri (Floating Windows):**
   - `Fixture List`, `Fixture Editor`, `Stage Visualizer`, `Settings`, `Help`, `About` adalah jendela pop-up non-modal independen dengan kontrol *Minimize, Maximize, Close*.
6. **Enam Tab Utama Program (Workspaces):**
   - `Tab 1: Address`: Grid 256 kanal DMX (maksimal 24 kolom horizontal, warna sel mengikuti tipe kanal, Clear All dengan konfirmasi, Undo `Ctrl+Z` / Redo `Ctrl+Shift+Z`).
   - `Tab 2: Analyze`: Audio file loader, YouTube audio downloader & converter otomatis, tombol Analyze & Remove, analisis asinkron non-blocking dengan efek blur/dimmed pada area analisis dan tips saintifik DSP.
   - `Tab 3: Result`: Dashboard metrik analisis (Russell 2D plane V-A, BPM, Chroma, kuadran mood Praise/Worship), tombol Re-Analyze, dan Export to Perform.
   - `Tab 4: Perform`: Manajemen urutan playlist pertunjukan panggung, pembuatan cue struktur lagu (Intro/Verse/Chorus/Bridge), waktu fade, chase rate, dan shortcut panggung.
   - `Tab 5: Page`: Lembar tombol virtual executor untuk eksekusi instan suasana panggung (Praise, Worship, Strobe Flash).
   - `Tab 6: Mixer`: Meja 257 fader fisik (1 Grand Master + 256 DMX) berestetika grandMA3 (*tactile ribbed cap*, *illuminated groove rail* dengan LED menyala di belakang fader, dan garis skala kalibrasi analog).

---

## 💻 4. Kompatibilitas Multi-Platform & Responsivitas Layar

- **Development saat ini:** Linux Mint (Laptop ASUS X407MA, 1366×768).
- **Target Deployment:** Windows 11 (Laptop Acer Swift 3 di ruang server/panggung, 1920×1080).
- **Aturan Sizing Responsif:**
  * Default window size: `1200 × 680` px (pas di layar 768p tanpa terpotong panel OS).
  * Minimum window size: `960 × 560` px.
  * Tinggi fader disesuaikan ke `190px` (lebar `52px`) agar pas dan padat di 768p dan meregang elastis di 1080p.
  * Sel grid DMX berukuran `46×46px` (24 kolom = 1056px, muat lega di layar 1366px).

---

## 🔄 5. Disiplin Git & Sinkronisasi

1. Repositori GitHub `zzdree/zzluxora-v10` dan `zzdree/script` adalah **Single Source of Truth**.
2. Setiap fitur yang selesai diuji wajib di-commit dan di-push ke branch `main`.
3. Di laptop utama, sinkronisasi dilakukan hanya dengan `git pull origin main`.

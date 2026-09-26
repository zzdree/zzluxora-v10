# 🎛️ CLAUDE.md — ZZLUXORA v10 (Next-Gen Production Stage Lighting Console)

Panduan arsitektur, instruksi pengembangan, dan konteks operasional untuk **ZZLUXORA v10.0.0** (GrandMA3 Next-Gen Console Architecture).

---

## 📌 1. Ikhtisar & Identitas Proyek

- **Nama Aplikasi:** **ZZLUXORA** (v10.0.0 Flagship Next-Gen)
- **Repositori:** `https://github.com/zzdree/zzluxora-v10.git` (Branch: `main`)
- **Peneliti / Pengembang:** Andreas Restuawanta Christwara (`NIM: 5312422036`)
- **Dosen Pembimbing:** Mario Norman Syah, S.Pd., M.Eng. (`NIP: 199304212024061001`)
- **Institusi:** Program Studi S1 Teknik Komputer, Fakultas Teknik, Universitas Negeri Semarang (UNNES)
- **Karakter Desain:** Modern-minimalis industri panggung pertunjukan (menggabungkan fleksibilitas **grandMA3** dan utilitas **QLC+**).
- **Format File Project:** `.zlx` (JSON terstruktur terkompresi).
- **Format Profil Fixture:** `.zfx` (JSON profil lampu berstandar QLC+).

---

## 🏗️ 2. Arsitektur Perangkat Lunak (Clean Modular Architecture — Feedback v3)

Aplikasi dibangun menggunakan **Python 3.10+** dan **PySide6 (Qt6)** dengan pemisahan tegas antara logika komputasi murni (*Core Engine*) dan antarmuka (*UI/UX*):

```text
zzluxora_v10/
├── core/                      # PURE PYTHON ENGINE (ZERO-GUI DEPENDENCY)
│   ├── __init__.py
│   ├── audio_loader.py        # Pemuat audio multi-format (.wav, .mp3, .flac, .ogg)
│   ├── fft_engine.py          # Implementasi STFT (Hann Window, N=2048, H=512, fs=22050, 43.07 FPS)
│   ├── feature_extractor.py   # Ekstraksi RMS, Spectral Centroid, Chroma 12-semitone, MFCC, Flux
│   ├── emotion_model.py       # Model Afektif Russell 2D Plane (Valence-Arousal)
│   ├── color_engine.py        # Konversi (V, A, RMS) -> HSV -> RGB -> Physical 4-Kanal RGBW
│   ├── artnet_sender.py       # Transmisi UDP socket Port 6454 ke Node DMX (530-byte ArtDmx)
│   ├── models.py              # Data structures: Fixture, Patch, Scene, Chase, ProjectState
│   └── project_io.py          # Serialisasi & Deserialisasi berkas .zlx & .zfx
│
├── ui/                        # USER INTERFACE (PYSIDE6 / QT6)
│   ├── __init__.py
│   ├── styles.py              # Dark theme styling, QSS tokens, grandMA-inspired palette
│   ├── icons.py               # Vektor SVG icons & custom painter helpers
│   ├── assets/                # Asset resmi logo & icon (logo_zz.png, logo_zz.ico)
│   ├── main_window.py         # Root window, unified top header menubar, telemetry, blackout
│   ├── panels/
│   │   ├── address_tab.py     # Grid DMX Address 256 kanal (maks 24 kolom horizontal, color-coded)
│   │   ├── analyze_tab.py     # Core skripsi audio analyzer, YouTube downloader, non-blocking DSP
│   │   ├── result_tab.py      # Metrik afektif Russell 2D, kuadran mood, export to perform
│   │   ├── perform_tab.py     # Live show controller, playlist reordering, cue transitions
│   │   ├── page_tab.py        # Virtual executor buttons (Praise, Worship, Strobe Flash)
│   │   ├── mixer_tab.py       # 257 Slider fader (1 Grand Master + 256 DMX) grandMA3 style
│   │   ├── fixture_list.py    # Floating window: Drawer fixture & drag-and-drop patching
│   │   ├── fixture_editor.py  # Floating window: QLC+ style fixture definition editor (.zfx)
│   │   ├── preview_tab.py     # Floating window: Visualizer panggung 2D & 3D multi-screen
│   │   ├── settings_panel.py  # Dialog: Konfigurasi IP Art-Net (127.0.0.1, 192.168.4.1, Custom)
│   │   ├── help_panel.py      # Dialog: Panduan penggunaan & tabel keyboard shortcuts
│   │   └── about_panel.py     # Dialog: Lembar informasi akademis & identitas pengembang
│   └── widgets/               # Reusable custom UI components (Faders, Knobs, VU Meters)
│
├── markdowns/                 # DOKUMENTASI REKAYASA SISTEMATIS
│   ├── DESIGN.md              # Spesifikasi sistem desain grandMA3, token, & responsivitas
│   ├── PRD.md                 # Product Requirements Document & spesifikasi fungsional
│   ├── ARCHITECTURE.md        # Arsitektur sistem, threading model, & skema data
│   └── ROADMAP.md             # Rencana aksi eksekusi Big Plan v3 bertahap
│
├── fixtures/                  # Preset profil lampu (.zfx & .json)
├── installer/                 # Skrip packaging & deployment (build.py & installer.iss)
├── tests/                     # Unit testing & verification (11 tests pass 100%)
├── requirements.txt           # Dependensi pustaka Python
├── README.md                  # Dokumentasi proyek
└── main.py                    # Entry point aplikasi (Instant launch, zero splashscreen)
```

---

## 🎨 3. Spesifikasi UI/UX (Feedback v3 Implementation)

1. **Peluncuran Instan (Zero Splashscreen):**
   - Aplikasi terbuka seketika (*instant cold launch* < 500 ms) menyerupai QLC+, tanpa jeda splash screen.
2. **Top Header Terpadu (Sidebar Dihapus):**
   - **Kiri:** Logo `zz` glowing + Teks `ZZLUXORA` + Menubar Menu: `[File]` `[Fixture]` `[Editor]` `[Preview]` `[Setting]` `[Help]` `[About]`.
   - **Kanan:**
     * Status Art-Net badge (Hijau = Connected, Merah = Disconnected). Klik badge membuka dialog `Setting`.
     * Tombol Blackout (mengunci Grand Master Fader seketika ke 0).
     * Tombol Play/Stop toggle (mengaktifkan/menonaktifkan transmisi UDP paket DMX).
3. **Jendela Pop-up Mandiri (Floating Windows):**
   - `Fixture List`: Pop-up window daftar fixture dengan dukungan **Drag and Drop** langsung ke Tab Address.
   - `Fixture Definition Editor`: Pop-up window editor profil lampu `.zfx` (JSON) berstandar QLC+ dengan tabel Channel, Label, Type.
   - `Stage Visualizer (Preview)`: Pop-up window visualizer panggung 2D & 3D, dapat dipindah ke second monitor.
   - `Settings`: Pop-up konfigurasi target IP Art-Net (Localhost 127.0.0.1, SoftAP ESP32 192.168.4.1, Custom IP) & Universe 1.
   - `Help` & `About`: Pop-up panduan shortcut keyboard dan data akademik resmi mahasiswa/dospem/UNNES.
4. **Enam Tab Utama Program (Workspaces):**
   - `Tab 1: Address`: Grid 256 kanal DMX (maksimal 24 kolom horizontal, warna sel mengikuti tipe kanal, Clear All dengan konfirmasi, Undo `Ctrl+Z` / Redo `Ctrl+Shift+Z`).
   - `Tab 2: Analyze`: Audio file loader, YouTube audio downloader & converter otomatis, tombol Analyze & Remove, analisis asinkron non-blocking dengan efek blur/dimmed pada area analisis dan tips saintifik DSP.
   - `Tab 3: Result`: Dashboard metrik analisis (Russell 2D plane V-A, BPM, Chroma, kuadran mood Praise/Worship), tombol Re-Analyze, dan Export to Perform.
   - `Tab 4: Perform`: Manajemen urutan playlist pertunjukan panggung, pembuatan cue struktur lagu (Intro/Verse/Chorus/Bridge), waktu fade, chase rate, dan shortcut panggung.
   - `Tab 5: Page`: Lembar tombol virtual executor untuk eksekusi instan suasana panggung (Praise, Worship, Strobe Flash).
   - `Tab 6: Mixer`: Meja 257 fader fisik (1 Grand Master + 256 DMX) berestetika grandMA3 (*tactile ribbed cap*, *illuminated groove rail* dengan LED menyala di belakang fader, dan garis skala kalibrasi analog).

---

## 💻 4. Kompatibilitas Multi-Platform (Linux Mint & Windows 11)

- **Development saat ini:** Linux Mint (Laptop ASUS X407MA, 1366x768).
- **Target Deployment:** Windows 11 (Laptop Acer Swift 3 di ruang server/panggung, 1920x1080).
- **Aturan Cross-Platform:**
  1. Selalu gunakan `pathlib.Path` untuk penanganan berkas dan direktori.
  2. Jaringan UDP socket Art-Net bersifat OS-agnostic (berjalan identik di Linux dan Windows).
  3. Pustaka audio: gunakan backend `soundfile` / `numpy` murni untuk ekstraksi sinyal saat proses analisis batch.
  4. Build `.exe` dijalankan di laptop Windows menggunakan `PyInstaller` dan installer `Inno Setup`.

---

## 🔄 5. Disiplin Git & Sinkronisasi

1. Repositori GitHub `zzdree/zzluxora-v10` dan `zzdree/script` adalah **Single Source of Truth**.
2. Setiap fitur yang selesai diuji wajib di-commit dan di-push ke branch `main`.
3. Di laptop utama, sinkronisasi dilakukan hanya dengan `git pull origin main`.

---

## 🚀 6. Status Pengembangan Terkini

- [x] Dokumen Catatan `script/notes/feedback_v3.txt` terstruktur rapi.
- [x] Dokumen Rekayasa `markdowns/` (`DESIGN.md`, `PRD.md`, `ARCHITECTURE.md`, `ROADMAP.md`).
- [x] Asset Logo Resmi 1:1 `logo_zz.png` (9Router) & `logo_zz.ico`.
- [x] Memory persistent ter-update.
- [ ] Implementasi UI Overhaul (Tahap Eksekusi Big Plan v3).

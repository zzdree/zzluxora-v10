# 🎛️ CLAUDE.md — ZZLUXORA v10 (Next-Gen Production Stage Lighting Console)

Panduan arsitektur, instruksi pengembangan, dan konteks operasional untuk **ZZLUXORA v10.0.0**.

---

## 📌 1. Ikhtisar & Identitas Proyek

- **Nama Aplikasi:** **ZZLUXORA** (v10.0.0 Flagship Next-Gen)
- **Repositori:** `https://github.com/zzdree/zzluxora-v10.git` (Branch: `main`)
- **Peneliti / Pengembang:** Andreas Restuawanta Christwara (`NIM: 5312422036`)
- **Dosen Pembimbing:** Mario Norman Syah, S.Pd., M.Eng. (`NIP: 199304212024061001`)
- **Institusi:** Program Studi S1 Teknik Komputer, Fakultas Teknik, Universitas Negeri Semarang (UNNES)
- **Karakter Desain:** Modern-minimalis industri panggung pertunjukan (menggabungkan fleksibilitas **grandMA3** dan utilitas **QLC+**).
- **Format File Project:** `.zlx` (JSON terstruktur terkompresi).

---

## 🏗️ 2. Arsitektur Perangkat Lunak (Clean Modular Architecture)

Aplikasi dibangun menggunakan **Python 3.10+** dan **PySide6 (Qt6)** dengan pemisahan tegas antara logika komputasi murni (*Core Engine*) dan antarmuka (*UI/UX*):

```text
zzluxora_v10/
├── core/                      # PURE PYTHON ENGINE (ZERO-GUI DEPENDENCY)
│   ├── __init__.py
│   ├── audio_loader.py        # Pemuat audio multi-format (.wav, .mp3, .flac)
│   ├── fft_engine.py          # Implementasi STFT (Hann Window, N=2048, H=512, fs=22050)
│   ├── feature_extractor.py   # Ekstraksi RMS, Spectral Centroid, Chroma 12-semitone, MFCC
│   ├── emotion_model.py       # Model Afektif Russell 2D Plane (Valence-Arousal)
│   ├── color_engine.py        # Konversi (V, A, RMS) -> HSV -> RGB -> Physical 4-Kanal RGBW
│   ├── artnet_sender.py       # Transmisi UDP socket Port 6454 ke Node DMX
│   ├── models.py              # Data structures: Fixture, Patch, Scene, Chase, ProjectState
│   └── project_io.py          # Serialisasi & Deserialisasi berkas .zlx
│
├── ui/                        # USER INTERFACE (PYSIDE6 / QT6)
│   ├── __init__.py
│   ├── styles.py              # Dark theme styling, QSS tokens, grandMA-inspired palette
│   ├── icons.py               # Vektor SVG icons & custom painter helpers
│   ├── main_window.py         # Root window, header bar, menu bar, status, blackout
│   ├── sidebar.py             # Hamburger navigation & view switcher
│   ├── panels/
│   │   ├── program_panel.py   # Container tab program
│   │   ├── address_tab.py     # Grid DMX Address (maks 24 kolom horizontal, auto-patch)
│   │   ├── analyze_tab.py     # Core skripsi audio analyzer & progress bar saintifik
│   │   ├── scenes_tab.py      # Pengelompokan cue musik (Verse, Chorus, Bridge)
│   │   ├── chase_tab.py       # Kontrol urutan chase & timing fader
│   │   ├── page_tab.py        # Virtual executor buttons & custom triggers
│   │   ├── mixer_tab.py       # 513 Slider fader (1 Master + 512 DMX, 0-255)
│   │   ├── preview_tab.py     # Visualizer 2D tampak depan PAR LED
│   │   ├── output_tab.py      # Konfigurasi IP Art-Net (127.0.0.1, 192.168.4.1 ESP32 AP)
│   │   ├── fixture_editor.py  # Modal form pembuatan profile fixture JSON
│   │   ├── fixture_list.py    # Drawer bawah untuk daftar fixture & drag-and-drop
│   │   ├── settings_panel.py  # Pengaturan audio device & preferensi
│   │   └── about_panel.py     # Lembar informasi akademis & identitas pengembang
│   └── widgets/               # Reusable custom UI components (Faders, Knobs, VU Meters)
│
├── fixtures/                  # Preset profil lampu (.json)
│   ├── generic_par_rgbw_4ch.json
│   ├── generic_par_rgbw_7ch.json
│   └── generic_par_rgbw_8ch.json
│
├── installer/                 # Skrip packaging & deployment
│   ├── build.py               # PyInstaller cross-platform builder
│   └── installer.iss          # Inno Setup script untuk Windows 11 installer
│
├── tests/                     # Unit testing & verification
├── requirements.txt           # Dependensi pustaka Python
├── README.md                  # Dokumentasi proyek
└── main.py                    # Entry point aplikasi
```

---

## 🎨 3. Spesifikasi UI/UX (Feedback v1 & v2 Implementation)

1. **Header Bar:**
   - Kiri: Logo lampu putih di background hitam + Tulisan `ZZLUXORA` + Nama / Path file project `.zlx`.
   - Kanan: Indikator status Art-Net (Hijau = Connected, Merah = Disconnected) + Toggle Button Play/Pause + Tombol Lingkaran Blackout (reset fader ke 0).
   - Menu Bar: `[File]` `[View]` `[Help]` (Shortcut Table komprehensif).
2. **Sidebar:**
   - Tombol hamburger (3 garis) di pojok kiri atas (ikon konsisten saat buka/tutup).
   - Jika project belum di-load: sidebar tertutup dengan latar logo samar (*watermark*).
   - Item menu dengan indikator marker aktif: Program, Fixture List, Fixture Editor, Settings, About.
3. **Tab Address:**
   - Grid DMX: Maksimal 24 kotak horizontal, scroll vertikal.
   - Status visual: Kotak kosong (nomor channel di sudut), kotak terisi (ikon warna/fungsi channel).
   - Tombol: Auto-patch sequential, Clear all patch (dialog konfirmasi).
4. **Tab Mixer:**
   - 513 Slider Fader: Fader 1 = Master Dimmer, Fader 2 s.d. 513 = DMX Channel 1 s.d. 512.
   - Nilai fader: 0–255 per channel.
   - Desain slider bergaya konsol grandMA dengan fader cap kotak industrial dan scrollbar horizontal mulus.
5. **Tab Preview:**
   - Visualisasi panggung 2D tampak depan (*front view*).
   - Fixture direpresentasikan sebagai lingkaran warna dinamis (RGBW mixing).
   - Dapat di-drag & drop dengan panel koordinat X & Y di sisi kanan.
6. **Tab Output:**
   - Pilihan IP siap pakai: `127.0.0.1` (Localhost), `192.168.4.1` (ESP32 AP Mode), dan Custom IP.
   - Tombol Save konfigurasi output.

---

## 💻 4. Kompatibilitas Multi-Platform (Linux Mint & Windows 11)

- **Development saat ini:** Linux Mint (Laptop ASUS X407MA).
- **Target Deployment:** Windows 11 (Laptop Acer Swift 3 di ruang server).
- **Aturan Cross-Platform:**
  1. Selalu gunakan `pathlib.Path` untuk penanganan berkas dan direktori.
  2. Jaringan UDP socket Art-Net bersifat OS-agnostic (berjalan identik di Linux dan Windows).
  3. Pustaka audio: gunakan backend `soundfile` / `numpy` murni untuk ekstraksi sinyal tanpa ketergantungan driver audio spesifik OS saat proses analisis batch.
  4. Build `.exe` dijalankan di laptop Windows menggunakan `PyInstaller` dan installer `Inno Setup`.

---

## 🔄 5. Disiplin Git & Sinkronisasi

1. Repositori GitHub `zzdree/zzluxora-v10` adalah **Single Source of Truth**.
2. Setiap fitur yang selesai diuji wajib di-commit dan di-push ke branch `main`.
3. Di laptop utama, sinkronisasi dilakukan hanya dengan `git pull origin main`.

---

## 🚀 6. Status Pengembangan Terkini & Roadmap Agent

### Status Komponen:
- **Core Audio Engine (`core/`):** **TUNTAS 100%**
  - Implementasi: `fft_engine.py`, `feature_extractor.py`, `emotion_model.py`, `color_engine.py`, `artnet_sender.py`, `models.py`, `project_io.py`.
  - Verifikasi: 11 unit tests standar (`tests/test_*.py`) lulus 100% tanpa error.
  - Sesuai dengan formulasi matematis naskah skripsi Bab 2 & Bab 3 (`script_andreas_v4.docx`).
- **Naskah Proposal (`script/`):** **TUNTAS 100%**
  - Berkas: `script_andreas_v4.docx` (2.58 MB) memuat 8 gambar teknis IEEE, 20 rumus Cambria Math, 33 referensi IEEE.
  - Dosen Pembimbing resmi: Mario Norman Syah, S.Pd., M.Eng. (NIP: 199304212024061001).

### Prioritas Pekerjaan Selanjutnya (UI/UX Console Implementation):
Membangun layer antarmuka PySide6 pada folder `ui/` mengacu pada `feedback_v2.txt` dan visualizer grandMA3:
1. `ui/styles.py`: Skema warna gelap industri (*industrial dark theme*), token warna kanal DMX, dan CSS/QSS styling.
2. `ui/icons.py`: Generator ikon prosedural / SVG (lampu, play/pause, blackout, hamburger, dimmer, strobe).
3. `ui/main_window.py`: Jendela utama, header bar terintegrasi, menu bar File/View/Help, status Art-Net, dan master blackout.
4. `ui/sidebar.py`: Navigasi hamburger responsif dengan watermark transparan saat project kosong.
5. `ui/panels/address_tab.py`: Grid DMX 512 kanal (24 kolom horizontal, scroll vertikal, visualisasi fungsi kanal).
6. `ui/panels/analyze_tab.py`: Integrasi AudioLoader, pemutar musik, visualisasi spektrum STFT, dan pemetaan afektif Russell 2D.
7. `ui/panels/mixer_tab.py`: 513 slider fader fisik (1 Master + 512 DMX channels 0–255) dengan fader cap grandMA style.
8. `ui/panels/preview_tab.py`: Panggung 2D tampak depan dengan rendering cahaya PAR LED dinamis (RGBW glow).
9. `ui/panels/output_tab.py`: Pengaturan jaringan Art-Net UDP 6454 (Localhost, ESP32 AP 192.168.4.1, Custom IP).
10. `ui/panels/fixture_editor.py` & `fixture_list.py`: Pengelola profil fixture lampu JSON dan patching.

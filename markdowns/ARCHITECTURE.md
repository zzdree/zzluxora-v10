# 🏗️ ARCHITECTURE.md — ZZLUXORA v10 Software Architecture

**Spesifikasi Arsitektur Sistem, Desain Modul, & Alur Data**  
*Framework: Python 3.10+ / Universal Qt6 (`ui/qt_compat.py`) | Pola: Clean Modular Architecture*

---

## 📌 1. Ikhtisar Arsitektur (High-Level Overview)

Perangkat lunak **ZZLUXORA v10** dirancang dengan prinsip **Pemisahan Kepentingan Secara Tegas (Strict Separation of Concerns)**:
1. **Core Engine (`core/`):** Pure Python / NumPy tanpa ketergantungan GUI (Zero-GUI Dependency). Bertanggung jawab atas kalkulasi matematis sinyal audio, pemodelan afektif Russell, dekomposisi warna fisik RGBW, konstruksi biner paket ArtDmx, dan I/O berkas.
2. **UI Layer (`ui/`):** Antarmuka pengguna berbasis event-driven dengan kompatibilitas ganda PySide6 & PyQt6. Bertanggung jawab atas rendering grafis konsol, visualisasi panggung, fader slider grandMA, dan manajemen jendela non-modal floating.
3. **Hardware / Network Interface:** Komunikasi soket UDP port 6454 (Universe 0) ke node ESP32 fisik atau simulator QLC+ melalui loopback `127.0.0.1`. Transmisi bersifat Play-gated.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        ZZLUXORA v10 USER INTERFACE                    │
│                                                                        │
│  [ZZ] ZZLUXORA [Untitled.zlx]                           (OS Title Bar) │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     PURE NATIVE QMenuBar                         │  │
│  │  File    Fixture    Editor    Preview    Setting    Help    About│  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │                     PROGRAM VIEW BAR                             │  │
│  │  [Address] [Analyze] [Result] [Perform] [Page] [Mixer]           │  │
│  │                  │ [ART-NET: IDLE] │ [BLACKOUT] │ [PLAY]         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │               MAIN WORKSPACES (6 TAB CENTRAL CONTAINER)          │  │
│  │  1. Address  │  2. Analyze  │  3. Result  │  4. Perform  │       │  │
│  │  5. Page     │  6. Mixer    │             │              │       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         │                ▲                                             │
│         ▼                │                                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │        FLOATING TOOL WINDOWS (DETACHABLE / NON-MODAL)            │  │
│  │  • Fixture List Window      (Drag-and-Drop Patching)             │  │
│  │  • Fixture Definition Editor (QLC+ Style Table Editor .zfx)      │  │
│  │  • Stage Visualizer Window  (2D Front View RGBW Light Beams)     │  │
│  │  • Network Setting Dialog   (Adapter IP & Universe 0 Setup)      │  │
│  │  • Help & About Dialogs     (Shortcuts & Student Credentials)    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Event Bus / Qt Signals
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     ASYNCHRONOUS WORKER THREADS                        │
│                                                                        │
│  ┌───────────────────────────────┐   ┌──────────────────────────────┐  │
│  │     AudioAnalysisWorker       │   │    YouTubeDownloaderWorker   │  │
│  │ (STFT, MFCC, Chroma, Russell) │   │ (Download & Audio Extraction)│  │
│  └───────────────────────────────┘   └──────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Shared Memory Data Structures
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     PURE PYTHON CORE ENGINE (`core/`)                  │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │   FFTEngine      │  │ FeatureExtractor │  │     EmotionModel     │  │
│  │(Hann STFT, N=2048│  │(RMS, Centroid,   │  │ (Russell 2D Plane,   │  │
│  │ H=512, 43.07 FPS)│  │ Chroma, MFCC)    │  │  Valence-Arousal)    │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│           │                     │                       │              │
│           └─────────────────────┼───────────────────────┘              │
│                                 ▼                                      │
│                        ┌──────────────────┐                            │
│                        │   ColorEngine    │                            │
│                        │ (HSV -> sRGB ->  │                            │
│                        │ Physical 4-ch W) │                            │
│                        └────────┬─────────┘                            │
│                                 ▼                                      │
│                        ┌──────────────────┐                            │
│                        │   ArtNetSender   │                            │
│                        │ (530-byte ArtDmx │                            │
│                        │ UDP Port 6454)   │                            │
│                        └────────┬─────────┘                            │
└─────────────────────────────────┼──────────────────────────────────────┘
                                  │ UDP Broadcast / Unicast Datagrams
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   TARGET HARDWARE & SIMULATION ENGINE                  │
│                                                                        │
│  ┌─────────────────────────────────┐ ┌──────────────────────────────┐  │
│  │   ESP32 DevKit V1 Hardware Node │ │ QLC+ v4 / v5 Simulation SITL │  │
│  │  (UART2 DMX512 -> MAX485 -> XLR)│ │ (127.0.0.1:6454 Loopback)    │  │
│  └─────────────────────────────────┘ └──────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 2. Rincian Modul & Sub-Sistem

### 2.1. Lapisan Inti Audio & Pencahayaan (`core/`)
- `fft_engine.py`:
  * Implementasi Cooley-Tukey Radix-2 DIT FFT dan STFT jendela geser.
  * Parameter: $N=2048$, $H=512$, $f_s=22.050\text{ Hz}$.
  * Menghasilkan frame rate tepat $43.07\text{ FPS}$ ($\approx 23.22\text{ ms}$) yang sinkron dengan laju transmisi fisik DMX512 (44 FPS).
  * Menerapkan Hann Window $w[n] = \sin^2\left(\frac{\pi n}{N-1}\right)$ untuk menekan *spectral leakage* hingga $-31.5\text{ dB}$.
- `feature_extractor.py`:
  * Menghitung 5 fitur utama MIR:
    1. RMS Energy (berdasarkan Teorema Parseval).
    2. Spectral Centroid (titik berat frekuensi audio).
    3. Chroma STFT 12-semitone ($C, C\sharp, D, \dots, B$) untuk deteksi akord Mayor/Minor.
    4. MFCC (13 koefisien dari 40 filterbank Mel).
    5. Spectral Flux (deteksi onset & ketukan musik).
- `emotion_model.py`:
  * Pemetaan fitur spektral ke Bidang Afektif Russell 2D $(V, A) \in [-1.0, 1.0]$.
  * Penentuan kuadran ibadah: Kuadran 1 (*Praise / Sukacita*) vs Kuadran 3 (*Deep Worship / Khidmat*).
- `color_engine.py`:
  * Transformasi $(V, A) \to (H, S)$ dan $\text{Dimmer} = \text{RMS}_{\text{norm}}$.
  * Konversi ruang warna HSV ke sRGB.
  * Dekomposisi fisik 4-kanal (*Physical RGBW Decomposition*) anti-washout:
    $$W = \min(R, G, B), \quad R' = R - W, \quad G' = G - W, \quad B' = B - W$$
- `artnet_sender.py`:
  * Enkapsulasi biner 530 byte paket ArtDmx (18 byte header little-endian opcode + 512 byte data DMX payload).
  * Transmisi non-blocking via UDP socket Port 6454.
- `models.py` & `project_io.py`:
  * Struktur data `ProjectState`, `FixtureProfile`, `PatchEntry`, `SceneCue`, `ChaseSequence`.
  * Serialisasi terkompresi berkas `.zlx` dan profil lampu `.zfx`.

### 2.2. Lapisan Antarmuka Pengguna (`ui/`)
- `main_window.py`:
  * Jendela utama (Root Window) tanpa sidebar.
  * Mengintegrasikan Header Bar dengan Menubar Menu (File, Fixture, Editor, Preview, Setting, Help, About).
  * Menampung `QTabWidget` untuk 6 tab utama program: Address, Analyze, Result, Perform, Page, Mixer.
  * Menyediakan telemetry Art-Net status, tombol Grand Master Blackout, dan tombol Play/Stop Art-Net streaming.
- `styles.py`:
  * Skema token warna industri panggung (`Theme`) dan Master QSS.
  * Definisi styling fader tactile cap, backlit rail, dan tombol konsol.
- `icons.py`:
  * Generator SVG prosedural untuk rendering ikon resolusi tinggi bebas distorsi (logo, play, pause, blackout, lamp, strobe, dimmer).
- `panels/address_tab.py`:
  * Grid DMX 256 kanal (24 kolom horizontal).
  * Mendukung aksi drop fixture dari Fixture List, auto-patching sekuensial, Clear Patch dengan konfirmasi, serta Undo/Redo (`Ctrl+Z` / `Ctrl+Shift+Z`).
- `panels/analyze_tab.py`:
  * Audio file loader & YouTube downloader input.
  * Asynchronous processing thread: area analisis diburamkan/dimmed tanpa mengunci GUI.
  * Progress bar dan scientific descriptive tips yang terkalibrasi secara dinamis.
- `panels/result_tab.py`:
  * Dashboard visualisasi hasil analisis (Russell 2D plane, metrik audio, palette warna).
  * Tombol re-analyze dan export to perform.
- `panels/perform_tab.py`:
  * Pengatur playlist pertunjukan live, pengaturan transisi scene (fade-in, fade-out, chase rate).
- `panels/page_tab.py`:
  * Executor page berisi tombol virtual untuk trigger instan suasana panggung (Praise, Worship, Strobe).
- `panels/mixer_tab.py`:
  * Meja mixer 257 fader fisik (1 Grand Master + 256 Kanal DMX).
  * Rel fader dengan efek LED backlight dan skala kalibrasi garis analog.
- `panels/fixture_list.py` (Floating Window):
  * Jendela pop-up daftar lampu yang dapat di-drag ke Tab Address.
- `panels/fixture_editor.py` (Floating Window):
  * Jendela editor profil lampu `.zfx` berstandar QLC+.
- `panels/preview_tab.py` (Floating Window):
  * Jendela visualizer panggung 2D dan 3D multi-screen support.
- `panels/settings_panel.py` (Dialog):
  * Dialog pengaturan IP Art-Net (Localhost 127.0.0.1, SoftAP ESP32 192.168.4.1, Custom).

---

## 🧵 3. Manajemen Thread & Eksekusi Asinkron

Untuk menjaga kestabilan antarmuka di lingkungan panggung (*zero-freeze guarantee*):
1. **GUI Thread (Main Event Loop):**
   * Menangani event rendering, interaksi pengguna, pergerakan slider fader, dan status display.
2. **AudioAnalysisWorker (`QThread`):**
   * Menjalankan ekstraksi STFT, MFCC, dan chroma pada berkas audio berukuran besar di thread latar belakang.
   * Mengirimkan sinyal progress (`progressChanged(int, str)`) ke GUI untuk memperbarui teks ilmiah dan progress bar.
   * Mengirimkan sinyal selesai (`analysisFinished(AnalysisResult)`) ke Tab Result.
3. **YouTubeDownloaderWorker (`QThread`):**
   * Menangani pengunduhan audio YouTube dan ekstraksi streams tanpa menghalangi interaksi pengguna pada tab lain.
4. **ArtNetStreamWorker (`QTimer` / Core Loop):**
   * Memancarkan paket UDP DMX512 pada interval tepat $23.22\text{ ms}$ (43 FPS) untuk menjamin stabilitas frame rate perangkat penerima.

---

## 💾 4. Skema Berkas Data

### 4.1. Berkas Proyek (`.zlx` — ZZLUXORA Project File)
Format JSON terstruktur memuat:
```json
{
  "version": "10.0.0",
  "project_name": "Worship_Sunday_Live",
  "created_at": "2026-09-27T10:00:00Z",
  "patch_table": [
    {"channel": 1, "fixture_id": "par_01", "type": "Red", "label": "PAR 1 Red", "value": 0},
    {"channel": 2, "fixture_id": "par_01", "type": "Green", "label": "PAR 1 Green", "value": 0}
  ],
  "songs": [
    {
      "title": "Kebaikan Tuhan",
      "audio_path": "data/audio/kebaikan_tuhan.mp3",
      "bpm": 72.0,
      "valence": 0.65,
      "arousal": -0.42,
      "mood_quadrant": "Q3 Worship",
      "color_palette": {"R": 180, "G": 90, "B": 240, "W": 45}
    }
  ],
  "mixer_state": {
    "grand_master": 255,
    "channels": [255, 0, 128, ...]
  }
}
```

### 4.2. Berkas Profil Lampu (`.zfx` — ZZLUXORA Fixture Profile)
```json
{
  "manufacturer": "Generic",
  "model": "PAR LED 54x3W RGBW",
  "channel_count": 8,
  "channels": [
    {"index": 1, "label": "Master Dimmer", "type": "Dimmer"},
    {"index": 2, "label": "Red", "type": "Red"},
    {"index": 3, "label": "Green", "type": "Green"},
    {"index": 4, "label": "Blue", "type": "Blue"},
    {"index": 5, "label": "White", "type": "White"},
    {"index": 6, "label": "Strobe", "type": "Strobe"},
    {"index": 7, "label": "Mode Function", "type": "Color Macro"},
    {"index": 8, "label": "Speed", "type": "Empty"}
  ]
}
```

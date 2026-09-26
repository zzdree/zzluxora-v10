# 🧩 COMPONENT_SPEC.md — ZZLUXORA v10 Component Specification

**Spesifikasi Detail Komponen Antarmuka & Logika Widget**  
*Senior Software Architect Edition — Standar Desain Universal Qt6 (PySide6 / PyQt6)*

---

## 📌 1. Daftar Komponen & Pemetaan Berkas

| Nama Komponen | Berkas Implementasi | Tipe Qt Base | Peran & Tanggung Jawab |
| :--- | :--- | :--- | :--- |
| **`MainWindow`** | `ui/main_window.py` | `QMainWindow` | Root application window, native QMenuBar, program bar, global undo, Art-Net loop |
| **`TactileFader`** | `ui/widgets/tactile_fader.py` | `QWidget` | Fader slider grandMA (rel LED menyala, cap bertakik 30x18, garis skala, tinggi 190px) |
| **`AddressGrid`** | `ui/panels/address_tab.py` | `QWidget` | Matriks 256 kanal DMX (sel 46x46px), drag-drop receiver, clean tags (DIM, RED, GRN, BLU, WHT, STR) |
| **`AnalyzePanel`** | `ui/panels/analyze_tab.py` | `QWidget` | Pemuat audio, pemicu YouTube dialog, progress bar saintifik non-blocking QThread |
| **`YouTubeDialog`** | `ui/widgets/youtube_dialog.py`| `QDialog` | Pop-up pengunduh audio YouTube mandiri & ekstraksi berkas lokal ke `data/audio/` |
| **`ResultPanel`** | `ui/panels/result_tab.py` | `QWidget` | Dashboard metrik Russell 2D, kuadran mood, tombol Export to Perform |
| **`PerformPanel`** | `ui/panels/perform_tab.py` | `QWidget` | Show controller, playlist reordering, cue timing, Generate Executors |
| **`PagePanel`** | `ui/panels/page_tab.py` | `QWidget` | Virtual executor sheet, tombol hasil auto-generate dari Perform, flash strobe |
| **`MixerPanel`** | `ui/panels/mixer_tab.py` | `QWidget` | Container 257 fader fisik (1 Master + 256 DMX) dengan smooth horizontal scrollbar |
| **`FixtureListWin`** | `ui/panels/fixture_list.py`| `QWidget` (Window)| Jendela pop-up non-modal daftar fixture lampu dengan MIME drag source |
| **`FixtureEditorWin`**| `ui/panels/fixture_editor.py`| `QMainWindow` | Jendela pop-up non-modal editor profil lampu `.zfx` berstandar QLC+ |
| **`StageVisualizerWin`**| `ui/panels/preview_tab.py`| `QWidget` (Window)| Jendela visualizer panggung 2D multi-screen support (non-modal) |
| **`SettingsDialog`**| `ui/panels/settings_panel.py`| `QDialog` (Window)| Jendela pop-up non-modal adapter scanner & konfigurasi target IP Art-Net (Universe 0) |
| **`HelpDialog`** | `ui/panels/help_panel.py` | `QDialog` (Window)| Jendela pop-up non-modal panduan operasional & tabel keyboard shortcuts |
| **`AboutDialog`** | `ui/panels/about_panel.py` | `QDialog` (Window)| Jendela pop-up non-modal identitas akademik resmi mahasiswa & universitas |

---

## 🎛️ 2. Spesifikasi Detail Komponen Kunci

### 2.1. `TactileFader` (grandMA Console Fader)
- **Base Class:** `QWidget` (Custom Painted via `QPainter` untuk performa 60 FPS tanpa beban stylesheet kompleks).
- **Properti:**
  * `channel_id: int` (0 = Grand Master, 1–256 = DMX channels).
  * `value: int` (Rentang: 0 s.d. 255).
  * `is_master: bool` (True jika Grand Master, menentukan warna rel LED).
  * `label: str` (Nama kanal / fixture).
- **Dimensi Compact (768p & 1080p Optimized):**
  * Lebar widget: 52px, Tinggi minimum: 190px.
  * Cap Fader: Lebar 30px, Tinggi 18px.
  * Margin: Top 18px, Bottom 38px.
- **Elemen Grafis (`paintEvent`):**
  1. *Background & Slot:* Cekungan slot hitam abu pekat (`#14161a`) berlebar 4px dengan radius sudut 2px.
  2. *Illuminated Groove (Rel LED):* Garis cahaya vertikal di dasar rel dari posisi bawah ke posisi cap:
     - Master Dimmer: Warna Warm Amber Glow (`#f59e0b`).
     - DMX Channels: Warna Cyan Neon Glow (`#06b6d4`).
  3. *Scale Markings (Garis Skala Analog):*
     - Garis penanda level di kiri dan kanan rel (lebar 6px, warna `#475569`).
     - Garis utama tebal pada nilai 0 (bawah), 127 (tengah 50%), dan 255 (atas 100%).
  4. *Tactile Cap (Knob):*
     - Bentuk trapesium berkontur dengan cekungan jari horizontal di tengah cap.
     - Garis penunjuk nilai putih presisi (`#ffffff`, tebal 2px) tepat di titik tengah horizontal cap.
  5. *Value Display & Direct Typing:*
     - Di bawah fader: Box angka DMX (0–255). Double-click memungkinkan operator mengetik nilai secara presisi.
- **Sinyal:** `valueChanged(int channel_id, int new_value)`.

---

### 2.2. `AddressGrid` (DMX 1–256 Patch Sheet)
- **Base Class:** `QWidget` dengan scroll vertikal `QScrollArea`.
- **Layout Geometri:**
  * Maksimal 24 kolom horizontal per baris.
  * Ukuran sel: 46×46px elastis mengikuti lebar jendela (total lebar 1056px, muat lega di layar 1366px).
- **Logika State Per Sel Kotak:**
  * *Unpatched:* Latar belakang `#282c34`, border 1px `#383e4c`, nomor DMX di sudut kanan atas (`#94a3b8`).
  * *Patched:* Latar belakang solid sesuai jenis kanal:
    - Dimmer -> Amber `#d97706` [`DIM`]
    - Red -> Merah `#dc2626` [`RED`]
    - Green -> Hijau `#16a34a` [`GRN`]
    - Blue -> Biru `#2563eb` [`BLU`]
    - White -> Putih `#f8fafc` [`WHT`] (teks label gelap)
    - Strobe -> Kuning `#eab308` [`STR`]
  * Label kanal di posisi tengah sel, nomor kanal DMX tetap di sudut kanan atas.
- **Drag and Drop Protocol:**
  * Menerima MIME type: `application/x-zzluxora-fixture`.
  * Saat fixture dijatuhkan ke sel $k$: sistem otomatis me-reserve kanal $k$ s.d. $k + N - 1$ ($N$ = jumlah kanal fixture) dan memperbarui grid secara instan.
- **Fitur Khusus:**
  * Tombol `[CLEAR PATCH]` memicu dialog konfirmasi. Aksi ini direkam ke dalam `GlobalUndoStack`.

---

### 2.3. `YouTubeDialog` (Standalone Audio Importer)
- **Base Class:** `QDialog` (Windowed non-modal).
- **Elemen:**
  * `QLineEdit`: Kolom input URL YouTube.
  * `QPushButton`: Tombol `[DOWNLOAD & EXTRACT AUDIO]`.
  * `QProgressBar`: Indikator persentase pengunduhan real-time.
  * `QLabel`: Status unduhan.
- **Backend Thread:** `YouTubeDownloaderWorker(QThread)`:
  * Mengunduh audio murni tanpa video ke direktori `data/audio/`.
  * Mengirim sinyal `download_finished(str file_path)`.
- **Integrasi Otomatis:** Setelah selesai, dialog tertutup dan file audio otomatis di-load ke `AnalyzePanel`.

---

### 2.4. `AnalyzePanel` (Core Audio & DSP Engine)
- **Elemen:**
  * Tombol `[LOAD AUDIO...]` dan `[IMPORT YOUTUBE...]`.
  * Tampilan informasi audio terpilih (Judul Lagu, Format, Durasi, Sample Rate $22.050\text{ Hz}$).
  * Tombol `[ANALYZE]` dan `[REMOVE SONG]`.
  * Waveform Viewer & Spektrogram FFT STFT real-time.
- **Asynchronous Blur & Scientific Ticker:**
  * Saat analisis berjalan, area widget dilapisi overlay semitransparan bertuliskan status komputasi ilmiah:
    - *“Menghitung Short-Time Fourier Transform (Hann Window N=2048, H=512)...”*
    - *“Mengekstrak Spectral Centroid & 12-Semitone Chroma STFT...”*
    - *“Menghitung 13 Koefisien MFCC & Deteksi Onset Spectral Flux...”*
    - *“Memetakan Koordinat Afektif ke Russell 2D Plane (Valence-Arousal)...”*
  * Pengguna tetap dapat berpindah ke tab lain tanpa lagging atau freeze GUI.

---

### 2.5. `PerformPanel` & Fitur Auto-Generate `GENERATE EXECUTORS`
- **Elemen:**
  * Playlist manager: Daftar urutan lagu ibadah yang dapat di-reorder via `[MOVE UP]` dan `[MOVE DOWN]`.
  * Section Cue Table: Daftar bagian lagu (Intro, Verse, Chorus, Bridge, Ending) lengkap dengan timing durasi, fade time, dan chase rate.
  * Tombol Aksi: **`[GENERATE EXECUTORS]`**.
- **Logika Otomasi:**
  * Saat tombol ditekan, sistem mengiterasi playlist lagu dan secara otomatis membangkitkan tombol-tombol eksekutor virtual pada `PagePanel`:
    - Tombol Suasana Utama (Praise Mood / Worship Mood).
    - Tombol Cue Tiap Section Lagu.
    - Tombol Flash Strobe.

---

### 2.6. `FixtureEditorWindow` (QLC+ Inspired)
- **Base Class:** `QMainWindow` (Windowed tool window mandiri dengan min/max/close).
- **Menubar Mandiri:** `[File]` -> `Open (.zfx)`, `Save`, `Save As`.
- **Komponen Form:**
  * Nama Pabrikan (*Manufacturer*), Nama Model (*Model*), Jumlah Kanal (*Channel Count*).
  * `QTableWidget` Pemetaan Kanal:
    - Kolom 1: Indeks Kanal (Ch 01, Ch 02, ...).
    - Kolom 2: Label Deskripsi (Dimmer, Red, Green, Blue, White, Strobe, Program, Speed, dll.).
    - Kolom 3: Tipe Dropdown (Dimmer, Red, Green, Blue, White, Strobe, Pan, Tilt, Color Macro, Empty).
- **Output Berkas:** Format JSON `.zfx` dan `.json` yang kompatibel dengan library fixture ZZLUXORA.

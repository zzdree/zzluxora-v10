# 🧩 COMPONENT_SPEC.md — ZZLUXORA v10 Component Specification

**Spesifikasi Detail Komponen Antarmuka & Logika Widget**  
*Senior Software Architect Edition — Standar Desain PySide6 (Qt6)*

---

## 📌 1. Daftar Komponen & Pemetaan Berkas

| Nama Komponen | Berkas Implementasi | Tipe Qt Base | Peran & Tanggung Jawab |
| :--- | :--- | :--- | :--- |
| **`MainWindow`** | `ui/main_window.py` | `QMainWindow` | Root application window, 3-level header, tab switching, global undo |
| **`HeaderBar`** | `ui/widgets/header_bar.py` | `QWidget` | Title bar (Level 1), Menu bar (Level 2), Program bar (Level 3) |
| **`TactileFader`** | `ui/widgets/tactile_fader.py` | `QWidget` | Fader slider grandMA3 (rel ber-LED, cap bertakik, garis skala) |
| **`AddressGrid`** | `ui/panels/address_tab.py` | `QWidget` | Matriks 256 kanal DMX, drag-drop patch receiver, channel styling |
| **`AnalyzePanel`** | `ui/panels/analyze_tab.py` | `QWidget` | Pemuat audio, pemicu YouTube dialog, progress bar saintifik non-blocking |
| **`YouTubeDialog`** | `ui/widgets/youtube_dialog.py`| `QDialog` | Pop-up pengunduh audio YouTube mandiri & ekstraksi berkas lokal |
| **`ResultPanel`** | `ui/panels/result_tab.py` | `QWidget` | Dashboard metrik Russell 2D, kuadran mood, tombol Export to Perform |
| **`PerformPanel`** | `ui/panels/perform_tab.py` | `QWidget` | Show controller, playlist reordering, cue timing, Export to Page |
| **`PagePanel`** | `ui/panels/page_tab.py` | `QWidget` | Virtual executor sheet, auto-generated scene buttons, flash strobe |
| **`MixerPanel`** | `ui/panels/mixer_tab.py` | `QWidget` | Container 257 fader fisik dengan smooth horizontal scrollbar |
| **`FixtureListWin`** | `ui/panels/fixture_list.py`| `QWidget` (Window)| Jendela pop-up daftar fixture lampu dengan MIME drag source |
| **`FixtureEditorWin`**| `ui/panels/fixture_editor.py`| `QMainWindow` | Jendela pop-up editor profil lampu `.zfx` berstandar QLC+ |
| **`StageVisualizerWin`**| `ui/panels/preview_tab.py`| `QWidget` (Window)| Jendela visualizer panggung 2D & 3D (multi-monitor support) |
| **`SettingsDialog`**| `ui/panels/settings_panel.py`| `QDialog` | Pop-up adapter scanner & konfigurasi target IP Art-Net |
| **`HelpDialog`** | `ui/panels/help_panel.py` | `QDialog` | Pop-up panduan operasional & tabel keyboard shortcuts |
| **`AboutDialog`** | `ui/panels/about_panel.py` | `QDialog` | Pop-up identitas akademik resmi mahasiswa & universitas |

---

## 🎛️ 2. Spesifikasi Detail Komponen Kunci

### 2.1. `TactileFader` (grandMA3 Console Fader)
- **Base Class:** `QWidget` (Custom Painted via `QPainter` untuk performa 60 FPS tanpa beban stylesheet kompleks).
- **Properti:**
  * `channel_id: int` (0 = Grand Master, 1–256 = DMX channels).
  * `value: int` (Rentang: 0 s.d. 255).
  * `is_master: bool` (True jika Grand Master, menentukan warna rel LED).
  * `label: str` (Nama kanal / fixture).
- **Elemen Grafis (`paintEvent`):**
  1. *Background & Slot:* Cekungan slot hitam abu pekat (`#14161a`) berlebar 4px dengan radius sudut 2px.
  2. *Illuminated Groove (Rel LED):* Garis cahaya vertikal di dasar rel dari posisi bawah ke posisi cap:
     - Master Dimmer: Warna Warm Amber Glow (`#f59e0b`).
     - DMX Channels: Warna Cyan Neon Glow (`#06b6d4`).
  3. *Scale Markings (Garis Skala Analog):*
     - Garis penanda level di kiri dan kanan rel (lebar 6px, warna `#475569`).
     - Garis utama tebal pada nilai 0 (bawah), 127 (tengah 50%), dan 255 (atas 100%).
  4. *Tactile Cap (Knob):*
     - Dimensi: 32px (lebar) × 22px (tinggi).
     - Warna: `#282c34` bergradasi halus ke `#1e2024` dengan border 1px `#4a5264`.
     - Cekungan jari horizontal di tengah cap.
     - Garis penunjuk nilai putih presisi (`#ffffff`, tebal 2px) tepat di titik tengah horizontal cap.
  5. *Value Display & Direct Typing:*
     - Di bawah fader: Box angka DMX (0–255). Double-click memungkinkan operator mengetik nilai secara presisi.
- **Sinyal:** `valueChanged(int channel_id, int new_value)`.

---

### 2.2. `AddressGrid` (DMX 1–256 Patch Sheet)
- **Base Class:** `QWidget` dengan scroll vertikal `QScrollArea`.
- **Layout Geometri:**
  * Maksimal 24 kolom horizontal per baris.
  * 11 baris (256 sel total, baris terakhir memuat 16 sel).
  * Ukuran sel: 52×52px elastis mengikuti lebar jendela.
- **Logika State Per Sel Kotak:**
  * *Unpatched:* Latar belakang `#282c34`, border 1px `#383e4c`, nomor DMX di sudut kanan atas (`#94a3b8`).
  * *Patched:* Latar belakang solid sesuai jenis kanal:
    - Dimmer -> Amber `#d97706` + Ikon 💡
    - Red -> Merah `#dc2626`
    - Green -> Hijau `#16a34a`
    - Blue -> Biru `#2563eb`
    - White -> Putih `#f8fafc` (teks label gelap)
    - Strobe -> Kuning `#eab308` + Ikon ⚡
  * Label kanal di posisi tengah sel, nomor kanal DMX tetap di sudut kanan atas.
- **Drag and Drop Protocol:**
  * Menerima MIME type: `application/x-zzluxora-fixture`.
  * Saat fixture dijatuhkan ke sel $k$: sistem otomatis me-reserve kanal $k$ s.d. $k + N - 1$ ($N$ = jumlah kanal fixture) dan memperbarui grid secara instan.
- **Fitur Khusus:**
  * Tombol `[Clear All Patch]` memicu dialog konfirmasi. Aksi ini direkam ke dalam `GlobalUndoStack`.

---

### 2.3. `YouTubeDialog` (Standalone Audio Importer)
- **Base Class:** `QDialog` (Windowed non-modal).
- **Elemen:**
  * `QLineEdit`: Kolom input URL YouTube (dengan placeholder `https://www.youtube.com/watch?v=...`).
  * `QPushButton`: Tombol `[⬇ Download & Extract Audio]`.
  * `QProgressBar`: Indikator persentase pengunduhan real-time.
  * `QLabel`: Status unduhan (Downloading audio stream -> Converting to MP3/WAV -> Saving to local).
- **Backend Thread:** `YouTubeDownloaderWorker(QThread)`:
  * Menggunakan modul Python `yt-dlp` (atau fallback stream generator) untuk mengunduh audio murni tanpa video ke direktori `data/audio/`.
  * Mengirim sinyal `downloadCompleted(str file_path)`.
- **Integrasi Otomatis:** Setelah selesai, dialog tertutup dan file audio otomatis di-load ke `AnalyzePanel`.

---

### 2.4. `AnalyzePanel` (Core Audio & DSP Engine)
- **Elemen:**
  * Tombol `[📁 Load Audio File]` dan `[🌐 Import from YouTube]`.
  * Tampilan informasi audio terpilih (Judul Lagu, Format, Durasi, Sample Rate $22.050\text{ Hz}$).
  * Tombol `[⚡ Analyze Song]` dan `[🗑️ Remove Song]`.
  * Waveform Viewer & Spektrogram FFT STFT real-time.
- **Asynchronous Blur & Scientific Ticker:**
  * Saat analisis berjalan, area widget dilapisi overlay semitransparan bertuliskan status komputasi ilmiah:
    - *“Menghitung Short-Time Fourier Transform (Hann Window N=2048, H=512)...”*
    - *“Mengekstrak Spectral Centroid & 12-Semitone Chroma STFT...”*
    - *“Menghitung 13 Koefisien MFCC & Deteksi Onset Spectral Flux...”*
    - *“Memetakan Koordinat Afektif ke Russell 2D Plane (Valence-Arousal)...”*
  * Pengguna tetap dapat berpindah ke tab lain tanpa lagging atau freeze GUI.

---

### 2.5. `PerformPanel` & Fitur Auto-Generate `Export to Page`
- **Elemen:**
  * Playlist manager: Daftar urutan lagu ibadah yang dapat di-drag untuk mengubah urutan (*reorder*).
  * Section Cue Table: Daftar bagian lagu (Intro, Verse 1, Chorus, Bridge, Altar Call, Ending) lengkap dengan timing durasi, fade time, dan chase rate.
  * Tombol Aksi: **`[⚡ Generate / Export to Page]`**.
- **Logika Otomasi `Export to Page`:**
  * Saat tombol ditekan, sistem mengiterasi seluruh section lagu dan secara otomatis membangkitkan tombol-tombol eksekutor virtual pada `PagePanel`:
    - Tombol Suasana Utama (Praise Mood / Worship Mood).
    - Tombol Cue Tiap Section Lagu.
    - Tombol Flash Strobe.

---

### 2.6. `FixtureEditorWindow` (QLC+ Inspired)
- **Base Class:** `QMainWindow` (Windowed tool window mandiri).
- **Menubar Mandiri:** `[File]` -> `Open (.zfx)`, `Save`, `Save As`.
- **Komponen Form:**
  * Nama Pabrikan (*Manufacturer*), Nama Model (*Model*), Jumlah Kanal (*Channel Count*).
  * `QTableWidget` Pemetaan Kanal:
    - Kolom 1: Indeks Kanal (1, 2, 3, ...).
    - Kolom 2: Label Deskripsi (Dimmer, Red, Green, Blue, White, Strobe, dll.).
    - Kolom 3: Tipe Dropdown (Dimmer, Red, Green, Blue, White, Strobe, Pan/Tilt, Color Macro, Empty).
- **Output Berkas:** Format JSON `.zfx` yang kompatibel dengan library fixture ZZLUXORA.

# 🎨 DESIGN.md — ZZLUXORA v10 Design System & UI Specification

**Sistem Desain & Panduan Antarmuka Konsol Pencahayaan Panggung Generasi Mutakhir**  
*Lead Architect / Senior Developer Edition — Standar Industri grandMA2/grandMA3 onPC & Utilitas QLC+*

---

## 📌 1. Filosofi & Visi Desain

Aplikasi **ZZLUXORA v10** adalah perangkat lunak konsol pencahayaan panggung cerdas (*intelligent stage lighting console*) yang mengemulasi feel, keandalan, dan ketangguhan konsol pencahayaan fisik profesional (MA Lighting grandMA2 & grandMA3 onPC) ke dalam antarmuka desktop modern yang ringan dan berkinerja tinggi.

### Prinsip Inti Rekayasa Desain:
1. **Pure Dark Grey Theme (Kenyamanan FOH):**
   Tidak menggunakan hitam legam OLED (#000000) yang melelahkan mata akibat kontras berlebih, melainkan **Pure Dark Grey** industri elegan (`#1e2024` s.d. `#282c34`). Warna ini menyerupai lempengan bodi baja/aluminium konsol panggung asli.
2. **Tipografi Putih Bersih Kontras Tinggi (High-Contrast White):**
   Seluruh teks nama channel, angka DMX (0–255), label fader, dan menu menggunakan **Putih Bersih** (`#ffffff` / `#f8fafc`) dengan rendering subpixel tajam agar operator FOH dapat membaca parameter dari jarak pandang panggung tanpa salah ketik/baca.
3. **Hardware Tactile Emulation:**
   Fader slider dirancang khusus dengan rel ber-LED menyala lembut (*illuminated groove rail*), cap taktil bersirip horizontal (*ribbed tactile cap*), dan garis skala kalibrasi analog menyerupai konsol audio/lighting studio.
4. **Instan & Ringan (Zero-Bloat, No Splashscreen, Clean Blank State):**
   Peluncuran instan (< 500 ms) seperti QLC+, tanpa splash screen lambat, dan memulai dalam kondisi bersih/kosong tanpa demo hardcoded.
5. **Anti-Slop (No Emojis & Clean Technical Separators):**
   Bebas total dari emoji kekanak-kanakan di tombol/header. Menggunakan pemisah teknis standar konsol: pipa `|` atau titik dua `:`, tanpa em-dash dekoratif `—`.
6. **Responsif 768p & 1080p:**
   Dirancang proporsional pada resolusi 1366×768 (laptop dev Linux Mint) maupun 1920×1080 (laptop utama Windows 11).

---

## 🎨 2. Palet Warna & Token Desain (Color Tokens)

### 2.1. Primitive Dark Grey & Surface Tokens
| Token | Nilai Hex | Peran & Penggunaan |
| :--- | :--- | :--- |
| `--bg-root` | `#1e2024` | Latar belakang dasar jendela utama (Pure Dark Grey) |
| `--bg-surface` | `#242830` | Latar panel kerja, tab container, dan dialog |
| `--bg-surface-elevated`| `#2d323c` | Latar header bar, widget mengambang, card aktif |
| `--bg-fader-groove` | `#14161a` | Cekungan rel fader slider hitam abu pekat berbayang |
| `--border-subtle` | `#333844` | Garis batas pemisah panel dan grid (1px crisp) |
| `--border-strong` | `#4a5264` | Garis batas elemen aktif / hover / focused input |

### 2.2. Accent & Lighting Glow Tokens (grandMA Inspired)
| Token | Nilai Hex | Peran & Penggunaan |
| :--- | :--- | :--- |
| `--accent-amber` | `#f59e0b` | Emas grandMA untuk Grand Master & Master Dimmer |
| `--accent-cyan` | `#06b6d4` | Cyan neon untuk rel fader DMX channel & visualizer glow |
| `--status-online` | `#22c55e` | Status Art-Net terhubung / streaming aktif (Green) |
| `--status-offline`| `#ef4444` | Status Art-Net terputus / transmisi berhenti (Red) |
| `--status-blackout`| `#000000` | Tombol Blackout industrial hitam pekat berbingkai merah |
| `--text-primary` | `#ffffff` | **Putih Bersih**: Teks utama, judul, nilai fader DMX |
| `--text-secondary`| `#cbd5e1` | Abu-abu terang: Subjudul, status deskripsi, label tab |
| `--text-muted` | `#94a3b8` | Abu-abu redup: Placeholder, nomor DMX unpatched |

### 2.3. Semantic DMX Channel Role Tokens (Address Grid & Fixture Sync)
| Tipe Kanal | Nilai Hex | Warna Visual | Kode Teknis |
| :--- | :--- | :--- | :--- |
| **Dimmer** | `#d97706` | Amber Gold | `DIM` |
| **Red (R)** | `#dc2626` | Deep Bright Red | `RED` |
| **Green (G)** | `#16a34a` | Vivid Green | `GRN` |
| **Blue (B)** | `#2563eb` | Royal Blue | `BLU` |
| **White (W)** | `#f8fafc` | Pure Stage White| `WHT` |
| **Strobe** | `#eab308` | Electric Yellow | `STR` |
| **Pan / Tilt** | `#8b5cf6` | Violet Purple | `PAN / TILT` |
| **Color Macro** | `#ec4899` | Magenta Rainbow | `MACRO` |
| **Unpatched** | `#282c34` | Pure Dark Grey | `—` |

---

## 🏛️ 3. Arsitektur Header Desktop Standar (Windows & Linux)

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Icon ZZ] ZZLUXORA [Untitled.zlx]                                                        —  □  ✕ │  <-- Level 1: OS Title Bar
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ File    Fixture    Editor    Preview    Setting    Help    About                                 │  <-- Level 2: Pure QMenuBar
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [Address] [Analyze] [Result] [Perform] [Page] [Mixer]    │ [ART-NET: IDLE]  [BLACKOUT]   [PLAY]  │  <-- Level 3: Program Bar
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Level 1: OS Window Title Bar
- **Pojok Kiri:** Logo resmi `ZZ` (Arial Black Italic, putih di atas hitam solid murni `#000000`, tanpa glow) + Judul format bersih: `ZZLUXORA [NamaProject.zlx]`.
- Tanpa frame judul palsu di dalam konten jendela untuk memaksimalkan area kerja vertikal.
- **Pojok Kanan:** Tombol standar jendela OS (Minimize, Maximize, Close).

### 3.2. Level 2: Pure Native Main Menu Bar (QMenuBar)
- **Tinggi:** ~30px.
- **Menu Items:** `File`, `Fixture`, `Editor`, `Preview`, `Setting`, `Help`, `About`.
- **Karakteristik:**
  * `File`: Dropdown menu native (`Open Project... (Ctrl+O)`, `Save Project (Ctrl+S)`, `Save As Project... (Ctrl+Shift+S)`, `Exit (Alt+F4)`).
  * `Fixture`, `Editor`, `Preview`, `Setting`, `Help`, `About`: **Membuka Jendela Pop-up Independen (Windowed Mode non-modal)** dengan kontrol *Minimize, Maximize, Close*.

### 3.3. Level 3: Program View Bar (Sejajar Horizontal)
- **Tinggi:** ~38px.
- **Sisi Kiri (Tab Switcher):**
  * Enam tombol tab workspace: `[Address]`, `[Analyze]`, `[Result]`, `[Perform]`, `[Page]`, `[Mixer]`.
  * Tab aktif memiliki border-bottom 3px warna amber grandMA (`#f59e0b`) dan teks putih menyala.
- **Sisi Kanan (Status & Kontrol Panggung):**
  * **Art-Net Status Badge:** Kotak status `[ART-NET: IDLE]` (merah) atau `[ART-NET: TRANSMITTING]` (hijau). Klik badge langsung membuka pop-up Setting.
  * **Tombol Blackout:** Kotak industrial hitam pekat berbingkai merah (`[BLACKOUT]`) untuk mereset Grand Master seketika ke 0.
  * **Tombol Play/Stop Toggle:** 1 tombol tunggal berganti status. Kondisi Idle menampilkan `[PLAY]` (hijau, Art-Net transmisi mati). Begitu diklik -> transmisi aktif dan tombol berubah otomatis menjadi `[STOP]` (merah, streaming 43.07 FPS).

---

## 🎛️ 4. Spesifikasi Komponen Fader Konsol grandMA (Mixer Tab)

Mengacu langsung pada Gambar Referensi **Image #02**, **Image #04**, dan **Image #05**:
- **Cap Fader Taktil (Tactile Ribbed Cap):**
  * Dimensi: Lebar 30px, Tinggi 18px (dioptimalkan untuk responsivitas layar 768p).
  * Bentuk trapesium dengan cekungan ergonomis jari operator.
  * Tekstur sirip horizontal (*ribbed grooves*) di sisi samping cap.
  * Garis indikator putih presisi di bagian tengah cap sebagai penunjuk nilai DMX.
- **Track Slider & Rel LED Menyala (Illuminated Rail):**
  * Cekungan alur hitam pekat berkedalaman inner-shadow.
  * Rel di belakang cap memancarkan cahaya LED lembut vertikal:
    - Master Dimmer: Cahaya Amber Warm Gold (`#f59e0b`).
    - Kanal DMX 1–256: Cahaya Cyan Elektrik (`#06b6d4`).
- **Garis Skala Kalibrasi (Analog Scale Markings):**
  * Skala garis bergradasi di samping track fader (menyerupai fader konsol audio/lighting analog).
  * Penanda garis khusus pada 0%, 50% (127), dan 100% (255).
- **Pembacaan Nilai:**
  * Di bawah fader: Label nomor channel dan box input angka DMX real-time (0–255) yang dapat diketik langsung.

---

## 🖥️ 5. Responsivitas Layar (1366×768 vs 1920×1080)

1. **Laptop Dev (Linux Mint ASUS X407MA - 1366×768):**
   * Ukuran jendela default: `1200 × 680` px (pas di layar tanpa tertutup taskbar OS).
   * Ukuran minimum jendela: `960 × 560` px.
   * Tinggi fader disesuaikan ke `190px` agar tidak memerlukan vertical scroll.
   * Matriks Address 24 kolom menggunakan sel `46×46px` (total lebar 1056px, pas di layar 1366px).
2. **Laptop Utama (Windows 11 Acer Swift 3 - 1920×1080):**
   * Antarmuka otomatis berekspansi memenuhi ruang kerja Full HD.
   * Jendela pop-up (`Preview`, `Fixture List`, `Fixture Editor`, `Setting`) dapat dipindahkan ke monitor sekunder panggung.

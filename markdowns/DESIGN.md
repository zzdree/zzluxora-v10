# 🎨 DESIGN.md — ZZLUXORA v10 Design System & UI Specification

**Sistem Desain & Panduan Antarmuka Konsol Pencahayaan Panggung Generasi Mutakhir**  
*Lead Architect / Senior Developer Edition — Standar Industri grandMA3 & Utilitas QLC+*

---

## 📌 1. Filosofi & Visi Desain

Aplikasi **ZZLUXORA v10** adalah perangkat lunak konsol pencahayaan panggung cerdas (*intelligent stage lighting console*) yang mengemulasi feel dan ketangguhan konsol pencahayaan fisik profesional (MA Lighting grandMA3) ke dalam antarmuka desktop modern.

### Prinsip Inti Rekayasa Desain:
1. **Pure Dark Grey Theme (Kenyamanan FOH):**
   Tidak menggunakan hitam legam OLED (#000000) yang melelahkan mata akibat kontras berlebih, melainkan **Pure Dark Grey** industri elegan (`#1e2024` s.d. `#282c34`). Warna ini menyerupai lempengan bodi baja/aluminium konsol panggung asli.
2. **Tipografi Putih Bersih Kontras Tinggi (High-Contrast White):**
   Seluruh teks nama channel, angka DMX (0–255), label fader, dan menu menggunakan **Putih Bersih** (`#ffffff` / `#f8fafc`) dengan rendering subpixel tajam agar operator FOH dapat membaca parameter dari jarak pandang panggung tanpa salah ketik/baca.
3. **Hardware Tactile Emulation:**
   Fader slider dirancang khusus dengan rel ber-LED menyala lembut (*illuminated groove rail*), cap taktil bersirip horizontal (*ribbed tactile cap*), dan garis skala kalibrasi analog menyerupai konsol audio/lighting studio.
4. **Instan & Ringan (Zero-Bloat, No Splashscreen):**
   Peluncuran instan (< 500 ms) seperti QLC+, siap live performance tanpa jeda booting buatan.

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

### 2.2. Accent & Lighting Glow Tokens (grandMA3 Inspired)
| Token | Nilai Hex | Peran & Penggunaan |
| :--- | :--- | :--- |
| `--accent-amber` | `#f59e0b` | Emas grandMA3 untuk Grand Master & Master Dimmer |
| `--accent-cyan` | `#06b6d4` | Cyan neon untuk rel fader DMX channel & visualizer glow |
| `--status-online` | `#22c55e` | Status Art-Net terhubung / streaming aktif (Green Glow) |
| `--status-offline`| `#ef4444` | Status Art-Net terputus / transmisi berhenti (Red Glow) |
| `--status-blackout`| `#000000` | Tombol Blackout lingkaran hitam pekat berbingkai merah |
| `--text-primary` | `#ffffff` | **Putih Bersih**: Teks utama, judul, nilai fader DMX |
| `--text-secondary`| `#cbd5e1` | Abu-abu terang: Subjudul, status deskripsi, label tab |
| `--text-muted` | `#94a3b8` | Abu-abu redup: Placeholder, nomor DMX unpatched |

### 2.3. Semantic DMX Channel Role Tokens (Address Grid & Fixture Sync)
| Tipe Kanal | Nilai Hex | Warna Visual | Ikon Karakteristik |
| :--- | :--- | :--- | :--- |
| **Dimmer** | `#d97706` | Amber Gold | 💡 Bohlam Lampu / Intensitas |
| **Red (R)** | `#dc2626` | Deep Bright Red | 🔴 Blok Warna Merah |
| **Green (G)** | `#16a34a` | Vivid Green | 🟢 Blok Warna Hijau |
| **Blue (B)** | `#2563eb` | Royal Blue | 🔵 Blok Warna Biru |
| **White (W)** | `#f8fafc` | Pure Stage White| ⚪ Blok Warna Putih Panggung |
| **Strobe** | `#eab308` | Electric Yellow | ⚡ Kilat / Shutter Flash |
| **Pan / Tilt** | `#8b5cf6` | Violet Purple | 🔄 Sumbu Rotasi Moving Head |
| **Color Macro** | `#ec4899` | Magenta Rainbow | 🌈 Roda Warna / Preset Efek |
| **Unpatched** | `#282c34` | Pure Dark Grey | — Nomor kanal di sudut kanan |

---

## 🏛️ 3. Arsitektur 3-Level Header (Standard Desktop Windows & Linux)

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Icon ZZ] ZZLUXORA    D:\projects\church_live\SundayWorship.zlx                          —  □  ✕ │  <-- Level 1: Title Bar
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ File    Fixture    Editor    Preview    Setting    Help    About                                 │  <-- Level 2: Menu Bar
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [Address] [Analyze] [Result] [Perform] [Page] [Mixer]    │ [ART-NET: IDLE]  [○ Blackout]  [▶ Play]│  <-- Level 3: Program Bar
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Level 1: Title Bar (App Bar & Project Path)
- **Tinggi:** 32px.
- **Pojok Kiri:** Logo icon `zz` glowing (20×20px) + Teks brand `ZZLUXORA` (font sans-serif bold, warna putih murni `#ffffff`).
- **Samping Kanan Brand:** Path lengkap file proyek yang sedang aktif (contoh: `D:\projects\worship\SundayWorship.zlx` atau `[Untitled.zlx]`) dengan warna teks `#cbd5e1`.
- **Pojok Kanan:** Tombol standar jendela OS (Minimize, Maximize, Close).

### 3.2. Level 2: Main Menu Bar
- **Tinggi:** 30px.
- **Menu Items:** `File`, `Fixture`, `Editor`, `Preview`, `Setting`, `Help`, `About`.
- **Karakteristik:**
  * `File`: Dropdown menu native (`Open Project (Ctrl+O)`, `Save Project (Ctrl+S)`, `Save As Project (Ctrl+Shift+S)`, `Exit`).
  * `Fixture`, `Editor`, `Preview`, `Setting`, `Help`, `About`: **Membuka Jendela Pop-up Independen (Windowed Mode by default)** dengan tombol minimize, maximize, dan close.

### 3.3. Level 3: Program View Bar (Sejajar Horizontal)
- **Tinggi:** 42px.
- **Sisi Kiri (Tab Switcher):**
  * Enam tombol tab workspace: `[Address]`, `[Analyze]`, `[Result]`, `[Perform]`, `[Page]`, `[Mixer]`.
  * Tab aktif memiliki border-bottom 2px warna amber grandMA3 (`#f59e0b`) dan teks putih menyala.
- **Sisi Kanan (Status & Kontrol Panggung):**
  * **Art-Net Status Badge:** Kapsul pill interaktif `[ART-NET: IDLE]` (merah) atau `[ART-NET: TRANSMITTING]` (hijau). Klik badge langsung membuka pop-up Setting.
  * **Tombol Blackout:** Lingkaran hitam pekat berbingkai merah (`○ Blackout`) untuk mereset Grand Master seketika ke 0.
  * **Tombol Play/Stop Toggle:** 1 tombol tunggal berganti status. Kondisi Idle menampilkan ikon Play hijau (`▶ Play`). Begitu diklik -> transmisi aktif dan tombol berubah otomatis menjadi Stop merah (`■ Stop`).

---

## 🎛️ 4. Spesifikasi Komponen Fader Konsol grandMA3 (Mixer Tab)

Mengacu langsung pada Gambar Referensi **Image #02**, **Image #04**, dan **Image #05**:
- **Cap Fader Taktil (Tactile Ribbed Cap):**
  * Bentuk trapesium dengan cekungan ergonomis jari operator.
  * Tekstur sirip horizontal (*ribbed grooves*) di sisi samping cap.
  * Garis indikator putih presisi di bagian tengah cap sebagai penunjuk nilai DMX.
  * Dimensi Cap: Lebar 32px, Tinggi 22px.
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
   * Seluruh komponen menggunakan stretch factor proporsional.
   * Tab Mixer menggunakan smooth horizontal scrollbar yang ringan.
   * Jendela pop-up (Visualizer, Fixture List) dapat di-docking atau diminimalkan dengan mudah.
2. **Laptop Utama (Windows 11 Acer Swift 3 - 1920×1080):**
   * Antarmuka otomatis berekspansi memenuhi ruang kerja Full HD.
   * Jendela visualizer panggung dapat dipindahkan ke monitor sekunder (eksternal panggung).

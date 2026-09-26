# 🎨 DESIGN.md — ZZLUXORA v10 Design System & UI Specification

**Sistem Desain & Panduan Antarmuka Konsol Pencahayaan Panggung Generasi Mutakhir**  
*Mengadopsi Standar Industri grandMA3, Utilitas QLC+, dan Prinsip Desain Anti-AI Slop*

---

## 📌 1. Filosofi & Visi Desain

Aplikasi **ZZLUXORA v10** adalah perangkat lunak konsol pencahayaan panggung cerdas (*intelligent stage lighting console*) yang dirancang khusus untuk operator pencahayaan live pertunjukan dan ibadah gereja (GIA Deliksari). 

### Prinsip Inti Desain:
1. **Utilitas Panggung Nyata (Mission-Critical Stage Readiness):**
   Antarmuka beroperasi di ruang gelap (*Front of House* / FOH). Kontras tinggi (WCAG AAA), elemen interaktif besar dan tegas, serta bebas dari dekorasi visual yang membingungkan operator saat pertunjukan live.
2. **Estetika grandMA3 Hardware-Emulation:**
   Mengadopsi bahasa visual konsol fisik grandMA3 (MA Lighting GmbH): permukaan logam hitam pekat, fader slider dengan *illuminated track groove* (jalur LED bercahaya di belakang fader cap), *tactile ribbed fader caps*, serta skala kalibrasi garis bertingkat.
3. **Instan & Ringan (Zero-Bloat, No Splashscreen):**
   Aplikasi diluncurkan secara instan (*cold start* < 500 ms) menyerupai QLC+, tanpa splash screen lambat, meminimalkan waktu pemulihan jika terjadi reboot di tengah acara.
4. **Anti-AI Slop:**
   Bebas dari gradien ungu/pink generik AI, sudut lengkung ekstrem yang membuang ruang, atau ikon kartun yang tidak fungsional. Seluruh elemen bergaris tegas 1px solid dengan rasio proporsional.

---

## 🎨 2. Palet Warna & Token Desain (Color Tokens)

### 2.1. Primitive Background & Surface Tokens
| Token | Nilai Hex | Penggunaan |
| :--- | :--- | :--- |
| `--bg-root` | `#0a0c10` | Latar belakang jendela root paling dasar |
| `--bg-surface` | `#11141a` | Latar belakang panel utama, card container, dan tab |
| `--bg-surface-elevated`| `#181c24` | Latar widget mengambang, dialog pop-up, header |
| `--bg-fader-well` | `#07080a` | Cekungan rel fader slider hitam pekat bertekstur |
| `--border-subtle` | `#222733` | Garis batas pemisah panel dan grid (1px solid) |
| `--border-strong` | `#333a4d` | Garis batas kontrol aktif / focused input |

### 2.2. Accent & Lighting Glow Tokens (grandMA3 Inspired)
| Token | Nilai Hex | Penggunaan |
| :--- | :--- | :--- |
| `--accent-amber` | `#f59e0b` | Warna emas khas grandMA3 untuk Grand Master & Dimmer |
| `--accent-cyan` | `#06b6d4` | Warna cyan neon untuk jalur fader track groove & highlight |
| `--status-online` | `#22c55e` | Status Art-Net terhubung / streaming aktif (Green Glow) |
| `--status-offline`| `#ef4444` | Status Art-Net terputus / transmisi berhenti (Red Glow) |
| `--status-warning`| `#eab308` | Status waspada / Onset trigger / Strobe mode |
| `--text-primary` | `#f1f5f9` | Teks utama, pembacaan nilai fader (High Contrast) |
| `--text-secondary`| `#94a3b8` | Label subjudul, nomor DMX unpatched, instruksi |
| `--text-muted` | `#64748b` | Keterangan non-aktif, watermark, placeholder |

### 2.3. Semantic DMX Channel Role Tokens (Address Grid & Fixture Sync)
| Tipe Kanal | Nilai Hex | Warna Visual | Ikon Karakter |
| :--- | :--- | :--- | :--- |
| **Dimmer** | `#d97706` | Amber Gold | 💡 Lampu Bohlam / Intensitas |
| **Red (R)** | `#dc2626` | Deep Bright Red | 🔴 Balok Warna Merah |
| **Green (G)** | `#16a34a` | Vivid Green | 🟢 Balok Warna Hijau |
| **Blue (B)** | `#2563eb` | Royal Blue | 🔵 Balok Warna Biru |
| **White (W)** | `#f8fafc` | Pure Stage White| ⚪ Balok Warna Putih Netral |
| **Strobe** | `#eab308` | Electric Yellow | ⚡ Kilat / Flash Shutter |
| **Pan / Tilt** | `#8b5cf6` | Violet Purple | 🔄 Sumbu Rotasi Moving Head |
| **Color Macro** | `#ec4899` | Magenta Rainbow | 🌈 Roda Warna / Preset |
| **Unpatched** | `#1a1d24` | Industrial Dark Gray| — Nomor kanal di pojok kanan |

---

## 📐 3. Tipografi & Skala Teks (Typography)

Menggunakan font sistem sans-serif monospaced bersih untuk presisi angka panggung:
- **Font Utama:** Inter, Segoe UI, Roboto, sans-serif.
- **Font Numerik & DMX Value:** JetBrains Mono, Fira Code, Consolas, monospace (menghindari angka goyang saat nilai berubah cepat).

| Level | Ukuran Font | Bobot | Line-Height | Penggunaan |
| :--- | :--- | :--- | :--- | :--- |
| Display | 18px | 800 Bold | 22px | Nama Brand `ZZLUXORA`, Judul Modal |
| Heading | 14px | 700 Bold | 18px | Tab Title, Section Header, Dialog Title |
| Subheading | 12px | 600 SemiBold| 16px | Kategori Patch, Label Mixer Fader |
| Body / Value| 11px | 500 Medium | 14px | Pembacaan Angka Fader (0-255), Grid Label |
| Caption | 9px | 600 SemiBold| 11px | Nomor Kanal DMX Pojok (1-256), Status Badge|

---

## 🎛️ 4. Spesifikasi Komponen Khusus (grandMA3 Aesthetic)

### 4.1. Tactile Fader Slider (Mixer Tab)
Mengacu langsung pada Gambar Referensi **Image #02**, **Image #04**, dan **Image #05**:
- **Cap Fader (Knob):**
  * Bentuk trapesium memanjang dengan cekungan ergonomis di tengah (*finger concavity*).
  * Tekstur sirip horizontal (*ribbed tactile grips*) di sisi samping untuk kenyamanan drag & drop sentuhan jari operator.
  * Garis horizontal putih presisi di tengah cap sebagai penunjuk level nilai DMX.
  * Ukuran Cap: Lebar 32px, Tinggi 20px.
- **Track Slider (Groove & Backlit Rail):**
  * Lebar alur (slot): 4px solid dengan kedalaman terbayang (*inner shadow*).
  * Efek *Backlit LED*: Rel di belakang cap memiliki pencahayaan lembut vertikal:
    - Master Dimmer: Cahaya Amber Warm Gold (`#f59e0b`).
    - Kanal RGBW: Cahaya sesuai grup warna (Merah, Hijau, Biru, Putih).
    - Kanal Lain: Cahaya Cyan Elektrik (`#06b6d4`).
- **Skala Garis Kalibrasi (Scale Markings):**
  * Garis-garis tanda level di sisi kiri dan kanan track (menyerupai fader konsol audio/lighting studio analog).
  * Penanda khusus pada 0%, 50% (127), dan 100% (255).
- **Label & Readout Numerik:**
  * Di atas fader: Nama kanal / fixture yang ter-patch.
  * Di bawah fader: Tombol identifikasi kanal + Nilai DMX real-time (0–255) yang dapat diketik langsung.

### 4.2. Header Bar Terpadu (Single Unified Header - No Sidebar)
- Tinggi: 44px tetap (fixed).
- Sisi Kiri:
  * Logo Icon 24x24px (huruf `zz` bold italic glowing).
  * Teks Brand `ZZLUXORA` (13px, bold, tracking +1px).
  * Pemisah vertikal 1px (`#222733`).
  * Menubar Menu Bar: `[File]` `[Fixture]` `[Editor]` `[Preview]` `[Setting]` `[Help]` `[About]`.
- Sisi Kanan:
  * Badge Art-Net: Tombol kapsul pill rounded (`#15181f`), teks status "ART-NET: TRANSMITTING" (Hijau) atau "ART-NET: IDLE" (Merah). Klik badge membuka popup Setting.
  * Tombol Blackout: Lingkaran 32x32px berlatar hitam pekat berbingkai merah peringatan (`#ef4444`).
  * Tombol Play/Stop: Tombol rounded 32x32px berganti dinamis: Play (Segitiga hijau) / Stop (Persegi merah).

### 4.3. Address Grid Sheet (DMX 1–256)
- Matriks kotak 24 kolom horizontal, baris ke bawah bertambah dinamis dengan scrollbar vertikal.
- Ukuran per kotak: Minimal 48x48px (responsif mengikuti lebar jendela).
- Desain kotak kosong: Border 1px `#222733`, latar `#14171f`, nomor DMX di sudut kanan atas dalam warna abu-abu `#64748b`.
- Desain kotak terisi: Border 1px solid menyala, latar belakang solid sesuai warna jenis kanal, teks fungsi (contoh: "RED", "DIM", "STROBE") di posisi tengah dengan font tebal kontras tinggi.

---

## 🖥️ 5. Responsivitas Layar (1366x768 vs 1920x1080)

Aplikasi wajib tampil proporsional tanpa elemen terpotong (*no clipping, no overflow*) pada dua perangkat utama:
1. **Laptop Dev (Linux Mint ASUS X407MA):** 1366 × 768 piksel (768p).
2. **Laptop Utama (Windows 11 Acer Swift 3):** 1920 × 1080 piksel (1080p).

### Aturan Rekayasa Responsif:
- Seluruh panel utama menggunakan `QSplitter` dan layout elastis (`QVBoxLayout` & `QHBoxLayout` dengan stretch factors).
- Tidak menggunakan nilai posisi atau ukuran absolut (`setGeometry` fixed) untuk komponen utama.
- Tab Mixer menggunakan `QScrollArea` dengan scrolling horizontal yang sangat halus (*smooth horizontal scrolling*).
- Jendela visualizer (Preview), Fixture List, dan Fixture Editor dirancang sebagai **Floating Tool Windows** yang bebas digeser, di-maximize, atau dipindahkan ke monitor sekunder (eksternal panggung).

# 🗺️ ROADMAP.md — Big Plan v3 Execution Roadmap (ZZLUXORA v10)

**Peta Jalan Rekayasa Perangkat Lunak & Tahapan Implementasi Terstruktur**  
*Basis: Feedback v3 & Standar Konsol grandMA3 / QLC+*

---

## 📌 Rencana Induk Rekayasa (Big Plan v3 Phases)

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      PETA JALAN PENGEMBANGAN v10                       │
├────────────────────────────────────────────────────────────────────────┤
│  FASE 1: Identitas Visual, Logo 9Router, & Asset Deployment            │
│  FASE 2: Rombak Total Shell (Unified Header Menubar, No Sidebar)       │
│  FASE 3: Implementasi 4 Jendela Pop-up Independen (Floating Windows)   │
│  FASE 4: Restrukturisasi 6 Tab Utama Program (Workspaces)              │
│  FASE 5: Pengujian Software-in-the-Loop (SITL) bersama QLC+ v4 & v5   │
│  FASE 6: Pengujian Hardware Lapangan (ESP32 + PAR LED) & Packaging     │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 🚀 FASE 1: Identitas Visual & Asset Deployment
- [x] **Logo 9Router:** Menghasilkan logo resmi rasio 1:1 huruf `zz` bold italic dengan neon glow cyan-amber pada latar hitam pekat (`ui/assets/logo_zz.png`).
- [x] **Asset Multi-Format:** Mengonversi asset ke multi-size icon (`.ico` 16x16 s.d. 256x256) untuk integrasi window title bar dan taskbar OS.
- [ ] **Aplikasi Identitas:** Mengikat logo resmi ke `QApplication.setWindowIcon()` dan `MainWindow.setWindowTitle("ZZLUXORA - [Project]")`.

---

### 🎛️ FASE 2: Rombak Total Shell (Unified Header Menubar - No Sidebar)
- [ ] **Eliminasi Sidebar:** Menghapus navigasi vertikal samping (`sidebar.py`) guna membebaskan area kerja horizontal.
- [ ] **Header Bar Terpadu:**
  * **Kiri:** Logo icon + Teks `ZZLUXORA` + Menubar (`[File]` `[Fixture]` `[Editor]` `[Preview]` `[Setting]` `[Help]` `[About]`).
  * **Kanan:**
    - Badge status Art-Net (Hijau = Connected, Merah = Disconnected). Interaktif: Klik badge membuka dialog `Setting`.
    - Tombol lingkaran Blackout (menurunkan Grand Master Fader seketika ke 0).
    - Tombol Play/Stop toggle (mengaktifkan/menonaktifkan transmisi UDP paket DMX).
- [ ] **Pemberian Shortcut Global:**
  * `Ctrl+O`: Open Project
  * `Ctrl+S`: Save Project
  * `Ctrl+Shift+S`: Save As Project
  * `Space`: Play/Stop Toggle Art-Net
  * `Escape` / `B`: Blackout

---

### 🪟 FASE 3: Implementasi Jendela Pop-up Mandiri (Floating Windows)
- [ ] **Fixture List Window:**
  * Jendela independen non-modal (dapat di-resize, minimize, maximize, close).
  * Memuat pustaka fixture `.zfx` / JSON.
  * Mendukung aksi **Drag and Drop** langsung ke sel grid Tab Address.
- [ ] **Fixture Definition Editor Window:**
  * Jendela editor profil lampu terisolasi berstandar QLC+ Fixture Editor.
  * Menubar mandiri: File -> Open, Save, Save As (`.zfx`).
  * Form pabrikan, model, channel count, dan tabel pemetaan tipe kanal (Dimmer, RGB, White, Strobe).
- [ ] **Stage Visualizer Window:**
  * Jendela visualizer panggung floating (dapat dipindah ke second monitor / layar FOH).
  * Tab 2D: Tampak depan panggung dengan pendaran cahaya lingkaran RGBW dinamis.
  * Tab 3D: Perspektif ruang panggung dan sudut beam konus lampu.
- [ ] **Network Setting Dialog:**
  * Pemindaian adapter jaringan otomatis.
  * Preset siap pakai: `127.0.0.1` (Localhost SITL), `192.168.4.1` (ESP32 SoftAP), Custom IP.
- [ ] **Help & About Dialogs:**
  * Help: Manual book & tabel lengkap shortcut konsol.
  * About: Informasi akademik resmi Andreas Restuawanta Christwara, Mario Norman Syah, S.Pd., M.Eng., UNNES, dan judul skripsi.

---

### 📑 FASE 4: Restrukturisasi 6 Tab Utama Program (Workspaces)
- [ ] **Tab 1 — Address:**
  * Matriks 256 kanal DMX (maksimal 24 kolom per baris horizontal, scroll vertikal).
  * Warna kotak terisi sinkron dengan tipe kanal Fixture Editor (Merah, Hijau, Biru, Putih, Amber Dimmer, Kuning Strobe).
  * Label kanal di tengah kotak, nomor kanal di sudut kanan atas.
  * Tombol [Clear All Patch] dengan dialog konfirmasi.
  * Tombol & shortcut Undo (`Ctrl+Z`) dan Redo (`Ctrl+Shift+Z`).
- [ ] **Tab 2 — Analyze (Core Skripsi):**
  * Pemuat audio multi-format (`.wav`, `.mp3`, `.flac`, `.ogg`).
  * Input tautan YouTube dengan pengunduh & ekstraksi audio otomatis ke direktori aplikasi.
  * Tombol [Analyze] dan [Remove Song] (dinonaktifkan jika belum ada audio).
  * Analisis asinkron berbasis `QThread`: area analisis diburamkan/dimmed tanpa freeze.
  * Progress bar saintifik dengan teks penjelasan proses DSP real-time.
- [ ] **Tab 3 — Result:**
  * Rekapitulasi analisis audio lagu rohani.
  * Visualisasi koordinat afektif Russell 2D Plane ($V, A$), BPM, akord Chroma, kuadran mood (Praise vs Worship).
  * Tombol [Re-Analyze] dan tombol [Export to Perform].
- [ ] **Tab 4 — Perform:**
  * Manajemen playlist urutan lagu pertunjukan live.
  * Pengaturan section lagu (Intro, Verse, Chorus, Bridge, Outro).
  * Pengaturan durasi transisi (*fade time*) dan kecepatan *chase*.
- [ ] **Tab 5 — Page:**
  * Halaman tombol eksekutor virtual interaktif (ala Virtual Console QLC+ & grandMA3).
  * Preset trigger instan suasana panggung (Praise, Worship, Strobe Flash).
- [ ] **Tab 6 — Mixer:**
  * Meja fader virtual 257 fader: 1 Grand Master Dimmer + 256 Kanal DMX.
  * Desain fader taktil grandMA3: *ribbed tactile cap*, *illuminated groove rail* (LED menyala lembut di belakang slider), dan skala garis kalibrasi analog.
  * Scrolling horizontal mulus (*smooth horizontal scroll*).

---

### 🔄 FASE 5: Verifikasi Software-in-the-Loop (SITL)
- [ ] Pengujian streaming paket DMX 43 FPS dari ZZLUXORA v10 ke QLC+ v4 (`qlc+4`) via Art-Net `127.0.0.1:6454`.
- [ ] Pengujian streaming visualizer 3D ke QLC+ v5 (`qlc+5`).
- [ ] Verifikasi pergerakan slider fader di QLC+ Virtual Console saat fader di ZZLUXORA digeser.

---

### ⚡ FASE 6: Pengujian Hardware Fisik & Deployment
- [ ] Uji coba koneksi Wi-Fi ke SoftAP ESP32 (`192.168.4.1`) di lingkungan laptop ASUS X407MA.
- [ ] Uji coba pengontrolan fisik 4 unit PAR LED RGBW via kabel DMX512 XLR 3-pin.
- [ ] Build installer executable Windows 11 (`.exe` via Inno Setup) di laptop Acer Swift 3.
- [ ] Sinkronisasi penuh ke repositori GitHub `zzdree/zzluxora-v10` sebagai Single Source of Truth.

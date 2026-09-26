# 💾 STATE_MANAGEMENT.md — ZZLUXORA v10 State & Command Architecture

**Spesifikasi Manajemen State Global, Command Pattern (Undo/Redo), & Serialisasi Data**  
*Senior Software Architect Edition — Standar Mutu Produksi & Thread Safety*

---

## 📌 1. Prinsip Manajemen State

Aplikasi **ZZLUXORA v10** mengadopsi prinsip **Single Source of Truth (SSOT)** dalam memori:
1. **Central Project State (`ProjectState`):** Struktur data tunggal di `core/models.py` yang menampung seluruh konfigurasi pertunjukan aktif (patch DMX, audio songlist, hasil analisis MIR, urutan cue panggung, dan status fader mixer).
2. **Command Pattern (`QUndoStack`):** Setiap aksi mutasi state yang dipicu pengguna dibungkus ke dalam objek `QUndoCommand`, memungkinkan fitur **Undo (`Ctrl+Z`)** dan **Redo (`Ctrl+Shift+Z` / `Ctrl+Y`)** berlaku untuk **seluruh program secara global**.
3. **Dirty Flag & Autosave Safeguard:** Perubahan data memicu flag `is_dirty = True` yang secara otomatis memperbarui status pada Title Bar (`ZZLUXORA - [NamaFile]*`) dan mencegah penutupan aplikasi tanpa menyimpan.

---

## 🏛️ 2. Arsitektur Command Pattern (Global Undo/Redo)

```text
               ┌────────────────────────────────────────────────────────┐
               │                GLOBAL QUndoStack                     │
               │   (Terpusat di MainWindow / Dikelola Event Bus)       │
               └───────────┬────────────────────────────────┬───────────┘
                           │                                │
            Execute / Push │                                │ Undo / Redo
                           ▼                                ▼
       ┌───────────────────────────────────────┐   ┌───────────────────────────────┐
       │         PatchFixtureCommand           │   │      FaderChangeCommand       │
       │ • redo(): pasang fixture ke DMX k..N  │   │ • redo(): ubah fader ke val   │
       │ • undo(): kembalikan patch lama       │   │ • undo(): kembalikan nilai fader│
       └───────────────────────────────────────┘   └───────────────────────────────┘
                           ▲                                ▲
                           │                                │
       ┌───────────────────────────────────────┐   ┌───────────────────────────────┐
       │        ClearAllPatchCommand           │   │      ReorderPlaylistCommand   │
       │ • redo(): bersihkan seluruh patch     │   │ • redo(): ubah urutan lagu    │
       │ • undo(): pulihkan seluruh patch lama │   │ • undo(): kembalikan urutan   │
       └───────────────────────────────────────┘   └───────────────────────────────┘
```

### 2.1. Implementasi Command Kunci

#### A. `PatchFixtureCommand` & `ClearAllPatchCommand`
* **Target:** Matriks Tab Address.
* **Mekanisme:**
  - Menyimpan snapshot patch sebelum aksi dijalankan.
  - Saat `redo()` dipanggil: Mengalokasikan kanal DMX $k$ s.d. $k+N-1$, menetapkan warna dan tipe profil lampu, serta memancarkan sinyal pembaruan grid.
  - Saat `undo()` dipanggil: Mengembalikan kondisi alokasi kanal persis seperti sebelum aksi, memulihkan konfigurasi tanpa merusak channel lain.

#### B. `FaderChangeCommand`
* **Target:** Meja Tab Mixer (257 Fader).
* **Mekanisme:**
  - Menyimpan `channel_id`, `old_value`, dan `new_value`.
  - Menerapkan kompresi perintah (*Command Compression via `id()` dan `mergeWith()`*): Jika pengguna menggeser fader berulang kali dalam durasi 500 ms, seluruh pergerakan digabungkan menjadi satu langkah undo tunggal.

#### C. `ReorderPlaylistCommand`
* **Target:** Daftar lagu di Tab Perform.
* **Mekanisme:** Menyimpan urutan indeks playlist sebelum dan sesudah drag-and-drop.

---

## ⚡ 3. Buffer Kanal DMX & State Machine Transmisi Art-Net

### 3.1. Thread-Safe DMX Channel Buffer
- Buffer DMX adalah array byte berukuran 512 elemen (`bytearray(512)`), di mana indeks 0 merepresentasikan DMX Channel 1, dan indeks 511 merepresentasikan DMX Channel 512.
- **Master Dimmer Attenuation:**
  Nilai fisik kanal DMX yang dikirim ke socket dihitung melalui peredaman Grand Master ($M \in [0, 255]$):
  $$\text{DMX}_{\text{out}}[i] = \text{round}\left(\text{DMX}_{\text{raw}}[i] \times \frac{M}{255}\right)$$
- Saat tombol **Blackout** ditekan: Nilai $M$ diset seketika ke 0, sehingga seluruh $\text{DMX}_{\text{out}}$ bernilai 0 tanpa mengubah nilai mentah fader $\text{DMX}_{\text{raw}}$.

### 3.2. State Machine Transmisi Art-Net (Play-Gated)
```text
           [Aplikasi Dibuka: State IDLE]
           (Transmisi DMX MATI - Paket Tidak Dikirim)
                   │
                   ▼
         ┌───────────────────┐
         │    STATE: IDLE    │ <───────────────┐
         │ (Status Merah)    │                 │
         └─────────┬─────────┘                 │
                   │ Klik [PLAY]               │ Klik [STOP]
                   ▼                           │
         ┌───────────────────┐                 │
         │ STATE:TRANSMITTING│ ────────────────┘
         │ (Status Hijau)    │
         │ UDP 43.07 FPS     │
         └─────────┬─────────┘
                   │ Tekan [BLACKOUT]
                   ▼
         ┌───────────────────┐
         │  STATE: BLACKOUT  │
         │ (Grand Master = 0)│ ──> [Kembali ke Transmitting saat fader dinaikkan]
         └───────────────────┘
```

---

## 📁 4. Serialisasi & Deserialisasi Berkas Data

### 4.1. Berkas Proyek (`.zlx`)
- Format berkas `.zlx` adalah JSON yang terstruktur murni Python untuk efisiensi penyimpanan dan kecepatan I/O.
- Disediakan berkas demo resmi di `fixtures/demo_church_worship.zlx`.
- Struktur Data:
  ```json
  {
    "app": "ZZLUXORA",
    "version": "10.0.0",
    "project_name": "Sunday_Worship_Session",
    "target_ip": "127.0.0.1",
    "target_port": 6454,
    "universe": 0,
    "master_dimmer": 255,
    "patches": [ ... ],
    "songs": [ ... ],
    "faders": { ... }
  }
  ```

### 4.2. Berkas Profil Fixture (`.zfx`)
- Format berkas `.zfx` adalah JSON teks murni berstandar QLC+ fixture definition yang dapat dibaca dan diedit langsung.

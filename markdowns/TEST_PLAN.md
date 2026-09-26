# 🧪 TEST_PLAN.md — ZZLUXORA v10 Verification & Quality Assurance Plan

**Rencana Pengujian Komprehensif, Verifikasi Software-in-the-Loop (SITL), & Uji Lapangan**  
*Senior Software Architect Edition — Standar Disiplin TDD & Validasi Ilmiah*

---

## 📌 1. Strategi & Disiplin Verifikasi

Sesuai dengan pedoman **Test-Driven Development (TDD)** dan skill **Verification Before Completion**:
1. **Zero False Positives:** Setiap fitur baru wajib dibuktikan dengan pengujian nyata yang dapat dieksekusi (*executable test*), bukan sekadar asumsi teoritis.
2. **Pengujian Bertingkat (Multi-Tier Testing):**
   * **Level 1 — Unit Testing (`tests/`):** Validasi komputasi matematika murni DSP, pemodelan afektif, dan enkapsulasi biner paket DMX.
   * **Level 2 — SITL Loopback Testing (`tools/`):** Validasi komunikasi antar-aplikasi (ZZLUXORA v10 -> QLC+ v4/v5 via `127.0.0.1:6454`).
   * **Level 3 — GUI & Responsiveness Testing:** Validasi tata letak dan skalabilitas visual pada resolusi 1366×768 (Linux Mint) dan 1920×1080 (Windows 11).
   * **Level 4 — Hardware Field Testing:** Validasi fisik pada modul mikrokontroler ESP32 dan lampu PAR LED RGBW di Gereja GIA Deliksari.

---

## 🔬 2. Matriks Pengujian Unit (Unit Test Suite)

| ID Test | Modul Target | Cakupan Pengujian | Kriteria Lulus |
| :--- | :--- | :--- | :--- |
| **UT-01** | `fft_engine.py` | STFT Hann Windowing ($N=2048, H=512$) | Output shape sesuai matriks frekuensi-waktu, laju $43.07\text{ FPS}$ |
| **UT-02** | `feature_extractor.py` | RMS Energy & Parseval's Theorem | Nilai RMS $\ge 0.0$, akurat merefleksikan dinamika volume audio |
| **UT-03** | `feature_extractor.py` | Spectral Centroid & Brightness | Nilai centroid frekuensi berada dalam rentang $0 \le f_c \le f_{\text{Nyquist}}$ |
| **UT-04** | `feature_extractor.py` | 12-Semitone Chroma STFT | Matriks Chroma berdimensi $12 \times T$ ternormalisasi $\in [0, 1]$ |
| **UT-05** | `feature_extractor.py` | MFCC 13-Koefisien & Mel Filterbank | 13 koefisien per frame audio diekstraksi tanpa NaN/Inf |
| **UT-06** | `emotion_model.py` | Russell 2D Affective Plane | Koordinat $V, A \in [-1.0, 1.0]$, klasifikasi Q1 vs Q3 akurat |
| **UT-07** | `color_engine.py` | HSV ke sRGB & Physical 4-Kanal RGBW | Dekomposisi $W = \min(R,G,B)$ murni anti-washout, $R',G',B',W \in [0, 255]$ |
| **UT-08** | `artnet_sender.py` | Konstruksi Paket ArtDmx 530 Byte | Header 18B tepat (OpCode `0x5000` LE, ProtVer 14 BE), payload 512B |
| **UT-09** | `project_io.py` | Serialisasi & Deserialisasi `.zlx` | Simpan dan muat berkas `.zlx` menghasilkan state identik 100% |
| **UT-10** | `project_io.py` | Parsing Profil Fixture `.zfx` | Profil lampu JSON tervalidasi dengan jumlah kanal dan tipe mapping |
| **UT-11** | `command_undo.py` | Global Undo/Redo Stack | Aksi patch, fader, dan playlist kembali ke kondisi semula saat undo |

---

## 🎛️ 3. Pengujian Software-in-the-Loop (SITL bersama QLC+)

### 3.1. Skenario Pengujian Loopback 127.0.0.1
1. **Langkah 1:** Buka QLC+ v4 (`qlc+4`) atau QLC+ v5 (`qlc+5`) dengan memuat template workspace `/home/zzdree/ANDREAS/zzluxora_test.qxw`.
2. **Langkah 2:** Pastikan Universe 1 di QLC+ terkonfigurasi ke input Art-Net `127.0.0.1` Line 0 (Universe 0) dengan opsi `Passthrough = True`.
3. **Langkah 3:** Jalankan ZZLUXORA v10, klik tombol `[PLAY]` pada Header Bar.
4. **Verifikasi Visual:**
   * Di QLC+ Virtual Console / Simple Desk: Fader kanal 1 s.d. 16 bergerak secara real-time mengikuti pergerakan fader di Tab Mixer ZZLUXORA.
   * Di QLC+ 3D Visualizer (v5): Lampu PAR LED memancarkan warna RGBW dinamis sesuai musik.
5. **Uji Blackout:**
   * Tekan tombol `[BLACKOUT]` di ZZLUXORA: Seluruh fader di QLC+ seketika turun ke 0.
   * Naikkan kembali fader Grand Master: Output pulih seketika.

---

## 🖥️ 4. Pengujian Responsivitas Antarmuka Lintas Layar

### 4.1. Baseline Resolusi 1366×768 (Linux Mint Dev Laptop)
- Pastikan jendela utama muat secara proporsional tanpa ada tombol atau tab yang terpotong.
- Tab Mixer dapat di-scroll horizontal secara mulus (*smooth horizontal scroll*).
- Tab Address menampilkan 24 kolom kotak tanpa horizontal scrollbar yang mengganggu.

### 4.2. Baseline Resolusi 1920×1080 (Windows 11 Main Laptop)
- Seluruh panel berekspansi mengisi ruang Full HD secara elastis.
- Jendela pop-up (`Preview` Visualizer, `Fixture List`, `Fixture Editor`) dapat dipindahkan ke monitor kedua secara independen (*multi-screen workflow*).

---

## ⚡ 5. Rencana Pengujian Lapangan Hardware (Field Test GIA Deliksari)

1. **Jaringan Wi-Fi:** Sambungkan laptop ke SoftAP ESP32 SSID `ZZLUXORA_NODE` (IP Gateway `192.168.4.1`).
2. **Konektivitas Fisik:** Hubungkan output XLR 3-pin ESP32 MAX485 ke rantai *daisy-chain* 4 unit PAR LED RGBW.
3. **Verifikasi Output Panggung:**
   * Putar lagu Praise bertempo cepat (BPM > 120): Output lampu menghasilkan warna cerah enerjik (Kuning/Merah/Cyan) dan responsif terhadap ketukan beat.
   * Putar lagu Worship berirama syahdu (BPM < 80): Output lampu menghasilkan suasana hangat khidmat (Ungu/Biru/Amber Warm White) dengan transisi fade halus.

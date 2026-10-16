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
   * **Level 5 — Audit Adversarial & Regresi:** Setiap defect yang ditemukan audit direproduksi lebih dulu, diperbaiki, lalu dikunci dengan uji regresi. Uji memeriksa isi paket dan state nyata, bukan hanya tampilan, karena defect seperti frame basi pada BLACKOUT dan alamat DMX yang rusak saat simpan lolos dari pengujian yang hanya membaca state antarmuka.

---

## 🔬 2. Matriks Pengujian Unit (Unit Test Suite — 129 Tests Passed)

Per 16 Oktober 2026, seluruh **129 test lulus 100%** dijalankan lewat
`PYTHONPATH=$PWD/tools python3 tools/run_tests_guarded.py`. Wrapper ini menetralkan
`QMessageBox`, `QFileDialog`, dan `QInputDialog` lebih dulu sehingga pengujian tidak
pernah memunculkan dialog di layar operator; sejumlah jalur yang diuji memang berakhir
dengan dialog (mis. penyimpanan berkas).

Suite terdiri dari dua gaya penulisan: 105 test berbasis `unittest` dan 24 test
berbasis `pytest` (yang juga memuat 37 subtest). Perintah lama
`python3 -m unittest discover -s tests -p "test_*.py"` masih sah, tetapi **dapat
memunculkan popup** dan tidak menjalankan modul bergaya pytest.

| ID Suite | Berkas Uji | Cakupan Pengujian | Jumlah Test | Kriteria Lulus |
| :--- | :--- | :--- | :--- | :--- |
| **UT-01** | `test_fft_engine.py` | STFT Hann Windowing ($N=2048, H=512, f_s=22050$) | 3 tests | Output shape matriks frekuensi-waktu tepat, laju $43.07\text{ FPS}$ |
| **UT-02** | `test_feature_extractor.py` | RMS Parseval, Centroid 1 kHz, 13 MFCC Mel+DCT-II, Spectral Flux, Onset Strength, Tempo Autokorelasi 120 BPM | 9 tests | Seluruh fitur numerik finite, flux positif pada transien, tempo $\pm 5$ BPM |
| **UT-03** | `test_audio_loader.py` | Pemuatan berkas WAV, normalisasi mono float32, penanganan format rusak / non-existent | 3 tests | Signal ternormalisasi $\in [-1.0, 1.0]$, error handling tepat |
| **UT-04** | `test_emotion_model.py` | Russell 2D Affective Plane ($V, A$), Krumhansl Mode Ratio, input bobot $0.50/0.30/0.20$ | 2 tests | Koordinat $V, A \in [-1.0, 1.0]$, klasifikasi Q1 vs Q3 akurat |
| **UT-05** | `test_color_engine.py` | Polar atan2 HSV, lantai saturasi $S \ge 0.2$, dekomposisi 4-Kanal Physical RGBW | 2 tests | $W = \min(R,G,B)$ anti-washout, $R',G',B',W \in [0, 255]$ |
| **UT-06** | `test_artnet_sender.py` | Konstruksi Paket ArtDmx 530 Byte (Universe 0, OpCode `0x5000`) | 2 tests | Header 18B tepat little-endian, payload 512B terisi |
| **UT-07** | `test_project_io.py` | Serialisasi `.zlx` simetris (cues Page, port UDP, universe 0, master 255), profil `.zfx` | 5 tests | Simpan & muat berkas `.zlx` identik 100% (round-trip cues/port) |
| **UT-08** | `test_ui_components.py` | Universal Qt6 headless, Impeccable Theme tokens, Mixer, Perform, Preview 2D/3D | 54 tests | Semua modul antarmuka FOH teruji headless tanpa Qt crash |
| **UT-09** | `test_audit_regressions.py` | Regresi audit: anotasi model, konsistensi universe, PCM 24-bit, atomisitas paket Art-Net, skema `.zlx`, socket tertutup | 16 tests | Defect yang ditemukan audit tidak dapat kembali |
| **UT-10** | `test_fixture_editor.py` | Fixture Editor: label bertahan saat jumlah kanal berubah, save tidak merusak, widget tidak bocor, berkas rusak ditolak, write atomik | 7 tests | Round-trip profil `.zfx` setia dan berkas rusak tidak pernah dimuat |
| **UT-11** | `test_analyze_result.py` | Alur analisis: input diam tidak mengklaim nada, metrik dibersihkan setelah gagal, field kosong tidak diisi angka karangan, metrik ternormalisasi 0-1 | 6 tests | Hasil analisis tidak pernah menyajikan bukti yang tidak terukur |
| **UT-12** | `test_preview_lifecycle.py` | Visualizer: timer haze berhenti saat ditutup, proyeksi lantai tidak degenerat, seleksi 2D/3D bersama, geser grup menjaga jarak, pivot panggung kosong | 11 tests | Visualizer tidak menyesatkan operator maupun membocorkan sumber daya |

Jumlah pada tabel di atas menghitung fungsi uji. Angka **129** yang dilaporkan runner mencakup 9 subtest parametrik tambahan, sehingga total yang dieksekusi lebih besar daripada jumlah baris tabel.

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

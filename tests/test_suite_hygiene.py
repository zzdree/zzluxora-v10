"""Menjaga agar test tidak pernah lagi lolos tanpa benar-benar dijalankan.

Sesi 16 Oktober 2026 menemukan tujuh belas test yang ditulis dengan pola
"cat >> berkas test". Perintah itu menaruh test di AKHIR berkas, dan karena
berkas berakhir dengan

    if __name__ == "__main__":
        unittest.main()

test baru mendarat SETELAH blok itu. Kode seperti itu tetap sah secara sintaks
(berada di dalam def), jadi tidak ada yang error, tetapi unittest.TestLoader
hanya mengumpulkan metode dari kelas. Akibatnya test tidak pernah dijalankan dan
suite tetap melaporkan "OK" - laporan yang menyesatkan, karena perbaikan yang
dianggap "terkunci uji" sebenarnya belum diuji sama sekali.

Penjaga ini membuat keadaan itu MUSTAHIL lolos lagi: ia memeriksa setiap berkas
test dan menolak bila ada def test_ yang berada setelah blok main, atau bila ada
test_module_level yang tidak berada di dalam kelas TestCase.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent


class TestSuiteHygiene(unittest.TestCase):
    def _test_files(self):
        return sorted(p for p in TESTS_DIR.glob("test_*.py") if p.name != Path(__file__).name)

    def test_no_test_defined_after_the_main_block(self):
        """Tidak boleh ada def test_ setelah `if __name__ == "__main__"`."""
        pola_main = re.compile(r'if __name__ == ["\']__main__["\']:')
        pelanggar = []
        for path in self._test_files():
            teks = path.read_text(encoding="utf-8")
            cocok = pola_main.search(teks)
            if not cocok:
                continue
            if re.search(r"\n\s+def test_", teks[cocok.end():]):
                nama = re.findall(r"def (test_\w+)", teks[cocok.end():])
                pelanggar.append(f"{path.name}: {nama}")
        self.assertEqual(
            pelanggar, [],
            "test berikut berada setelah blok main sehingga tidak akan pernah "
            "dijalankan oleh unittest:\n  " + "\n  ".join(pelanggar),
        )

    def test_unittest_style_files_keep_tests_inside_a_testcase_class(self):
        """Berkas yang dijalankan unittest tidak boleh punya test di tingkat modul.

        run_tests_guarded.py memilih runner per berkas: yang mengimpor pytest
        dijalankan pytest, sisanya unittest discovery. pytest mengumpulkan
        fungsi test_ tingkat modul, tetapi unittest HANYA mengumpulkan metode
        dari subkelas TestCase. Jadi berkas non-pytest dengan fungsi tingkat
        modul akan melaporkan "OK" sambil melewatkan seluruh testnya, tanpa satu
        pun galat. Berkas bergaya pytest sengaja dilewati di sini karena pola
        itu sah bagi runner-nya.
        """
        pelanggar = []
        for path in self._test_files():
            teks = path.read_text(encoding="utf-8")
            if "import pytest" in teks:
                continue  # dijalankan pytest; fungsi tingkat modul sah
            try:
                pohon = ast.parse(teks)
            except SyntaxError as exc:
                pelanggar.append(f"{path.name}: tidak dapat dibaca ({exc})")
                continue

            # Peta nama kelas -> apakah ia subkelas TestCase
            kelas_testcase = set()
            for simpul in ast.walk(pohon):
                if isinstance(simpul, ast.ClassDef):
                    for basis in simpul.bases:
                        nama_basis = ast.unparse(basis)
                        if "TestCase" in nama_basis:
                            kelas_testcase.add(simpul.name)

            for simpul in pohon.body:
                if isinstance(simpul, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if simpul.name.startswith("test_"):
                        pelanggar.append(
                            f"{path.name}:{simpul.lineno} {simpul.name} berada di "
                            "tingkat modul sehingga unittest akan melewatkannya; "
                            "pindahkan ke dalam kelas TestCase")

            for simpul in ast.walk(pohon):
                if not isinstance(simpul, ast.ClassDef):
                    continue
                if simpul.name not in kelas_testcase:
                    punya_test = [
                        s.name for s in simpul.body
                        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and s.name.startswith("test_")
                    ]
                    if punya_test:
                        pelanggar.append(
                            f"{path.name}:{simpul.lineno} kelas {simpul.name} berisi "
                            f"{punya_test} tetapi bukan subkelas TestCase")

        self.assertEqual(
            pelanggar, [],
            "berkas ini dijalankan unittest (tidak mengimpor pytest), sehingga test "
            "berikut tidak akan pernah dikumpulkan:\n  " + "\n  ".join(pelanggar),
        )

    def test_guarded_runner_collects_a_nonzero_number_of_tests(self):
        """Runner resmi harus benar-benar mengumpulkan test.

        Melindungi dari keadaan yang lebih buruk lagi: bila seluruh berkas gagal
        diimpor, discovery mengembalikan nol test dan suite melaporkan lulus.
        """
        suite = unittest.TestLoader().discover(str(TESTS_DIR), pattern="test_*.py")
        self.assertGreater(
            suite.countTestCases(), 100,
            "discovery menemukan terlalu sedikit test; kemungkinan ada berkas test "
            "yang gagal diimpor dan diam-diam terlewat",
        )

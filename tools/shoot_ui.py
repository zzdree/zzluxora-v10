"""Ambil tangkapan layar setiap tab ZZLUXORA untuk audit visual.

Skrip ini menangkap jendela secara nyata dari dalam Qt (bukan menebak dari kode),
lalu menyimpannya ke /tmp/zz_shots agar dapat diperiksa langsung. Dipakai untuk
menilai tampilan sebelum mengubahnya, dan untuk membandingkan sesudah perubahan.

Penggunaan:
    QT_QPA_PLATFORM=offscreen python3 tools/shoot_ui.py [--outdir /tmp/zz_shots]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import _autodialog_guard  # noqa: F401  (menetralkan dialog sebelum UI diimpor)

from ui.qt_compat import QApplication, QTimer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("/tmp/zz_shots"))
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication(["-platform", "offscreen"])

    from ui.main_window import MainWindow
    win = MainWindow()
    win.resize(1366, 768)
    win.show()

    # Proses event supaya tata letak benar-benar dihitung sebelum ditangkap.
    for _ in range(8):
        app.processEvents()

    tab_names = ["address", "analyze", "result", "perform", "page", "mixer"]
    for index, name in enumerate(tab_names):
        try:
            win._switch_workspace(index)
        except Exception as exc:
            print(f"  lewati {name}: {exc}")
            continue
        for _ in range(6):
            app.processEvents()
        QTimer.singleShot(0, lambda: None)
        app.processEvents()
        path = args.outdir / f"tab_{index + 1}_{name}.png"
        win.grab().save(str(path))
        print(f"  {path}")

    win.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

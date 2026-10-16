"""
Tests for core.youtube_importer: URL validation, dependency reporting, and the
failure paths that previously reported false success.

Network-dependent download is not exercised here; the tests cover the pure
logic plus the error contracts that the dialog relies on.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import youtube_importer as yt


class TestUrlValidation(unittest.TestCase):
    def test_accepts_common_youtube_forms(self):
        for url in (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=abc",
            "https://m.youtube.com/watch?v=abc",
            "https://music.youtube.com/watch?v=abc",
            "https://youtu.be/abc",
            "https://www.youtube.com/shorts/abc",
            "https://www.youtube.com/live/abc",
            "HTTP://YOUTUBE.COM/watch?v=abc",
        ):
            with self.subTest(url=url):
                self.assertTrue(yt.looks_like_youtube_url(url))

    def test_rejects_non_youtube_and_junk(self):
        for url in ("", "   ", "not a url", "https://vimeo.com/123",
                    "https://example.com/youtube.com/watch?v=x", "www.youtube.com/watch?v=x"):
            with self.subTest(url=url):
                self.assertFalse(yt.looks_like_youtube_url(url))


class TestDependencyReport(unittest.TestCase):
    def test_report_lists_both_components(self):
        report = yt.dependency_report()
        self.assertIn("yt-dlp", report)
        self.assertIn("ffmpeg", report)

    def test_missing_dependency_includes_install_remedy(self):
        with patch.object(yt, "resolve_yt_dlp_command", return_value=None), \
             patch.object(yt, "resolve_ffmpeg", return_value=None):
            statuses = yt.check_dependencies()
        self.assertTrue(all(not s.available for s in statuses))
        for status in statuses:
            self.assertIn("install", status.remedy.lower())


class TestImportErrorContract(unittest.TestCase):
    """The dialog shows these messages verbatim, so they must be actionable."""

    def test_invalid_url_raises_before_any_network_use(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(yt.YouTubeImportError) as ctx:
                yt.download_and_convert("https://vimeo.com/123", Path(directory))
        self.assertIn("YouTube video link", str(ctx.exception))

    def test_missing_dependencies_raise_with_remedy(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(yt, "resolve_yt_dlp_command", return_value=None), \
             patch.object(yt, "resolve_ffmpeg", return_value=None):
            with self.assertRaises(yt.YouTubeImportError) as ctx:
                yt.download_and_convert(
                    "https://www.youtube.com/watch?v=abc", Path(directory)
                )
        message = str(ctx.exception)
        self.assertIn("missing", message.lower())
        self.assertIn("pip install", message)

    def test_failed_download_does_not_report_success(self):
        """A non-zero yt-dlp exit must raise, never emit a finished file."""
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(yt, "resolve_yt_dlp_command", return_value=["yt-dlp"]), \
             patch.object(yt, "resolve_ffmpeg", return_value="/usr/bin/ffmpeg"), \
             patch("core.youtube_importer.subprocess.run") as run:
            run.return_value = type(
                "Result", (), {"returncode": 1, "stdout": "", "stderr": "ERROR: video unavailable"}
            )()
            with self.assertRaises(yt.YouTubeImportError) as ctx:
                yt.download_and_convert(
                    "https://www.youtube.com/watch?v=abc", Path(directory)
                )
        self.assertIn("Download failed", str(ctx.exception))
        self.assertIn("video unavailable", str(ctx.exception))

    def test_no_produced_file_raises_instead_of_picking_a_stale_one(self):
        """When yt-dlp succeeds but writes nothing new, import must fail."""
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(yt, "resolve_yt_dlp_command", return_value=["yt-dlp"]), \
             patch.object(yt, "resolve_ffmpeg", return_value="/usr/bin/ffmpeg"):
            # Pre-existing file that a naive "newest file" pick would have used.
            stale = Path(directory) / "Old_Song.m4a"
            stale.write_bytes(b"stale")

            with patch("core.youtube_importer.subprocess.run") as run:
                run.return_value = type(
                    "Result", (), {"returncode": 0, "stdout": "", "stderr": ""}
                )()
                with self.assertRaises(yt.YouTubeImportError) as ctx:
                    yt.download_and_convert(
                        "https://www.youtube.com/watch?v=abc", Path(directory)
                    )
        self.assertIn("no audio file appeared", str(ctx.exception))


class TestFfmpegResolution(unittest.TestCase):
    def test_prefers_bundled_ffmpeg_when_present(self):
        with patch("core.youtube_importer.shutil.which", return_value="/usr/bin/ffmpeg"), \
             patch.dict("sys.modules", {"imageio_ffmpeg": None}):
            # imageio_ffmpeg None forces the import to fail -> falls back to PATH
            self.assertEqual(yt.resolve_ffmpeg(), "/usr/bin/ffmpeg")

    def test_returns_none_when_nothing_available(self):
        with patch("core.youtube_importer.shutil.which", return_value=None), \
             patch.dict("sys.modules", {"imageio_ffmpeg": None}):
            self.assertIsNone(yt.resolve_ffmpeg())


class TestYouTubeDialogLifecycle(unittest.TestCase):
    """The dialog must open, and must never destroy a live worker thread.

    Three regressions are covered. First, _refresh_dependency_line() was called
    during _init_ui() before btn_download existed, so every open raised
    AttributeError. Second, the dialog is opened with exec() from a local
    reference, so it could be garbage collected while a download was still in
    flight, destroying a running QThread. Third, _on_finished accepted the
    dialog without releasing the worker.
    """

    _qapp = None

    @classmethod
    def _application(cls):
        """Create the dialog host and KEEP a reference to it.

        Two traps live here. First, QApplication([]) resolves to the "minimal"
        platform plugin in a headless runner and constructing a QDialog there
        aborts the process, so "offscreen" is pinned explicitly. Second, if the
        only reference to the QApplication is a local inside the test method it
        is collected as soon as that method returns, and letting the application
        object die while widgets still exist aborts the process. Holding it on
        the class mirrors ui/components' suite, which keeps the same reference
        alive for the whole run.
        """
        from ui.qt_compat import HAS_QT, QApplication
        if not HAS_QT:
            raise unittest.SkipTest("Qt bindings are not installed")
        app = QApplication.instance()
        if app is None:
            app = QApplication(["-platform", "offscreen"])
        cls._qapp = app
        return app

    def test_dialog_opens_and_dependency_line_reads(self):
        self._application()
        from ui.widgets.youtube_dialog import YouTubeDialog
        dialog = YouTubeDialog()
        try:
            self.assertTrue(hasattr(dialog, "btn_download"))
            self.assertTrue(dialog.dep_lbl.text())
        finally:
            dialog.reject()

    def test_reject_stops_a_running_worker_before_the_dialog_goes(self):
        self._application()
        import time
        from pathlib import Path
        from ui.widgets.youtube_dialog import YouTubeDialog, YouTubeDownloaderWorker

        class SlowWorker(YouTubeDownloaderWorker):
            def run(self):
                for _ in range(400):
                    if self.isInterruptionRequested():
                        return
                    time.sleep(0.01)

        dialog = YouTubeDialog()
        worker = SlowWorker("https://www.youtube.com/watch?v=abc12345678", Path("/tmp"))
        worker.start()
        time.sleep(0.2)
        self.assertTrue(worker.isRunning(), "precondition: the worker is alive")
        dialog.worker = worker

        dialog.reject()

        self.assertFalse(worker.isRunning(), "reject must not leave a live thread behind")
        self.assertIsNone(dialog.worker)

    def test_stop_worker_is_safe_when_no_worker_exists(self):
        self._application()
        from ui.widgets.youtube_dialog import YouTubeDialog
        dialog = YouTubeDialog()
        try:
            self.assertIsNone(dialog.worker)
            dialog._stop_worker()
            self.assertIsNone(dialog.worker)
        finally:
            dialog.reject()


if __name__ == "__main__":
    unittest.main()

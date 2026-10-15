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


if __name__ == "__main__":
    unittest.main()

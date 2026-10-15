"""
youtube_importer.py - YouTube audio acquisition for ZZLUXORA v10.

Pipeline (deliberately two steps, no reliance on a system ffmpeg):
    1. yt-dlp downloads the native bestaudio stream (.m4a or .webm) with no
       postprocessing, so it works even when ffmpeg is absent.
    2. ffmpeg converts that file to mono PCM WAV at the engine's sample rate.

ffmpeg is resolved from the imageio-ffmpeg package, which ships a static
binary for Linux and Windows, so no system install and no root are required.
A system ffmpeg is used only if the bundled one is unavailable.

This module is Qt-free and standard-library only, so it can be unit tested
without a display.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

# The STFT engine is configured for 22050 Hz mono, so convert to exactly that.
TARGET_SAMPLE_RATE = 22050
DOWNLOAD_TIMEOUT_SEC = 900
CONVERT_TIMEOUT_SEC = 600

# Formats yt-dlp may leave on disk before conversion.
_NATIVE_AUDIO_SUFFIXES = (".m4a", ".webm", ".opus", ".mp4", ".aac", ".ogg", ".mp3", ".wav")

_YOUTUBE_URL_PATTERN = re.compile(
    r"^https?://(?:www\.|m\.|music\.)?"
    r"(?:youtube\.com/(?:watch\?|shorts/|live/|embed/)|youtu\.be/)",
    re.IGNORECASE,
)


class YouTubeImportError(RuntimeError):
    """Raised when a YouTube import cannot be completed.

    The message is written to be shown directly to the operator.
    """


@dataclass
class DependencyStatus:
    """Result of checking one external dependency."""

    name: str
    available: bool
    detail: str
    remedy: str = ""


def looks_like_youtube_url(url: str) -> bool:
    """Return True when the string is plausibly a single YouTube video URL."""
    return bool(_YOUTUBE_URL_PATTERN.match((url or "").strip()))


def resolve_ffmpeg() -> Optional[str]:
    """Return a usable ffmpeg executable path, preferring the bundled binary.

    Order: imageio-ffmpeg bundle first (deterministic across machines), then a
    system ffmpeg on PATH as a fallback.
    """
    try:
        import imageio_ffmpeg  # type: ignore

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and Path(bundled).exists():
            return str(bundled)
    except Exception:
        pass

    return shutil.which("ffmpeg")


# yt-dlp older than this silently fails to extract YouTube signatures. The
# floor is checked because a stale-but-present binary passes a bare presence
# test and then fails deep inside the download with a confusing message.
YTDLP_MIN_VERSION = (2025, 1)


def yt_dlp_version(command: Sequence[str]) -> Optional[tuple]:
    """Return the yt-dlp version as a (year, month) tuple, or None."""
    try:
        result = subprocess.run(
            [*command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    raw = (result.stdout or "").strip().splitlines()
    if not raw:
        return None
    try:
        parts = raw[0].strip().split(".")
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return None


def resolve_yt_dlp_command() -> Optional[List[str]]:
    """Return the command prefix used to invoke yt-dlp.

    Prefers the yt-dlp Python package (so the version tracks requirements.txt),
    then falls back to a system binary.
    """
    try:
        import yt_dlp  # type: ignore  # noqa: F401

        return [sys.executable, "-m", "yt_dlp"]
    except Exception:
        pass

    system = shutil.which("yt-dlp")
    if system:
        return [system]
    return None


def check_dependencies() -> List[DependencyStatus]:
    """Report the availability of every dependency the import path needs."""
    statuses: List[DependencyStatus] = []

    yt = resolve_yt_dlp_command()
    if yt is None:
        statuses.append(
            DependencyStatus(
                name="yt-dlp",
                available=False,
                detail="not found",
                remedy="pip install -U yt-dlp",
            )
        )
    else:
        version = yt_dlp_version(yt)
        if version is not None and version < YTDLP_MIN_VERSION:
            statuses.append(
                DependencyStatus(
                    name="yt-dlp",
                    available=False,
                    detail=f"{version[0]}.{version[1]} is too old (YouTube extraction fails)",
                    remedy="pip install -U yt-dlp",
                )
            )
        else:
            pretty = f"{version[0]}.{version[1]}" if version else "version unknown"
            statuses.append(
                DependencyStatus(
                    name="yt-dlp",
                    available=True,
                    detail=f"{pretty} via {' '.join(yt)}",
                    remedy="pip install -U yt-dlp",
                )
            )

    ff = resolve_ffmpeg()
    statuses.append(
        DependencyStatus(
            name="ffmpeg",
            available=ff is not None,
            detail=ff or "not found",
            remedy="pip install -U imageio-ffmpeg",
        )
    )

    return statuses


def _describe_missing(statuses: Sequence[DependencyStatus]) -> str:
    parts = [f"{s.name} ({s.remedy})" for s in statuses if not s.available]
    return "; ".join(parts)


def _snapshot(directory: Path) -> set:
    """Set of resolved paths currently in the directory (recursively)."""
    return {p.resolve() for p in directory.rglob("*") if p.is_file()}


def download_and_convert(
    url: str,
    output_dir: Path,
    progress: Optional[Callable[[int, str], None]] = None,
    duration_hint_sec: Optional[float] = None,
) -> Path:
    """Download a YouTube track and return a mono 22050 Hz PCM WAV path.

    Raises YouTubeImportError with an operator-facing message on any failure.
    The conversion output is written to output_dir and never overwrites the
    user's existing files silently.
    """

    def emit(percent: int, message: str) -> None:
        if progress is not None:
            progress(percent, message)

    if not looks_like_youtube_url(url):
        raise YouTubeImportError(
            "That does not look like a YouTube video link. Paste a single video URL, "
            "for example https://www.youtube.com/watch?v=... or https://youtu.be/..."
        )

    missing = [s for s in check_dependencies() if not s.available]
    if missing:
        raise YouTubeImportError(
            "Cannot import from YouTube because required components are missing: "
            + _describe_missing(missing)
        )

    yt_command = resolve_yt_dlp_command()
    ffmpeg_exe = resolve_ffmpeg()
    if yt_command is None or ffmpeg_exe is None:  # pragma: no cover - guarded above
        raise YouTubeImportError("YouTube import dependencies are unavailable.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    emit(10, "Validating link...")
    before = _snapshot(output_dir)

    emit(25, "Downloading audio stream...")
    download_command = [
        *yt_command,
        "-f", "bestaudio/best",
        "--no-playlist",
        "--no-part",
        "--newline",
        "-o", str(output_dir / "%(title)s.%(ext)s"),
        url,
    ]
    try:
        download = subprocess.run(
            download_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=DOWNLOAD_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        raise YouTubeImportError(
            f"Download timed out after {DOWNLOAD_TIMEOUT_SEC // 60} minutes. "
            "Check the network connection and try again."
        ) from exc
    except OSError as exc:
        raise YouTubeImportError(f"Could not start yt-dlp: {exc}") from exc

    if download.returncode != 0:
        tail = (download.stderr or download.stdout or "").strip().splitlines()
        detail = tail[-1] if tail else "no diagnostics"
        if "Sign in" in detail or "bot" in detail.lower():
            detail += " (YouTube may be challenging this request; try updating yt-dlp)"
        raise YouTubeImportError(f"Download failed: {detail}")

    produced = [
        p for p in output_dir.rglob("*")
        if p.is_file() and p.resolve() not in before
        and p.suffix.lower() in _NATIVE_AUDIO_SUFFIXES
    ]
    if not produced:
        raise YouTubeImportError(
            "yt-dlp finished but no audio file appeared. The link may be a playlist, "
            "a live stream, or a video without an audio stream."
        )

    # Prefer the largest new file: the audio stream, not a thumbnail or subtitle.
    source = max(produced, key=lambda p: p.stat().st_size)

    emit(65, "Converting to WAV (mono, 22050 Hz)...")
    target = source.with_suffix(".wav")
    if target.exists() or target.resolve() in before:
        counter = 2
        while target.exists():
            target = source.with_name(f"{source.stem} ({counter}).wav")
            counter += 1

    convert_command = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(source),
        "-vn",
        "-ac", "1",
        "-ar", str(TARGET_SAMPLE_RATE),
        "-c:a", "pcm_s16le",
        str(target),
    ]
    try:
        conversion = subprocess.run(
            convert_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=CONVERT_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        raise YouTubeImportError(
            f"Audio conversion timed out after {CONVERT_TIMEOUT_SEC // 60} minutes."
        ) from exc
    except OSError as exc:
        raise YouTubeImportError(f"Could not start ffmpeg: {exc}") from exc

    if conversion.returncode != 0 or not target.exists():
        tail = (conversion.stderr or "").strip().splitlines()
        detail = tail[-1] if tail else "no diagnostics"
        raise YouTubeImportError(f"Audio conversion failed: {detail}")

    # The intermediate native file is no longer needed once the WAV exists.
    try:
        if source != target and source.exists():
            source.unlink()
    except OSError:
        pass

    emit(100, f"Ready: {target.name}")
    return target


def dependency_report() -> str:
    """Human-readable dependency summary, useful for diagnostics and Help."""
    lines: List[str] = []
    for status in check_dependencies():
        mark = "OK" if status.available else "MISSING"
        line = f"{status.name}: {mark} ({status.detail})"
        if not status.available:
            line += f" -> install with: {status.remedy}"
        lines.append(line)
    return "\n".join(lines)


__all__ = [
    "DependencyStatus",
    "YTDLP_MIN_VERSION",
    "YouTubeImportError",
    "check_dependencies",
    "dependency_report",
    "download_and_convert",
    "looks_like_youtube_url",
    "resolve_ffmpeg",
    "resolve_yt_dlp_command",
    "yt_dlp_version",
]

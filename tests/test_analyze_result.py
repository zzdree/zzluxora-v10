"""Regression tests for the Analyze/Result defects found in the 16 Oct 2026 audit.

Covers:
  ANLZ-01  silent or empty audio was reported as a confident musical key
  ANLZ-02  a failed re-analysis left the previous run's metrics on screen
  ANLZ-04  missing result fields rendered as invented measured values
"""

import wave
from array import array
from pathlib import Path

import pytest

from ui.qt_compat import HAS_QT, QApplication

pytestmark = pytest.mark.skipif(not HAS_QT, reason="Qt binding unavailable")


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _write_silent_wav(path: Path, seconds: float = 2.0, sample_rate: int = 22050) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(array("h", [0] * int(sample_rate * seconds)).tobytes())


def _write_empty_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(22050)


def _analyse(path: Path) -> dict:
    from ui.panels.analyze_tab import AudioAnalysisWorker

    captured = {}
    worker = AudioAnalysisWorker(str(path))
    worker.analysis_finished.connect(lambda res: captured.update(res))
    worker.run()
    return captured


def test_silent_audio_does_not_claim_a_musical_key(app, tmp_path):
    """ANLZ-01: two seconds of digital silence used to report 'C Major (Praise)'."""
    path = tmp_path / "silent.wav"
    _write_silent_wav(path)

    result = _analyse(path)
    key = str(result.get("chroma_key", ""))

    assert "Major" not in key and "Minor" not in key, f"silence claimed a key: {key!r}"
    assert "No tonal content" in key
    assert result.get("quadrant") == "Idle", "silence must not get a worship quadrant"


def test_empty_audio_does_not_claim_a_musical_key(app, tmp_path):
    """ANLZ-01: a zero-sample file also produced a confident key."""
    path = tmp_path / "empty.wav"
    _write_empty_wav(path)

    result = _analyse(path)
    key = str(result.get("chroma_key", ""))

    assert "Major" not in key and "Minor" not in key
    assert result.get("quadrant") == "Idle"


def test_failed_analysis_clears_previous_metrics(app):
    """ANLZ-02: the stats card must not keep the earlier track's numbers."""
    from ui.panels.analyze_tab import AnalyzeTab

    tab = AnalyzeTab()
    tab._on_analysis_finished({
        "title": "Previous Track", "bpm": 71.8, "rms": 0.691,
        "valence": 0.26, "arousal": -0.17, "frames_count": 100,
        "duration_sec": 10.0, "fps_rate": 43.07, "quadrant": "Q4_PEACE_INTIMACY",
        "palette": {"R": 10, "G": 20, "B": 30, "W": 0}, "chroma_key": "G Major",
        "mfcc_density": 0.5, "spectral_flux": 0.1, "spectral_centroid": 2000.0,
    })
    assert "Previous Track" in tab.stats_label.text()

    tab._on_analysis_failed("cannot decode")

    text = tab.stats_label.text()
    assert "Analysis failed" in text
    assert "Previous Track" not in text, "stale track name must be cleared"
    assert "71.8" not in text, "stale BPM must be cleared"


def test_missing_result_fields_show_unknown_not_numbers(app):
    """ANLZ-04: absent fields must not render as plausible measurements."""
    from ui.panels.result_tab import ResultTab

    tab = ResultTab()
    tab.load_analysis_result({"title": "PartialOnly"})

    rendered = [
        tab.table.item(row, 1).text()
        for row in range(tab.table.rowCount())
        if tab.table.item(row, 1)
    ]
    joined = " | ".join(rendered)

    for invented in ("1850", "120.0 BPM", "0.500", "0.150", "R:255 G:255 B:255"):
        assert invented not in joined, f"invented value {invented!r} was rendered"

    assert "- (not measured)" in joined
    assert not tab.btn_export.isEnabled(), "Export must be disabled without real data"


def test_complete_result_still_renders_and_enables_export(app):
    """The placeholder work must not break a genuine, complete result."""
    from ui.panels.result_tab import ResultTab

    tab = ResultTab()
    tab.load_analysis_result({
        "title": "Real Track", "bpm": 72.0, "valence": 0.2, "arousal": -0.1,
        "rms": 0.5, "frames_count": 500, "duration_sec": 12.0, "fps_rate": 43.07,
        "quadrant": "Q4_PEACE_INTIMACY", "spectral_centroid": 2100.0,
        "chroma_key": "D Minor (Worship character)",
        "mfcc_density": 0.42, "spectral_flux": 0.08,
        "palette": {"R": 20, "G": 40, "B": 80, "W": 10},
    })

    joined = " | ".join(
        tab.table.item(row, 1).text()
        for row in range(tab.table.rowCount())
        if tab.table.item(row, 1)
    )
    assert "72.0 BPM" in joined
    assert "2100.0 Hz" in joined
    assert "R:20 G:40 B:80 W:10" in joined
    assert tab.btn_export.isEnabled()


def test_texture_metrics_are_normalized(app, tmp_path):
    """ANLZ-03: the Result tab labels these as indices, so they must be 0-1.

    The worker used to report the engine's raw unbounded quantities: spectral
    flux summed per frame (0 to about 258) and the raw MFCC contrast mean (about
    24 to 48). Read on screen as an "index" and a "density", those numbers invite
    the wrong interpretation in a thesis table.
    """
    from pathlib import Path as _Path

    repo_root = _Path(__file__).resolve().parent.parent
    audio = sorted((repo_root / "data" / "audio").glob("*.wav"))
    if not audio:
        pytest.skip("no bundled audio to analyse")

    result = _analyse(audio[0])

    mfcc = result.get("mfcc_density")
    flux = result.get("spectral_flux")
    assert mfcc is not None and 0.0 <= mfcc <= 1.0, f"mfcc_density out of range: {mfcc}"
    assert flux is not None and 0.0 <= flux <= 1.0, f"spectral_flux out of range: {flux}"

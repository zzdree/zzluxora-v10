"""Regression tests for Stage Visualizer defects found in the 16 Oct 2026 audit.

Covers:
  PREVIEW-5  the 30 FPS haze animation kept running after the window was closed
"""

import pytest

from ui.qt_compat import HAS_QT, QApplication

pytestmark = pytest.mark.skipif(not HAS_QT, reason="Qt binding unavailable")


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _visualizer_with_fixture():
    from ui.main_window import MainWindow

    win = MainWindow()
    win.tab_address._on_fixture_dropped(
        1,
        {"name": "PAR-A", "channels": [
            {"type": t, "label": t.upper()}
            for t in ("dimmer", "red", "green", "blue", "empty", "program", "speed", "empty")
        ]},
    )
    win._on_open_visualizer()
    return win, win.win_visualizer


def test_haze_timer_stops_when_visualizer_closes(app):
    """PREVIEW-5: closing the window must stop the animation timer."""
    win, panel = _visualizer_with_fixture()
    canvas = panel.canvas_3d

    canvas.set_haze_enabled(True)
    app.processEvents()
    assert canvas.anim_timer.isActive(), "haze should animate while visible"

    panel.close()
    app.processEvents()
    assert not canvas.anim_timer.isActive(), \
        "the haze timer must not keep repainting a closed window"

    win.close()


def test_haze_timer_resumes_when_visualizer_reopens(app):
    """Haze is a live effect, so reopening must restore the animation."""
    win, panel = _visualizer_with_fixture()
    canvas = panel.canvas_3d

    canvas.set_haze_enabled(True)
    app.processEvents()
    panel.close()
    app.processEvents()
    assert not canvas.anim_timer.isActive()

    panel.show()
    app.processEvents()
    assert canvas.anim_timer.isActive(), "haze must animate again once the window is visible"
    assert canvas.haze_enabled, "the haze setting itself must survive a close/open cycle"

    win.close()


def test_haze_timer_stays_off_when_haze_is_disabled(app):
    """A closed window with haze off must not restart the timer on reopen."""
    win, panel = _visualizer_with_fixture()
    canvas = panel.canvas_3d

    canvas.set_haze_enabled(False)
    panel.close()
    app.processEvents()
    panel.show()
    app.processEvents()

    assert not canvas.anim_timer.isActive()
    assert not canvas.haze_enabled

    win.close()

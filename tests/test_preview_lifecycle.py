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


def test_floor_projection_is_not_degenerate_at_default_camera(app):
    """VIZ3D-01: pitch must not be exactly 0 or the floor becomes invisible.

    At pitch 0, sin(pitch) is 0, so every vertex with y == 0 lands on the same
    scanline and the floor quad, beam cone and floor pool all collapse to
    zero-area polygons that draw nothing.
    """
    import math

    from ui.panels.preview_tab import Stage3DCanvas

    canvas = Stage3DCanvas()
    floor = [(0, 0, 0), (320, 0, -140), (-320, 0, -140), (260, 0, 180), (-260, 0, 180)]

    def scanline_count() -> int:
        rows = {round(canvas.project(*p, 400.0, 320.0)[1], 6) for p in floor}
        return len(rows)

    assert canvas.pitch != 0.0, "default pitch must not be exactly zero"
    assert scanline_count() > 1, "the floor must span more than one scanline"

    canvas.reset_camera()
    assert canvas.pitch != 0.0, "reset_camera must not flatten the projection"
    assert scanline_count() > 1

    canvas.pitch = math.radians(35)
    canvas.reset_camera()
    assert scanline_count() > 1, "reset after an orbit must stay non-degenerate"


def test_selection_is_shared_between_2d_and_3d_canvases(app):
    """VIZ3D-03: the drawer sliders broadcast to both canvases.

    With private selection sets, a click in one view left a stale set in the
    other, so a slider drag repositioned fixtures the operator never selected.
    """
    win, panel = _visualizer_with_fixture()
    canvas_2d, canvas_3d = panel.canvas_2d, panel.canvas_3d

    canvas_2d.selected_ids = {1}
    canvas_2d.selection_changed.emit([1])
    assert canvas_2d.selected_ids == canvas_3d.selected_ids

    canvas_3d.selected_ids = {2}
    canvas_3d.selection_changed.emit([2])
    assert canvas_2d.selected_ids == canvas_3d.selected_ids == {2}, \
        "a 3D click must update the 2D selection"

    canvas_2d.selected_ids = {1, 2}
    canvas_2d.selection_changed.emit([1, 2])
    assert canvas_3d.selected_ids == {1, 2}, "multi-select must mirror too"

    win.close()

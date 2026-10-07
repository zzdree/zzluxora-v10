"""
preview_tab.py | Standalone Floating Stage Visualizer Window (2D & 3D with Haze/Smoke)
Provides high-fidelity stage lighting simulation with dynamic RGBW PAR LED beam glows,
3D perspective volumetric beams, multi-cell LED lens emitters, adjustable beam spread,
overhead truss rigging, atmospheric haze/smoke FX, full mouse camera controls (orbit, pan, zoom),
center-aligned 2D/3D layout, multi-selection (Shift+Click), and side drawer controls.
"""

from __future__ import annotations
import math
import random
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpinBox, QSlider, QStackedWidget,
    Qt, QPoint, QPointF, QRectF, Signal, QPainter, QColor, QPen, QPolygonF,
    QRadialGradient, QLinearGradient, QBrush, QFont, QTimer, QIcon
)
from ui.styles import Theme, CONSOLE_QSS


# -----------------------------------------------------------------------------
# 1. 2D STAGE CANVAS (FRONT VIEW WITH CENTER-ALIGNED VERTICAL & HORIZONTAL LAYOUT)
# -----------------------------------------------------------------------------
class Stage2DCanvas(QFrame if HAS_QT else object):
    """Front-view 2D Stage Canvas with RGBW beam projection, halos, floor bounce, and click selection."""
    fixture_selected = Signal(int)       # Primary selected fixture ID
    selection_changed = Signal(list)     # List of selected fixture IDs

    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Theme.SURFACE_VOID}; border: 1px solid {Theme.BORDER_SUBTLE}; border-radius: 6px;")

        # Starts empty by default (Clean initial state for untitled project)
        self.fixtures: list[dict] = []
        self.selected_ids: set[int] = set()

        # Global stage pivot offsets
        self.pivot_x = 0
        self.pivot_y = 0

    def set_fixtures(self, fixtures_data: list[dict]) -> None:
        """Loads patched fixtures and auto-arranges them center-aligned in 2D."""
        self.fixtures = []
        for idx, fix in enumerate(fixtures_data):
            self.fixtures.append({
                "id": fix.get("id", idx + 1),
                "name": fix.get("name", f"Fixture #{idx + 1}"),
                "start_channel": fix.get("start_channel", 1),
                "channels": fix.get("channels", []),
                "base_x": 0,
                "base_y": 0,
                "offset_x": 0,
                "offset_y": 0,
                "r": 255,
                "g": 180,
                "b": 0,
                "w": 40,
                "dim": 240,
            })
        self.selected_ids = {self.fixtures[0]["id"]} if self.fixtures else set()
        self.recompute_layout()
        self.update()

    def recompute_layout(self) -> None:
        """Computes center-aligned horizontal and vertical positions for active fixtures."""
        n = len(self.fixtures)
        if n == 0:
            return

        w = max(400, self.width() if self.width() > 100 else 800)
        h = max(350, self.height() if self.height() > 100 else 550)

        # Centered both horizontally and vertically
        center_x = w / 2.0 + self.pivot_x
        center_y = (h / 2.0) - 20 + self.pivot_y
        spacing = min(150.0, max(85.0, (w - 140.0) / max(1, n)))

        for i, fix in enumerate(self.fixtures):
            fix["base_x"] = int(center_x + (i - (n - 1) / 2.0) * spacing)
            fix["base_y"] = int(center_y)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.recompute_layout()

    def set_selected_offsets(self, ox: int, oy: int) -> None:
        """Updates offset position for selected fixtures."""
        if not self.selected_ids:
            self.pivot_x = ox
            self.pivot_y = oy
            self.recompute_layout()
        else:
            for fix in self.fixtures:
                if fix["id"] in self.selected_ids:
                    fix["offset_x"] = ox
                    fix["offset_y"] = oy
        self.update()

    def align_fixtures_horizontal(self) -> None:
        """Aligns selected (or all) fixtures to a horizontal line."""
        targets = [f for f in self.fixtures if f["id"] in self.selected_ids] if self.selected_ids else self.fixtures
        if not targets: return
        avg_oy = sum(f["offset_y"] for f in targets) // len(targets)
        for f in targets:
            f["offset_y"] = avg_oy
        self.update()

    def align_fixtures_vertical(self) -> None:
        """Aligns selected (or all) fixtures to a vertical line."""
        targets = [f for f in self.fixtures if f["id"] in self.selected_ids] if self.selected_ids else self.fixtures
        if not targets: return
        avg_ox = sum(f["offset_x"] for f in targets) // len(targets)
        for f in targets:
            f["offset_x"] = avg_ox
        self.update()

    def update_dmx_frame(self, dmx_channels: list[int] | bytearray) -> None:
        """Parses DMX channels dynamically based on each fixture's start channel and channel types."""
        if not self.fixtures:
            return

        for fix in self.fixtures:
            start = fix["start_channel"] - 1
            channels = fix.get("channels", [])

            dim = 255
            r = 0
            g = 0
            b = 0
            w = 0

            if channels:
                for ch in channels:
                    idx = ch.get("channel", 1) - 1
                    ctype = ch.get("type", "").lower()
                    if idx < len(dmx_channels):
                        val = dmx_channels[idx]
                        if ctype == "dimmer": dim = val
                        elif ctype == "red": r = val
                        elif ctype == "green": g = val
                        elif ctype == "blue": b = val
                        elif ctype == "white": w = val
            else:
                if start + 4 < len(dmx_channels):
                    dim = dmx_channels[start]
                    r = dmx_channels[start + 1]
                    g = dmx_channels[start + 2]
                    b = dmx_channels[start + 3]
                    w = dmx_channels[start + 4]

            fix["dim"] = dim
            fix["r"] = r
            fix["g"] = g
            fix["b"] = b
            fix["w"] = w

        self.update()

    def mousePressEvent(self, event) -> None:
        # Left click selects fixture. Shift+Click enables multi-selection.
        # Position is never altered by mouse dragging.
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            clicked_id = None
            for fix in self.fixtures:
                fx = fix["base_x"] + fix["offset_x"]
                fy = fix["base_y"] + fix["offset_y"]
                if (pos.x() - fx)**2 + (pos.y() - fy)**2 <= 30**2:
                    clicked_id = fix["id"]
                    break

            if clicked_id is not None:
                if event.modifiers() & Qt.ShiftModifier:
                    if clicked_id in self.selected_ids:
                        self.selected_ids.remove(clicked_id)
                    else:
                        self.selected_ids.add(clicked_id)
                else:
                    self.selected_ids = {clicked_id}

                self.fixture_selected.emit(clicked_id)
                self.selection_changed.emit(list(self.selected_ids))
                self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        floor_y = h - 45

        # Vertical Center for Fixtures & Overhead Truss Rigging
        center_y = (h / 2.0) - 20 + self.pivot_y
        truss_y = center_y - 48

        # 1. Truss Rigging Bar at Top
        pen_truss_main = QPen(QColor(Theme.RIGGING_TRUSS_MAIN), 6)
        painter.setPen(pen_truss_main)
        painter.drawLine(20, int(truss_y), w - 20, int(truss_y))

        # Truss diagonal cross bracing
        pen_truss_sub = QPen(QColor(Theme.RIGGING_TRUSS_SUB), 2)
        painter.setPen(pen_truss_sub)
        for tx in range(25, w - 25, 40):
            painter.drawLine(tx, int(truss_y - 8), tx + 20, int(truss_y + 8))
            painter.drawLine(tx + 20, int(truss_y + 8), tx + 40, int(truss_y - 8))

        # 2. Stage Floor Platform
        painter.fillRect(0, floor_y, w, h - floor_y, QColor(Theme.SURFACE_OBSIDIAN))
        pen_floor = QPen(QColor(Theme.BORDER_STRONG), 2)
        painter.setPen(pen_floor)
        painter.drawLine(0, floor_y, w, floor_y)

        # 3. Empty Stage Message if no fixtures patched
        if not self.fixtures:
            painter.setFont(QFont("Inter", 11, QFont.Medium))
            painter.setPen(QColor(Theme.TEXT_MUTED))
            painter.drawText(
                QRectF(0, h / 2 - 20, w, 40),
                Qt.AlignCenter,
                "Stage Ready • Patch fixtures in Address tab to visualize lighting"
            )
            painter.end()
            return

        # 4. Render Fixtures, Volumetric Beams, Floor Pools, and Cables
        for fix in self.fixtures:
            fx = fix["base_x"] + fix["offset_x"]
            fy = fix["base_y"] + fix["offset_y"]
            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])
            dim = fix["dim"] / 255.0

            # Power/DMX Drop Cable from Truss to Fixture
            painter.setPen(QPen(QColor(Theme.SURFACE_TROUGH), 2))
            painter.drawLine(fx, int(truss_y), fx, fy - 18)

            # A. Light Conical Beam Projection downwards
            if dim > 0.05:
                beam_grad = QLinearGradient(fx, fy, fx, floor_y)
                beam_color_top = QColor(r, g, b, int(180 * dim))
                beam_color_bottom = QColor(r, g, b, int(25 * dim))
                beam_grad.setColorAt(0.0, beam_color_top)
                beam_grad.setColorAt(0.7, QColor(r, g, b, int(50 * dim)))
                beam_grad.setColorAt(1.0, beam_color_bottom)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(beam_grad))

                beam_path = [
                    QPoint(fx - 14, fy + 8),
                    QPoint(fx + 14, fy + 8),
                    QPoint(fx + 75, floor_y),
                    QPoint(fx - 75, floor_y),
                ]
                painter.drawPolygon(beam_path)

                # Floor light reflection pool (elliptical bounce)
                floor_rad = QRadialGradient(fx, floor_y + 8, 75)
                floor_rad.setColorAt(0.0, QColor(r, g, b, int(150 * dim)))
                floor_rad.setColorAt(0.6, QColor(r, g, b, int(50 * dim)))
                floor_rad.setColorAt(1.0, QColor(r, g, b, 0))
                painter.setBrush(QBrush(floor_rad))
                painter.drawEllipse(fx - 75, floor_y - 8, 150, 24)

            # B. Glowing Lens Halo
            rad_grad = QRadialGradient(fx, fy, 45)
            rad_grad.setColorAt(0.0, QColor(r, g, b, int(230 * dim)))
            rad_grad.setColorAt(0.4, QColor(r, g, b, int(110 * dim)))
            rad_grad.setColorAt(1.0, QColor(r, g, b, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(rad_grad))
            painter.drawEllipse(fx - 45, fy - 45, 90, 90)

            # C. Fixture Casing Housing & Selection Highlight
            is_sel = fix["id"] in self.selected_ids
            if is_sel:
                # Cyan Selection Ring
                painter.setPen(QPen(QColor(Theme.ACCENT_CYAN), 2.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(fx - 23, fy - 23, 46, 46)

            painter.setPen(QPen(QColor(Theme.BORDER_STRONG), 1.5))
            painter.setBrush(QColor(Theme.FIXTURE_BODY))
            painter.drawEllipse(fx - 18, fy - 18, 36, 36)

            # D. PAR LED Multi-Cell Lens Array (Matrix of LED emitters)
            painter.setPen(Qt.NoPen)
            center_color = QColor(r, g, b, int(255 * max(0.2, dim)))
            painter.setBrush(center_color)
            painter.drawEllipse(fx - 11, fy - 11, 22, 22)

            # Concentric LED Lens Beads
            painter.setBrush(QColor(255, 255, 255, int(200 * max(0.25, dim))))
            bead_r = 1.8
            for angle in [0, 60, 120, 180, 240, 300]:
                rad = math.radians(angle)
                bx = fx + math.cos(rad) * 6
                by = fy + math.sin(rad) * 6
                painter.drawEllipse(QPointF(bx, by), bead_r, bead_r)
            painter.drawEllipse(QPointF(fx, fy), 2.2, 2.2)

            # E. Telemetry: ONLY Fixture Name
            painter.setFont(QFont("Inter", 8, QFont.Bold))
            painter.setPen(QColor(Theme.TEXT_PRIMARY))
            painter.drawText(QRectF(fx - 70, fy + 22, 140, 16), Qt.AlignCenter, fix["name"])

        painter.end()


# -----------------------------------------------------------------------------
# 2. 3D STAGE CANVAS (INVERTED ORBIT, ZOOM LIMITS, PAN MOVE, FRONT EYE-LEVEL DEFAULT)
# -----------------------------------------------------------------------------
class Stage3DCanvas(QFrame if HAS_QT else object):
    """
    True Perspective 3D Stage Visualizer.
    Features overhead aluminum box-truss, 3D PAR LED fixture housings with lens array,
    adjustable beam spread angle, perspective conical volumetric beams, floor pools,
    uninhibited inverted mouse orbit, bounded zoom, right-drag pan, eye-level front default,
    center-aligned dynamic layout, and atmospheric haze FX.
    """
    fixture_selected = Signal(int)
    selection_changed = Signal(list)

    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Theme.SURFACE_VOID}; border: 1px solid {Theme.BORDER_SUBTLE}; border-radius: 6px;")

        # Default Camera: Eye-Level Straight Front Perspective View
        self.yaw = 0.0                      # Straight ahead (0.0 rad)
        self.pitch = 0.0                    # Eye level (0.0 rad)
        self.cam_distance = 600.0           # Zoom distance (bounded 200..1200)
        self.pan_x = 0.0                    # Camera horizontal pan
        self.pan_y = 0.0                    # Camera vertical pan

        # Drag state
        self.is_orbiting = False
        self.is_panning = False
        self.last_mouse_pos = QPoint()
        self.press_pos = QPoint()

        # Global stage pivot offsets
        self.pivot_x = 0
        self.pivot_y = 0
        self.pivot_z = 0

        # Multi-selection support
        self.selected_ids: set[int] = set()

        # Starts empty by default (Clean initial state for untitled project)
        self.fixtures_3d: list[dict] = []

        # Atmospheric Haze / Smoke Simulation State (Default: OFF per feedback)
        self.haze_enabled = False
        self.haze_density = 0.5
        self.smoke_particles = []
        for _ in range(32):
            self.smoke_particles.append({
                "x": random.uniform(-300, 300),
                "y": random.uniform(20, 220),
                "z": random.uniform(-100, 160),
                "radius": random.uniform(40, 95),
                "speed_x": random.uniform(0.3, 0.9),
                "alpha": random.uniform(10, 32),
                "phase": random.uniform(0, math.pi * 2),
            })

        # Animation timer for haze/smoke movement (30 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(33)
        self.anim_timer.timeout.connect(self._on_animation_tick)

    def set_fixtures(self, fixtures_data: list[dict]) -> None:
        """Loads patched fixtures and auto-arranges them center-aligned in 3D."""
        self.fixtures_3d = []
        for idx, fix in enumerate(fixtures_data):
            self.fixtures_3d.append({
                "id": fix.get("id", idx + 1),
                "name": fix.get("name", f"Fixture #{idx + 1}"),
                "start_channel": fix.get("start_channel", 1),
                "channels": fix.get("channels", []),
                "base_x": 0.0,
                "base_y": 240.0,
                "base_z": 0.0,
                "offset_x": 0.0,
                "offset_y": 0.0,
                "offset_z": 0.0,
                "rot_x": 0.0,       # Pitch tilt in degrees
                "rot_y": 0.0,       # Yaw pan in degrees
                "rot_z": 0.0,       # Roll in degrees
                "beam_angle": 28.0, # Lens spread angle in degrees (15-60)
                "r": 255,
                "g": 180,
                "b": 0,
                "w": 40,
                "dim": 240,
            })
        self.selected_ids = {self.fixtures_3d[0]["id"]} if self.fixtures_3d else set()
        self.recompute_layout()
        self.update()

    def recompute_layout(self) -> None:
        """Computes center-aligned positions for 3D stage fixtures."""
        n = len(self.fixtures_3d)
        if n == 0:
            return

        spacing_3d = 120.0
        base_y = 240.0 + self.pivot_y
        base_z = 0.0 + self.pivot_z

        for i, fix in enumerate(self.fixtures_3d):
            fix["base_x"] = (i - (n - 1) / 2.0) * spacing_3d + self.pivot_x
            fix["base_y"] = base_y
            fix["base_z"] = base_z

    def set_selected_offsets(self, ox: float, oy: float, oz: float) -> None:
        """Applies position offsets to selected fixtures."""
        if not self.selected_ids:
            self.pivot_x = int(ox)
            self.pivot_y = int(oy)
            self.pivot_z = int(oz)
            self.recompute_layout()
        else:
            for fix in self.fixtures_3d:
                if fix["id"] in self.selected_ids:
                    fix["offset_x"] = ox
                    fix["offset_y"] = oy
                    fix["offset_z"] = oz
        self.update()

    def set_selected_rotations(self, rx: float, ry: float, rz: float) -> None:
        """Applies 3-axis rotation (Pitch, Yaw, Roll) to selected fixtures."""
        for fix in self.fixtures_3d:
            if not self.selected_ids or fix["id"] in self.selected_ids:
                fix["rot_x"] = rx
                fix["rot_y"] = ry
                fix["rot_z"] = rz
        self.update()

    def set_selected_beam_angle(self, angle: float) -> None:
        """Sets the optical lens beam spread angle in degrees."""
        for fix in self.fixtures_3d:
            if not self.selected_ids or fix["id"] in self.selected_ids:
                fix["beam_angle"] = angle
        self.update()

    def align_fixtures_horizontal(self) -> None:
        """Aligns selected (or all) 3D fixtures horizontally (same Y height)."""
        targets = [f for f in self.fixtures_3d if f["id"] in self.selected_ids] if self.selected_ids else self.fixtures_3d
        if not targets: return
        avg_oy = sum(f["offset_y"] for f in targets) / len(targets)
        for f in targets:
            f["offset_y"] = avg_oy
        self.update()

    def align_fixtures_vertical(self) -> None:
        """Aligns selected (or all) 3D fixtures vertically (same X lateral position)."""
        targets = [f for f in self.fixtures_3d if f["id"] in self.selected_ids] if self.selected_ids else self.fixtures_3d
        if not targets: return
        avg_ox = sum(f["offset_x"] for f in targets) / len(targets)
        for f in targets:
            f["offset_x"] = avg_ox
        self.update()

    def set_haze_enabled(self, enabled: bool) -> None:
        self.haze_enabled = enabled
        if enabled:
            if not self.anim_timer.isActive():
                self.anim_timer.start()
        else:
            if self.anim_timer.isActive():
                self.anim_timer.stop()
        self.update()

    def reset_camera(self) -> None:
        """Resets camera to eye-level front-facing view."""
        self.yaw = 0.0
        self.pitch = 0.0
        self.cam_distance = 600.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def _on_animation_tick(self) -> None:
        if not self.haze_enabled:
            return
        for p in self.smoke_particles:
            p["x"] += p["speed_x"]
            p["phase"] += 0.04
            p["y"] += math.sin(p["phase"]) * 0.4
            if p["x"] > 340:
                p["x"] = -340
                p["y"] = random.uniform(30, 200)
        self.update()

    def update_dmx_frame(self, dmx_channels: list[int] | bytearray) -> None:
        """Parses DMX channels dynamically for all 3D fixtures."""
        if not self.fixtures_3d:
            return

        for fix in self.fixtures_3d:
            start = fix["start_channel"] - 1
            channels = fix.get("channels", [])

            dim = 255
            r = 0
            g = 0
            b = 0
            w = 0

            if channels:
                for ch in channels:
                    idx = ch.get("channel", 1) - 1
                    ctype = ch.get("type", "").lower()
                    if idx < len(dmx_channels):
                        val = dmx_channels[idx]
                        if ctype == "dimmer": dim = val
                        elif ctype == "red": r = val
                        elif ctype == "green": g = val
                        elif ctype == "blue": b = val
                        elif ctype == "white": w = val
            else:
                if start + 4 < len(dmx_channels):
                    dim = dmx_channels[start]
                    r = dmx_channels[start + 1]
                    g = dmx_channels[start + 2]
                    b = dmx_channels[start + 3]
                    w = dmx_channels[start + 4]

            fix["dim"] = dim
            fix["r"] = r
            fix["g"] = g
            fix["b"] = b
            fix["w"] = w

        self.update()

    # -------------------------------------------------------------------------
    # MOUSE CONTROLS: LEFT (INVERTED ORBIT & SELECT), MIDDLE (NONE), WHEEL (ZOOM), RIGHT (PAN)
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        self.press_pos = event.position().toPoint()
        self.last_mouse_pos = event.position().toPoint()
        if event.button() == Qt.LeftButton:
            self.is_orbiting = True
        elif event.button() == Qt.RightButton:
            self.is_panning = True
        elif event.button() == Qt.MiddleButton:
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        cur_pos = event.position().toPoint()
        dx = cur_pos.x() - self.last_mouse_pos.x()
        dy = cur_pos.y() - self.last_mouse_pos.y()
        self.last_mouse_pos = cur_pos

        if self.is_orbiting:
            # Uninhibited inverted orbit: full 360 yaw rotation, wide pitch range
            self.yaw -= dx * 0.008
            self.pitch = max(-math.radians(65), min(math.radians(88), self.pitch - dy * 0.008))
            self.update()
        elif self.is_panning:
            # Right drag: pan camera horizontally and vertically
            self.pan_x += dx * 0.8
            self.pan_y += dy * 0.8
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.is_orbiting = False
            cur_pos = event.position().toPoint()
            # If clicked without significant drag, perform selection / multi-selection
            if (cur_pos - self.press_pos).manhattanLength() < 6:
                w = self.width()
                h = self.height()
                cx = w / 2.0
                cy = h / 2.0 + 40.0
                clicked_id = None
                for fix in self.fixtures_3d:
                    fx = fix["base_x"] + fix["offset_x"]
                    fy = fix["base_y"] + fix["offset_y"]
                    fz = fix["base_z"] + fix["offset_z"]
                    sx, sy, _ = self.project(fx, fy, fz, cx, cy)
                    if (cur_pos.x() - sx)**2 + (cur_pos.y() - sy)**2 <= 28**2:
                        clicked_id = fix["id"]
                        break

                if clicked_id is not None:
                    if event.modifiers() & Qt.ShiftModifier:
                        if clicked_id in self.selected_ids:
                            self.selected_ids.remove(clicked_id)
                        else:
                            self.selected_ids.add(clicked_id)
                    else:
                        self.selected_ids = {clicked_id}

                    self.fixture_selected.emit(clicked_id)
                    self.selection_changed.emit(list(self.selected_ids))
                    self.update()
        elif event.button() == Qt.RightButton:
            self.is_panning = False

    def wheelEvent(self, event) -> None:
        """Zoom in and zoom out via scroll wheel, bounded within limits."""
        delta = event.angleDelta().y()
        if delta > 0:
            # Zoom In
            self.cam_distance = max(200.0, self.cam_distance - 40.0)
        elif delta < 0:
            # Zoom Out (Bounded to prevent disappearing)
            self.cam_distance = min(1200.0, self.cam_distance + 40.0)
        self.update()

    def project(self, x: float, y: float, z: float, cx: float, cy: float, fov_scale: float = 460.0) -> tuple[float, float, float]:
        """Projects 3D coordinate (x, y, z) into 2D screen coordinate (sx, sy, depth) with camera pan & zoom."""
        # Yaw rotation (around Y axis)
        cos_y, sin_y = math.cos(self.yaw), math.sin(self.yaw)
        x1 = x * cos_y - z * sin_y
        z1 = x * sin_y + z * cos_y

        # Pitch rotation (around X axis)
        cos_p, sin_p = math.cos(self.pitch), math.sin(self.pitch)
        y1 = y * cos_p - z1 * sin_p
        z2 = y * sin_p + z1 * cos_p + self.cam_distance

        if z2 <= 20.0: z2 = 20.0
        sx = (cx + self.pan_x) + (x1 * fov_scale) / z2
        sy = (cy + self.pan_y) - (y1 * fov_scale) / z2
        return sx, sy, z2

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0 + 40.0

        # 1. 3D Stage Floor Polygon (Trapezoid in Perspective)
        floor_3d = [
            (-320, 0, -140),  # Front Left
            (320, 0, -140),   # Front Right
            (260, 0, 180),    # Back Right
            (-260, 0, 180),   # Back Left
        ]
        floor_poly = QPolygonF([QPointF(*self.project(x, y, z, cx, cy)[:2]) for x, y, z in floor_3d])

        floor_grad = QLinearGradient(cx, cy, cx, h)
        floor_grad.setColorAt(0.0, QColor(Theme.SCENE_FLOOR_NEAR))
        floor_grad.setColorAt(1.0, QColor(Theme.SURFACE_VOID))
        painter.setPen(QPen(QColor(Theme.BORDER_STRONG), 1.5))
        painter.setBrush(QBrush(floor_grad))
        painter.drawPolygon(floor_poly)

        # Floor Perspective Grid Lines
        painter.setPen(QPen(QColor(Theme.BORDER_SUBTLE), 1, Qt.DashLine))
        for gx in [-180, -90, 0, 90, 180]:
            p_start = QPointF(*self.project(gx, 0, -140, cx, cy)[:2])
            p_end = QPointF(*self.project(gx * 0.82, 0, 180, cx, cy)[:2])
            painter.drawLine(p_start, p_end)

        # 2. 3D Overhead Aluminum Box-Truss Rigging (Span adapts to fixture count)
        n = len(self.fixtures_3d)
        span = max(240.0, (n * 120.0) / 2.0 + 80.0)
        truss_y = 240.0 + self.pivot_y
        truss_z = 0.0 + self.pivot_z

        truss_points_front = [(-span + self.pivot_x, truss_y, truss_z - 10), (span + self.pivot_x, truss_y, truss_z - 10)]
        truss_points_back = [(-span + self.pivot_x, truss_y + 16, truss_z + 20), (span + self.pivot_x, truss_y + 16, truss_z + 20)]

        tf_s = QPointF(*self.project(*truss_points_front[0], cx, cy)[:2])
        tf_e = QPointF(*self.project(*truss_points_front[1], cx, cy)[:2])
        tb_s = QPointF(*self.project(*truss_points_back[0], cx, cy)[:2])
        tb_e = QPointF(*self.project(*truss_points_back[1], cx, cy)[:2])

        pen_pipe = QPen(QColor(Theme.RIGGING_PIPE), 4)
        painter.setPen(pen_pipe)
        painter.drawLine(tf_s, tf_e)
        painter.drawLine(tb_s, tb_e)

        # Truss diagonal bracing bars
        pen_brace = QPen(QColor(Theme.TICK_MINOR), 1.5)
        painter.setPen(pen_brace)
        step = 40
        start_x = int(-span + self.pivot_x)
        end_x = int(span + self.pivot_x)
        for tx in range(start_x, end_x - 40, step):
            p1 = QPointF(*self.project(tx, truss_y, truss_z - 10, cx, cy)[:2])
            p2 = QPointF(*self.project(tx + 20, truss_y + 16, truss_z + 20, cx, cy)[:2])
            p3 = QPointF(*self.project(tx + 40, truss_y, truss_z - 10, cx, cy)[:2])
            painter.drawLine(p1, p2)
            painter.drawLine(p2, p3)

        # 3. Volumetric 3D Beams with Lens Spread Angle & Floor Reflection Pools
        for fix in self.fixtures_3d:
            dim = fix["dim"] / 255.0
            if dim <= 0.04:
                continue

            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])

            fx = fix["base_x"] + fix["offset_x"]
            fy = fix["base_y"] + fix["offset_y"]
            fz = fix["base_z"] + fix["offset_z"]

            # Lens Position
            lens_pt = QPointF(*self.project(fx, fy - 14, fz, cx, cy)[:2])

            # Apply Fixture 3D Rotation (Pitch RotX, Yaw RotY) to beam target on floor
            rot_x_rad = math.radians(fix.get("rot_x", 0.0))
            rot_y_rad = math.radians(fix.get("rot_y", 0.0))
            beam_spread = fix.get("beam_angle", 28.0)

            # Target position on stage floor with rotation offsets
            spread_factor = math.tan(math.radians(beam_spread / 2.0))
            floor_dist = max(50.0, fy)
            target_x = fx * 0.88 + math.sin(rot_y_rad) * floor_dist * 0.4
            target_z = 25.0 + fz + math.sin(rot_x_rad) * floor_dist * 0.4

            # Dynamic floor radius computed from lens spread angle
            radius_x = max(20.0, floor_dist * spread_factor * 0.8)
            radius_z = max(14.0, radius_x * 0.65)

            floor_ellipse_pts = []
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                px = target_x + math.cos(rad) * radius_x
                pz = target_z + math.sin(rad) * radius_z
                floor_ellipse_pts.append(QPointF(*self.project(px, 0, pz, cx, cy)[:2]))

            # Volumetric 3D Conical Beam
            beam_polygon = [lens_pt]
            beam_polygon.extend(floor_ellipse_pts)
            beam_polygon.append(floor_ellipse_pts[0])

            beam_center_floor = QPointF(*self.project(target_x, 0, target_z, cx, cy)[:2])
            beam_grad = QLinearGradient(lens_pt, beam_center_floor)
            beam_grad.setColorAt(0.0, QColor(r, g, b, int(200 * dim)))
            beam_grad.setColorAt(0.4, QColor(r, g, b, int(85 * dim)))
            beam_grad.setColorAt(1.0, QColor(r, g, b, int(15 * dim)))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(beam_grad))
            painter.drawPolygon(QPolygonF(beam_polygon))

            # Floor Reflection Pool
            floor_glow = QRadialGradient(beam_center_floor, radius_x)
            floor_glow.setColorAt(0.0, QColor(r, g, b, int(170 * dim)))
            floor_glow.setColorAt(0.5, QColor(r, g, b, int(60 * dim)))
            floor_glow.setColorAt(1.0, QColor(r, g, b, 0))
            painter.setBrush(QBrush(floor_glow))
            painter.drawPolygon(QPolygonF(floor_ellipse_pts))

        # 4. Atmospheric Haze / Stage Smoke Layer (when enabled)
        if self.haze_enabled:
            for p in self.smoke_particles:
                sx, sy, sz = self.project(p["x"], p["y"], p["z"], cx, cy)
                scale = 450.0 / sz
                radius_proj = p["radius"] * scale
                if radius_proj > 5:
                    smoke_rad = QRadialGradient(sx, sy, radius_proj)
                    alpha = int(p["alpha"] * self.haze_density)
                    smoke_rad.setColorAt(0.0, QColor(190, 210, 235, alpha))
                    smoke_rad.setColorAt(0.5, QColor(160, 210, 210, int(alpha * 0.4)))
                    smoke_rad.setColorAt(1.0, QColor(120, 140, 180, 0))

                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(smoke_rad))
                    painter.drawEllipse(QPointF(sx, sy), radius_proj, radius_proj * 0.7)

        # 5. 3D Fixture Head Housings, Rigging Cables & Labels
        for fix in self.fixtures_3d:
            fx = fix["base_x"] + fix["offset_x"]
            fy = fix["base_y"] + fix["offset_y"]
            fz = fix["base_z"] + fix["offset_z"]

            head_sx, head_sy, head_sz = self.project(fx, fy, fz, cx, cy)
            scale = 450.0 / head_sz

            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])
            dim = fix["dim"] / 255.0

            # Power/DMX Drop Cable from Truss Pipe to Fixture Clamp
            truss_pt = QPointF(*self.project(fx, truss_y, truss_z - 10, cx, cy)[:2])
            painter.setPen(QPen(QColor(Theme.SURFACE_TROUGH), 2))
            painter.drawLine(truss_pt, QPointF(head_sx, head_sy - 16 * scale))

            # Suspension Coupler / Clamp
            painter.setPen(QPen(QColor(Theme.RIGGING_CLAMP), 2))
            painter.drawLine(QPointF(head_sx, head_sy - 16 * scale), QPointF(head_sx, head_sy - 4 * scale))

            # Yoke Bracket with Knurled Side Adjustment Knobs
            is_sel = fix["id"] in self.selected_ids
            painter.setPen(QPen(QColor(Theme.ACCENT_CYAN if is_sel else Theme.YOKE_IDLE), 2.5))
            yoke_rect = QRectF(head_sx - 16 * scale, head_sy - 6 * scale, 32 * scale, 24 * scale)
            painter.drawArc(yoke_rect, 0, 180 * 16)

            # Knurled Side Knobs on Yoke
            knob_pen = QPen(QColor(Theme.RIGGING_KNOB), 2)
            painter.setPen(knob_pen)
            painter.drawLine(QPointF(head_sx - 17 * scale, head_sy + 4 * scale), QPointF(head_sx - 15 * scale, head_sy + 4 * scale))
            painter.drawLine(QPointF(head_sx + 15 * scale, head_sy + 4 * scale), QPointF(head_sx + 17 * scale, head_sy + 4 * scale))

            # PAR LED Cylindrical Chassis with Rear Cooling Fins
            body_radius = 16 * scale
            painter.setPen(QPen(QColor(Theme.ACCENT_CYAN if is_sel else (Theme.ACCENT_AMBER if dim > 0.1 else Theme.BORDER_STRONG)), 1.5))
            painter.setBrush(QColor(Theme.FIXTURE_BODY))
            painter.drawEllipse(QPointF(head_sx, head_sy), body_radius, body_radius)

            # Rear Cooling Fin Lines
            painter.setPen(QPen(QColor(Theme.RIGGING_COOLING_FINS), 1))
            for f_offset in [-8, -4, 0, 4, 8]:
                fin_sx = head_sx + f_offset * scale
                painter.drawLine(QPointF(fin_sx, head_sy - 11 * scale), QPointF(fin_sx, head_sy - 6 * scale))

            # Multi-Cell LED Lens Face Emitter
            lens_color = QColor(r, g, b, int(255 * max(0.2, dim)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(lens_color))
            painter.drawEllipse(QPointF(head_sx, head_sy + 2 * scale), body_radius * 0.65, body_radius * 0.65)

            # Matrix of LED Lens Beads on PAR Face
            painter.setBrush(QColor(255, 255, 255, int(220 * max(0.25, dim))))
            bead_r = 1.4 * scale
            for angle in [0, 60, 120, 180, 240, 300]:
                rad = math.radians(angle)
                bx = head_sx + math.cos(rad) * (6 * scale)
                by = (head_sy + 2 * scale) + math.sin(rad) * (6 * scale)
                painter.drawEllipse(QPointF(bx, by), bead_r, bead_r)
            painter.drawEllipse(QPointF(head_sx, head_sy + 2 * scale), 1.8 * scale, 1.8 * scale)

            # Fixture Telemetry: ONLY Fixture Name
            painter.setFont(QFont("Inter", max(7, int(8 * scale)), QFont.Bold))
            painter.setPen(QColor(Theme.TEXT_PRIMARY))
            painter.drawText(
                QRectF(head_sx - 60, head_sy - 30 * scale, 120, 16),
                Qt.AlignCenter,
                fix["name"]
            )

        painter.end()


# -----------------------------------------------------------------------------
# 3. STANDALONE STAGE VISUALIZER WINDOW (2D & 3D WITH TOP TABS & HAMBURGER DRAWER)
# -----------------------------------------------------------------------------
class StageVisualizerWindow(QWidget if HAS_QT else object):
    """
    Standalone Floating Window for Stage Lighting Visualization.
    Features a top bar with 2D/3D switch on the left and a controls drawer button on the right,
    selection-aware pivot positioning & 3D rotation, and collapsible control drawer.
    """
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Stage Visualizer")
        self.resize(920, 600)
        self.setStyleSheet(CONSOLE_QSS)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_zz.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._active_fixtures: list[dict] = []
        self._current_view = 0  # 0: 2D Front View, 1: 3D Perspective View
        self._init_ui()

    def _init_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setSpacing(8)

        # Top Bar: Switch Buttons on the Left, Hamburger on the Right
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(6)

        self.btn_tab_2d = QPushButton("2D Front View")
        self.btn_tab_2d.setCheckable(True)
        self.btn_tab_2d.setChecked(True)
        self.btn_tab_2d.setStyleSheet(f"background-color: {Theme.BG_ELEVATED}; border: none; border-bottom: 2px solid {Theme.ACCENT_CYAN}; border-top-left-radius: 4px; border-bottom-left-radius: 4px; color: {Theme.TEXT_PRIMARY}; font-weight: 700; padding: 6px 18px;")
        self.btn_tab_2d.clicked.connect(lambda: self._switch_view(0))
        top_bar.addWidget(self.btn_tab_2d)

        self.btn_tab_3d = QPushButton("3D Perspective View")
        self.btn_tab_3d.setCheckable(True)
        self.btn_tab_3d.setChecked(False)
        self.btn_tab_3d.setStyleSheet(f"background-color: transparent; border: none; border-top-right-radius: 4px; border-bottom-right-radius: 4px; color: {Theme.TEXT_SECONDARY}; font-weight: 600; padding: 6px 18px;")
        self.btn_tab_3d.clicked.connect(lambda: self._switch_view(1))
        top_bar.addWidget(self.btn_tab_3d)

        top_bar.addStretch()

        # Right Controls Drawer Toggle, drawn as a compact vector icon.
        from ui.icons import create_hamburger_icon
        self.btn_hamburger = QPushButton()
        hamburger_icon = create_hamburger_icon(Theme.TEXT_PRIMARY, 18)
        if hamburger_icon is not None and not hamburger_icon.isNull():
            self.btn_hamburger.setIcon(hamburger_icon)
        else:
            self.btn_hamburger.setText("[DRAWER]")
        self.btn_hamburger.setToolTip("Toggle Controls Drawer")
        self.btn_hamburger.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                font-weight: 800;
                padding: 4px 10px;
                min-width: 28px;
                min-height: 24px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.ACCENT_CYAN};
            }}
        """)
        self.btn_hamburger.clicked.connect(self._toggle_drawer)
        top_bar.addWidget(self.btn_hamburger)

        root_layout.addLayout(top_bar)

        # Main Body: Stacked Canvases & Drawer
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Central Visualizer Canvases (QStackedWidget)
        self.tabs = QStackedWidget(self)
        self.canvas_2d = Stage2DCanvas(self)
        self.canvas_3d = Stage3DCanvas(self)
        self.tabs.addWidget(self.canvas_2d)
        self.tabs.addWidget(self.canvas_3d)

        self.canvas_2d.fixture_selected.connect(self._on_fixture_selected)
        self.canvas_3d.fixture_selected.connect(self._on_fixture_selected)

        content_layout.addWidget(self.tabs, 1)

        # Side Control Drawer (Default: Hidden / Closed)
        self.drawer_widget = QFrame()
        self.drawer_widget.setFixedWidth(235)
        self.drawer_widget.setVisible(False)
        self.drawer_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 6px;
            }}
        """)
        drawer_layout = QVBoxLayout(self.drawer_widget)
        drawer_layout.setContentsMargins(12, 12, 12, 12)
        drawer_layout.setSpacing(10)

        # 3D Camera Controls Group
        self.box_3d_controls = QFrame()
        self.box_3d_controls.setStyleSheet("border: none; background: transparent;")
        box_3d_layout = QVBoxLayout(self.box_3d_controls)
        box_3d_layout.setContentsMargins(0, 0, 0, 0)
        box_3d_layout.setSpacing(8)

        self.btn_reset_cam = QPushButton("Reset Camera")
        self.btn_reset_cam.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BUTTON_NEUTRAL_BG};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                font-weight: 700;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.SURFACE_HOVER};
            }}
        """)
        self.btn_reset_cam.clicked.connect(self._on_reset_camera_clicked)
        box_3d_layout.addWidget(self.btn_reset_cam)

        self.btn_haze = QPushButton("Haze FX")
        self.btn_haze.setStyleSheet(f"background-color: {Theme.BUTTON_NEUTRAL_BG}; border: 1px solid {Theme.BORDER_STRONG}; border-radius: 4px; color: {Theme.TEXT_MUTED}; font-weight: bold; padding: 6px;")
        self.btn_haze.clicked.connect(self._on_toggle_haze)
        box_3d_layout.addWidget(self.btn_haze)

        drawer_layout.addWidget(self.box_3d_controls)

        self.divider_3d = QFrame()
        self.divider_3d.setFixedHeight(1)
        self.divider_3d.setStyleSheet(f"background-color: {Theme.BORDER_SUBTLE}; border: none;")
        drawer_layout.addWidget(self.divider_3d)

        # --- FIXTURE POSITION SECTION ---
        lbl_pos = QLabel("FIXTURE POSITION")
        lbl_pos.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Theme.TEXT_SECONDARY}; letter-spacing: 0.5px;")
        drawer_layout.addWidget(lbl_pos)

        # Pivot X
        self.slider_pivot_x, self.spin_pivot_x, col_px = self._create_slider_spin_row("Pivot X:", -300, 300, 0)
        self.slider_pivot_x.valueChanged.connect(self.spin_pivot_x.setValue)
        self.spin_pivot_x.valueChanged.connect(self.slider_pivot_x.setValue)
        self.spin_pivot_x.valueChanged.connect(self._on_position_changed)
        drawer_layout.addLayout(col_px)

        # Pivot Y
        self.slider_pivot_y, self.spin_pivot_y, col_py = self._create_slider_spin_row("Pivot Y:", -300, 300, 0)
        self.slider_pivot_y.valueChanged.connect(self.spin_pivot_y.setValue)
        self.spin_pivot_y.valueChanged.connect(self.slider_pivot_y.setValue)
        self.spin_pivot_y.valueChanged.connect(self._on_position_changed)
        drawer_layout.addLayout(col_py)

        # Pivot Z (3D only)
        self.col_pz_widget = QWidget()
        pz_box = QVBoxLayout(self.col_pz_widget)
        pz_box.setContentsMargins(0, 0, 0, 0)
        self.slider_pivot_z, self.spin_pivot_z, col_pz = self._create_slider_spin_row("Pivot Z:", -300, 300, 0)
        self.slider_pivot_z.valueChanged.connect(self.spin_pivot_z.setValue)
        self.spin_pivot_z.valueChanged.connect(self.slider_pivot_z.setValue)
        self.spin_pivot_z.valueChanged.connect(self._on_position_changed)
        pz_box.addLayout(col_pz)
        drawer_layout.addWidget(self.col_pz_widget)

        # --- FIXTURE ROTATION SECTION (3D ONLY) ---
        self.box_rot_widget = QWidget()
        rot_box = QVBoxLayout(self.box_rot_widget)
        rot_box.setContentsMargins(0, 0, 0, 0)
        rot_box.setSpacing(6)

        div_rot = QFrame()
        div_rot.setFixedHeight(1)
        div_rot.setStyleSheet(f"background-color: {Theme.BORDER_SUBTLE}; border: none;")
        rot_box.addWidget(div_rot)

        lbl_rot = QLabel("FIXTURE ROTATION")
        lbl_rot.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Theme.TEXT_SECONDARY}; letter-spacing: 0.5px;")
        rot_box.addWidget(lbl_rot)

        # Rot X (Pitch Tilt)
        self.slider_rot_x, self.spin_rot_x, col_rx = self._create_slider_spin_row("Rot X (Tilt):", -90, 90, 0)
        self.slider_rot_x.valueChanged.connect(self.spin_rot_x.setValue)
        self.spin_rot_x.valueChanged.connect(self.slider_rot_x.setValue)
        self.spin_rot_x.valueChanged.connect(self._on_rotation_changed)
        rot_box.addLayout(col_rx)

        # Rot Y (Yaw Pan)
        self.slider_rot_y, self.spin_rot_y, col_ry = self._create_slider_spin_row("Rot Y (Pan):", -180, 180, 0)
        self.slider_rot_y.valueChanged.connect(self.spin_rot_y.setValue)
        self.spin_rot_y.valueChanged.connect(self.slider_rot_y.setValue)
        self.spin_rot_y.valueChanged.connect(self._on_rotation_changed)
        rot_box.addLayout(col_ry)

        # Rot Z (Roll)
        self.slider_rot_z, self.spin_rot_z, col_rz = self._create_slider_spin_row("Rot Z (Roll):", -180, 180, 0)
        self.slider_rot_z.valueChanged.connect(self.spin_rot_z.setValue)
        self.spin_rot_z.valueChanged.connect(self.slider_rot_z.setValue)
        self.spin_rot_z.valueChanged.connect(self._on_rotation_changed)
        rot_box.addLayout(col_rz)

        # Lens Spread Beam Angle (15° to 60°)
        self.slider_beam_angle, self.spin_beam_angle, col_beam = self._create_slider_spin_row("Beam Angle:", 15, 60, 28)
        self.slider_beam_angle.valueChanged.connect(self.spin_beam_angle.setValue)
        self.spin_beam_angle.valueChanged.connect(self.slider_beam_angle.setValue)
        self.spin_beam_angle.valueChanged.connect(self._on_beam_angle_changed)
        rot_box.addLayout(col_beam)

        drawer_layout.addWidget(self.box_rot_widget)

        # --- ALIGNMENT CONTROLS ---
        div_align = QFrame()
        div_align.setFixedHeight(1)
        div_align.setStyleSheet(f"background-color: {Theme.BORDER_SUBTLE}; border: none;")
        drawer_layout.addWidget(div_align)

        lbl_align = QLabel("ALIGNMENT")
        lbl_align.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Theme.TEXT_SECONDARY}; letter-spacing: 0.5px;")
        drawer_layout.addWidget(lbl_align)

        row_align = QHBoxLayout()
        row_align.setSpacing(6)
        self.btn_align_h = QPushButton("Align Horizontal")
        self.btn_align_h.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; border: 1px solid {Theme.BORDER_STRONG}; padding: 5px;")
        self.btn_align_h.clicked.connect(self._on_align_h_clicked)
        row_align.addWidget(self.btn_align_h)

        self.btn_align_v = QPushButton("Align Vertical")
        self.btn_align_v.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; border: 1px solid {Theme.BORDER_STRONG}; padding: 5px;")
        self.btn_align_v.clicked.connect(self._on_align_v_clicked)
        row_align.addWidget(self.btn_align_v)
        drawer_layout.addLayout(row_align)

        drawer_layout.addStretch()
        content_layout.addWidget(self.drawer_widget)

        root_layout.addLayout(content_layout, 1)

        # Initial view setup: default 2D Front View
        self._switch_view(0)

    def _create_slider_spin_row(self, label: str, min_val: int, max_val: int, init_val: int) -> tuple[QSlider, QSpinBox, QVBoxLayout]:
        col = QVBoxLayout()
        col.setSpacing(3)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        col.addWidget(lbl)

        row = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(init_val)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 4px; background: {Theme.SURFACE_INPUT}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ width: 12px; margin: -5px 0; background: {Theme.ACCENT_CYAN}; border-radius: 6px; }}
        """)
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(init_val)
        spin.setFixedWidth(60)
        spin.setStyleSheet(f"background-color: {Theme.SURFACE_INPUT}; color: {Theme.TEXT_PRIMARY}; border: 1px solid {Theme.BORDER_STRONG};")

        row.addWidget(slider, 1)
        row.addWidget(spin)
        col.addLayout(row)
        return slider, spin, col

    def _switch_view(self, index: int) -> None:
        self._current_view = index
        self.tabs.setCurrentIndex(index)
        # Segmented switcher idiom: active segment gets elevated fill + cyan underline,
        # inactive segments stay transparent. Matches the construction styles exactly.
        active_2d = f"background-color: {Theme.BG_ELEVATED}; border: none; border-bottom: 2px solid {Theme.ACCENT_CYAN}; border-top-left-radius: 4px; border-bottom-left-radius: 4px; color: {Theme.TEXT_PRIMARY}; font-weight: 700; padding: 6px 18px;"
        inactive_2d = f"background-color: transparent; border: none; border-top-left-radius: 4px; border-bottom-left-radius: 4px; color: {Theme.TEXT_SECONDARY}; font-weight: 600; padding: 6px 18px;"
        active_3d = f"background-color: {Theme.BG_ELEVATED}; border: none; border-bottom: 2px solid {Theme.ACCENT_CYAN}; border-top-right-radius: 4px; border-bottom-right-radius: 4px; color: {Theme.TEXT_PRIMARY}; font-weight: 700; padding: 6px 18px;"
        inactive_3d = f"background-color: transparent; border: none; border-top-right-radius: 4px; border-bottom-right-radius: 4px; color: {Theme.TEXT_SECONDARY}; font-weight: 600; padding: 6px 18px;"
        self.btn_tab_2d.setChecked(index == 0)
        self.btn_tab_3d.setChecked(index == 1)
        self.btn_tab_2d.setStyleSheet(active_2d if index == 0 else inactive_2d)
        self.btn_tab_3d.setStyleSheet(active_3d if index == 1 else inactive_3d)
        self.box_3d_controls.setVisible(index == 1)
        self.divider_3d.setVisible(index == 1)
        self.col_pz_widget.setVisible(index == 1)
        self.box_rot_widget.setVisible(index == 1)

    def _toggle_drawer(self) -> None:
        self.drawer_widget.setVisible(not self.drawer_widget.isVisible())

    def _on_fixture_selected(self, fixture_id: int) -> None:
        """When a fixture is selected in either 2D or 3D canvas, load its current pivot values into sliders."""
        target_2d = next((f for f in self.canvas_2d.fixtures if f["id"] == fixture_id), None)
        target_3d = next((f for f in self.canvas_3d.fixtures_3d if f["id"] == fixture_id), None)

        if target_2d:
            self.spin_pivot_x.blockSignals(True)
            self.spin_pivot_y.blockSignals(True)
            self.slider_pivot_x.blockSignals(True)
            self.slider_pivot_y.blockSignals(True)
            ox = int(target_2d.get("offset_x", 0))
            oy = int(target_2d.get("offset_y", 0))
            self.spin_pivot_x.setValue(ox)
            self.slider_pivot_x.setValue(ox)
            self.spin_pivot_y.setValue(oy)
            self.slider_pivot_y.setValue(oy)
            self.spin_pivot_x.blockSignals(False)
            self.spin_pivot_y.blockSignals(False)
            self.slider_pivot_x.blockSignals(False)
            self.slider_pivot_y.blockSignals(False)

        if target_3d:
            self.spin_pivot_z.blockSignals(True)
            self.slider_pivot_z.blockSignals(True)
            self.spin_rot_x.blockSignals(True)
            self.spin_rot_y.blockSignals(True)
            self.spin_rot_z.blockSignals(True)
            self.slider_rot_x.blockSignals(True)
            self.slider_rot_y.blockSignals(True)
            self.slider_rot_z.blockSignals(True)
            self.spin_beam_angle.blockSignals(True)
            self.slider_beam_angle.blockSignals(True)

            oz = int(target_3d.get("offset_z", 0))
            rx = int(target_3d.get("rot_x", 0))
            ry = int(target_3d.get("rot_y", 0))
            rz = int(target_3d.get("rot_z", 0))
            ba = int(target_3d.get("beam_angle", 28))

            self.spin_pivot_z.setValue(oz)
            self.slider_pivot_z.setValue(oz)
            self.spin_rot_x.setValue(rx)
            self.slider_rot_x.setValue(rx)
            self.spin_rot_y.setValue(ry)
            self.slider_rot_y.setValue(ry)
            self.spin_rot_z.setValue(rz)
            self.slider_rot_z.setValue(rz)
            self.spin_beam_angle.setValue(ba)
            self.slider_beam_angle.setValue(ba)

            self.spin_pivot_z.blockSignals(False)
            self.slider_pivot_z.blockSignals(False)
            self.spin_rot_x.blockSignals(False)
            self.spin_rot_y.blockSignals(False)
            self.spin_rot_z.blockSignals(False)
            self.slider_rot_x.blockSignals(False)
            self.slider_rot_y.blockSignals(False)
            self.slider_rot_z.blockSignals(False)
            self.spin_beam_angle.blockSignals(False)
            self.slider_beam_angle.blockSignals(False)

    def _on_position_changed(self) -> None:
        ox = self.spin_pivot_x.value()
        oy = self.spin_pivot_y.value()
        oz = self.spin_pivot_z.value()
        self.canvas_2d.set_selected_offsets(ox, oy)
        self.canvas_3d.set_selected_offsets(ox, oy, oz)

    def _on_rotation_changed(self) -> None:
        rx = self.spin_rot_x.value()
        ry = self.spin_rot_y.value()
        rz = self.spin_rot_z.value()
        self.canvas_3d.set_selected_rotations(rx, ry, rz)

    def _on_beam_angle_changed(self) -> None:
        angle = self.spin_beam_angle.value()
        self.canvas_3d.set_selected_beam_angle(angle)

    def _on_align_h_clicked(self) -> None:
        self.canvas_2d.align_fixtures_horizontal()
        self.canvas_3d.align_fixtures_horizontal()

    def _on_align_v_clicked(self) -> None:
        self.canvas_2d.align_fixtures_vertical()
        self.canvas_3d.align_fixtures_vertical()

    def _on_reset_camera_clicked(self) -> None:
        self.canvas_3d.reset_camera()
        self.btn_reset_cam.setStyleSheet(f"background-color: {Theme.COLOR_SUCCESS}; border: none; border-radius: 4px; color: {Theme.COLOR_BLACK}; font-weight: bold; padding: 6px;")
        QTimer.singleShot(350, self._restore_reset_cam_style)

    def _restore_reset_cam_style(self) -> None:
        self.btn_reset_cam.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BUTTON_NEUTRAL_BG};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                font-weight: 700;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.SURFACE_HOVER};
            }}
        """)

    def _on_toggle_haze(self) -> None:
        new_state = not self.canvas_3d.haze_enabled
        self.canvas_3d.set_haze_enabled(new_state)
        if new_state:
            self.btn_haze.setStyleSheet(f"background-color: {Theme.COLOR_SUCCESS}; border: none; border-radius: 4px; color: {Theme.COLOR_BLACK}; font-weight: bold; padding: 6px;")
        else:
            self.btn_haze.setStyleSheet(f"background-color: {Theme.BUTTON_NEUTRAL_BG}; border: 1px solid {Theme.BORDER_STRONG}; border-radius: 4px; color: {Theme.TEXT_MUTED}; font-weight: bold; padding: 6px;")

    def sync_fixtures(self, fixtures: list[dict]) -> None:
        """Synchronizes active patched fixtures to both 2D and 3D visualizer canvases."""
        self._active_fixtures = fixtures
        self.canvas_2d.set_fixtures(fixtures)
        self.canvas_3d.set_fixtures(fixtures)

    def update_dmx(self, channels: list[int] | bytearray) -> None:
        """Pushes DMX channels to both 2D and 3D visualizer canvases in real time."""
        if hasattr(self, 'canvas_2d'):
            self.canvas_2d.update_dmx_frame(channels)
        if hasattr(self, 'canvas_3d'):
            self.canvas_3d.update_dmx_frame(channels)

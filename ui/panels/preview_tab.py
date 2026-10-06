"""
preview_tab.py — Standalone Floating Stage Visualizer Window (2D & 3D with Haze/Smoke)
Provides high-fidelity stage lighting simulation with dynamic RGBW PAR LED beam glows,
3D perspective volumetric beams, overhead truss rigging, atmospheric haze/smoke FX,
full mouse camera control (orbit, pan, zoom), center-aligned auto layout, and collapsible side drawer.
"""

from __future__ import annotations
import math
import random
from pathlib import Path

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpinBox, QTabWidget,
    Qt, QPoint, QPointF, QRectF, Signal, QPainter, QColor, QPen, QPolygonF,
    QRadialGradient, QLinearGradient, QBrush, QFont, QTimer, QIcon
)
from ui.styles import Theme, CONSOLE_QSS


# -----------------------------------------------------------------------------
# 1. 2D STAGE CANVAS (FRONT VIEW WITH CENTER-ALIGNED RIGGING)
# -----------------------------------------------------------------------------
class Stage2DCanvas(QFrame if HAS_QT else object):
    """Front-view 2D Stage Canvas with RGBW beam projection, halos, floor bounce, and center alignment."""
    fixture_selected = Signal(int, int, int)

    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setStyleSheet("background-color: #07080a; border: 1px solid #333844; border-radius: 6px;")

        # Starts empty by default (Clean initial state for untitled project)
        self.fixtures: list[dict] = []
        self.selected_idx = -1
        self._drag_active = False

        # Pivot offsets (linked with 3D)
        self.pivot_x = 0
        self.pivot_y = 0

    def set_pivots(self, px: int, py: int) -> None:
        self.pivot_x = px
        self.pivot_y = py
        self.recompute_layout()
        self.update()

    def set_fixtures(self, fixtures_data: list[dict]) -> None:
        """Loads patched fixtures and auto-arranges them center-aligned."""
        self.fixtures = []
        for idx, fix in enumerate(fixtures_data):
            self.fixtures.append({
                "id": fix.get("id", idx + 1),
                "name": fix.get("name", f"Fixture #{idx + 1}"),
                "start_channel": fix.get("start_channel", 1),
                "channels": fix.get("channels", []),
                "x": 0,
                "y": 0,
                "r": 255,
                "g": 180,
                "b": 0,
                "w": 40,
                "dim": 240,
            })
        self.selected_idx = 0 if self.fixtures else -1
        self.recompute_layout()
        self.update()

    def recompute_layout(self) -> None:
        """Computes center-aligned positions for all active fixtures."""
        n = len(self.fixtures)
        if n == 0:
            return

        w = max(400, self.width() if self.width() > 100 else 800)
        center_x = w / 2.0 + self.pivot_x
        base_y = 80 + self.pivot_y
        spacing = min(150.0, max(85.0, (w - 140.0) / max(1, n)))

        for i, fix in enumerate(self.fixtures):
            fx = int(center_x + (i - (n - 1) / 2.0) * spacing)
            fix["x"] = fx
            fix["y"] = int(base_y)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.recompute_layout()

    def update_dmx_frame(self, dmx_channels: list[int] | bytearray) -> None:
        """Parses DMX channels dynamically based on each fixture's start channel and channel types."""
        if not self.fixtures:
            return

        for fix in self.fixtures:
            start = fix["start_channel"] - 1  # 0-indexed
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
                # Default 8CH footprint fallback
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
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            for idx, fix in enumerate(self.fixtures):
                fx, fy = fix["x"], fix["y"]
                if (pos.x() - fx)**2 + (pos.y() - fy)**2 <= 30**2:
                    self.selected_idx = idx
                    self._drag_active = True
                    self.fixture_selected.emit(fix["id"], fx, fy)
                    self.update()
                    break

    def mouseMoveEvent(self, event) -> None:
        if not self._drag_active or self.selected_idx < 0: return
        pos = event.position().toPoint()
        self.fixtures[self.selected_idx]["x"] = max(35, min(self.width() - 35, pos.x()))
        self.fixtures[self.selected_idx]["y"] = max(35, min(self.height() - 75, pos.y()))
        fix = self.fixtures[self.selected_idx]
        self.fixture_selected.emit(fix["id"], fix["x"], fix["y"])
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_active = False

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        floor_y = h - 45
        truss_y = 80 + self.pivot_y

        # 1. Truss Rigging Bar at Top
        pen_truss_main = QPen(QColor("#2d3340"), 6)
        painter.setPen(pen_truss_main)
        painter.drawLine(20, truss_y, w - 20, truss_y)

        # Truss diagonal cross bracing
        pen_truss_sub = QPen(QColor("#1e222a"), 2)
        painter.setPen(pen_truss_sub)
        for tx in range(25, w - 25, 40):
            painter.drawLine(tx, truss_y - 8, tx + 20, truss_y + 8)
            painter.drawLine(tx + 20, truss_y + 8, tx + 40, truss_y - 8)

        # 2. Stage Floor Platform
        painter.fillRect(0, floor_y, w, h - floor_y, QColor("#101319"))
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
                "Panggung Siap • Patch fixture di Tab Address untuk memvisualisasikan lampu"
            )
            painter.end()
            return

        # 4. Render Fixtures, Volumetric Beams, Floor Pools, and Cables
        for idx, fix in enumerate(self.fixtures):
            fx, fy = fix["x"], fix["y"]
            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])
            dim = fix["dim"] / 255.0

            # Cable Drop from Truss to Fixture
            painter.setPen(QPen(QColor("#14161a"), 2))
            painter.drawLine(fx, truss_y, fx, fy - 18)

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

            # C. Fixture Casing Housing
            is_sel = (idx == self.selected_idx)
            painter.setPen(QPen(QColor(Theme.ACCENT_CYAN if is_sel else Theme.BORDER_STRONG), 2))
            painter.setBrush(QColor("#181c24"))
            painter.drawEllipse(fx - 18, fy - 18, 36, 36)

            # D. Lens Center Emitter
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(r, g, b, int(255 * max(0.2, dim))))
            painter.drawEllipse(fx - 11, fy - 11, 22, 22)

            # E. Telemetry: ONLY Fixture Name
            painter.setFont(QFont("Inter", 8, QFont.Bold))
            painter.setPen(QColor(Theme.TEXT_PRIMARY))
            painter.drawText(QRectF(fx - 70, fy + 22, 140, 16), Qt.AlignCenter, fix["name"])

        painter.end()


# -----------------------------------------------------------------------------
# 2. 3D STAGE CANVAS (FULL MOUSE CONTROL: ORBIT, ZOOM, PAN & PIVOT OFFSETS)
# -----------------------------------------------------------------------------
class Stage3DCanvas(QFrame if HAS_QT else object):
    """
    True Perspective 3D Stage Visualizer.
    Features overhead aluminum box-truss, 3D fixture housings, perspective conical volumetric beams,
    stage floor bounce pools, full mouse controls (left orbit, wheel zoom, right pan),
    center-aligned dynamic layout, and dynamic atmospheric haze/smoke simulation.
    """
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setStyleSheet("background-color: #050608; border: 1px solid #333844; border-radius: 6px;")

        # Camera Orbit Angles & Pan
        self.yaw = math.radians(-12.0)
        self.pitch = math.radians(24.0)
        self.cam_distance = 580.0  # Zoom parameter (min 200, max 1400)
        self.pan_x = 0.0           # Move camera horizontal
        self.pan_y = 0.0           # Move camera vertical

        # Drag state
        self.is_orbiting = False
        self.is_panning = False
        self.last_mouse_pos = QPoint()

        # Pivot Offsets (linked with 2D)
        self.pivot_x = 0
        self.pivot_y = 0
        self.pivot_z = 0

        # Starts empty by default (Clean initial state for untitled project)
        self.fixtures_3d: list[dict] = []

        # Atmospheric Haze / Smoke Simulation State
        self.haze_enabled = True
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
        self.anim_timer.start()

    def set_pivots(self, px: int, py: int, pz: int = 0) -> None:
        self.pivot_x = px
        self.pivot_y = py
        self.pivot_z = pz
        self.recompute_layout()
        self.update()

    def set_fixtures(self, fixtures_data: list[dict]) -> None:
        """Loads patched fixtures and auto-arranges them center-aligned in 3D."""
        self.fixtures_3d = []
        for idx, fix in enumerate(fixtures_data):
            self.fixtures_3d.append({
                "id": fix.get("id", idx + 1),
                "name": fix.get("name", f"Fixture #{idx + 1}"),
                "start_channel": fix.get("start_channel", 1),
                "channels": fix.get("channels", []),
                "x": 0,
                "y": 240,
                "z": 0,
                "r": 255,
                "g": 180,
                "b": 0,
                "w": 40,
                "dim": 240,
            })
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
            fix["x"] = (i - (n - 1) / 2.0) * spacing_3d + self.pivot_x
            fix["y"] = base_y
            fix["z"] = base_z

    def set_haze_enabled(self, enabled: bool) -> None:
        self.haze_enabled = enabled
        if enabled and not self.anim_timer.isActive():
            self.anim_timer.start()
        self.update()

    def reset_camera(self) -> None:
        """Resets camera orientation, zoom, and pan back to defaults."""
        self.yaw = math.radians(-12.0)
        self.pitch = math.radians(24.0)
        self.cam_distance = 580.0
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
    # MOUSE CONTROLS: LEFT (ORBIT), MIDDLE (NONE), WHEEL (ZOOM), RIGHT (PAN)
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
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
            # Orbit yaw & pitch
            self.yaw += dx * 0.008
            self.pitch = max(math.radians(5), min(math.radians(85), self.pitch + dy * 0.008))
            self.update()
        elif self.is_panning:
            # Pan position right/left and up/down
            self.pan_x += dx * 0.8
            self.pan_y += dy * 0.8
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.is_orbiting = False
        elif event.button() == Qt.RightButton:
            self.is_panning = False

    def wheelEvent(self, event) -> None:
        """Zoom in and zoom out via scroll wheel, bounded within limits."""
        delta = event.angleDelta().y()
        if delta > 0:
            # Zoom In
            self.cam_distance = max(200.0, self.cam_distance - 40.0)
        elif delta < 0:
            # Zoom Out
            self.cam_distance = min(1400.0, self.cam_distance + 40.0)
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
        floor_grad.setColorAt(0.0, QColor("#12151d"))
        floor_grad.setColorAt(1.0, QColor("#090b0e"))
        painter.setPen(QPen(QColor(Theme.BORDER_STRONG), 1.5))
        painter.setBrush(QBrush(floor_grad))
        painter.drawPolygon(floor_poly)

        # Floor Perspective Grid Lines
        painter.setPen(QPen(QColor("#1e232d"), 1, Qt.DashLine))
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

        pen_pipe = QPen(QColor("#5a6275"), 4)
        painter.setPen(pen_pipe)
        painter.drawLine(tf_s, tf_e)
        painter.drawLine(tb_s, tb_e)

        # Truss diagonal bracing bars
        pen_brace = QPen(QColor("#383e4c"), 1.5)
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

        # 3. Volumetric 3D Beams & Floor Light Pools
        for fix in self.fixtures_3d:
            dim = fix["dim"] / 255.0
            if dim <= 0.04:
                continue

            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])

            lx, ly, lz = fix["x"], fix["y"] - 14, fix["z"]
            lens_pt = QPointF(*self.project(lx, ly, lz, cx, cy)[:2])

            target_x = fix["x"] * 0.88
            target_z = 25.0 + fix["z"]

            floor_ellipse_pts = []
            radius_x = 55.0
            radius_z = 35.0
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
            floor_glow = QRadialGradient(beam_center_floor, 70)
            floor_glow.setColorAt(0.0, QColor(r, g, b, int(170 * dim)))
            floor_glow.setColorAt(0.5, QColor(r, g, b, int(60 * dim)))
            floor_glow.setColorAt(1.0, QColor(r, g, b, 0))
            painter.setBrush(QBrush(floor_glow))
            painter.drawPolygon(QPolygonF(floor_ellipse_pts))

        # 4. Atmospheric Haze / Stage Smoke Layer
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
            lx, ly, lz = fix["x"], fix["y"], fix["z"]
            head_sx, head_sy, head_sz = self.project(lx, ly, lz, cx, cy)
            scale = 450.0 / head_sz

            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])
            dim = fix["dim"] / 255.0

            # Power/DMX Drop Cable from Truss Pipe to Fixture Clamp
            truss_pt = QPointF(*self.project(lx, truss_y, truss_z - 10, cx, cy)[:2])
            painter.setPen(QPen(QColor("#14161a"), 2))
            painter.drawLine(truss_pt, QPointF(head_sx, head_sy - 16 * scale))

            # Suspension Coupler / Clamp
            painter.setPen(QPen(QColor("#717b8f"), 2))
            painter.drawLine(QPointF(head_sx, head_sy - 16 * scale), QPointF(head_sx, head_sy - 4 * scale))

            # Yoke Bracket
            painter.setPen(QPen(QColor("#404654"), 2.5))
            yoke_rect = QRectF(head_sx - 14 * scale, head_sy - 6 * scale, 28 * scale, 22 * scale)
            painter.drawArc(yoke_rect, 0, 180 * 16)

            # PAR LED Cylindrical Body
            body_radius = 16 * scale
            painter.setPen(QPen(QColor(Theme.ACCENT_AMBER if dim > 0.1 else Theme.BORDER_STRONG), 1.5))
            painter.setBrush(QColor("#14171f"))
            painter.drawEllipse(QPointF(head_sx, head_sy), body_radius, body_radius)

            # Lens Face Emitter with Bezel
            lens_color = QColor(r, g, b, int(255 * max(0.2, dim)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(lens_color))
            painter.drawEllipse(QPointF(head_sx, head_sy + 2 * scale), body_radius * 0.65, body_radius * 0.65)

            # Fixture Telemetry: ONLY Fixture Name
            painter.setFont(QFont("Inter", max(7, int(8 * scale)), QFont.Bold))
            painter.setPen(QColor(Theme.TEXT_PRIMARY))
            painter.drawText(
                QRectF(head_sx - 60, head_sy - 28 * scale, 120, 16),
                Qt.AlignCenter,
                fix["name"]
            )

        painter.end()


# -----------------------------------------------------------------------------
# 3. STANDALONE STAGE VISUALIZER WINDOW (2D & 3D WITH HAMBURGER DRAWER)
# -----------------------------------------------------------------------------
class StageVisualizerWindow(QWidget if HAS_QT else object):
    """
    Standalone Floating Window for Stage Lighting Visualization.
    Features 2D Front View (default) and 3D Perspective Stage with Haze Simulation,
    a right-hand collapsible control drawer opened via hamburger [☰], and linked pivots.
    """
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Stage Visualizer")
        self.resize(900, 600)
        self.setStyleSheet(CONSOLE_QSS)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_zz.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self._active_fixtures: list[dict] = []
        self._init_ui()

    def _init_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setSpacing(8)

        # Header Row: Tabs on Left, Hamburger on Right (No decorative titles)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        # Central Visualizer Tabs: Default 2D Front View (Index 0), then 3D Perspective (Index 1)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 6px;
                background-color: {Theme.BG_ROOT};
            }}
            QTabBar::tab {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_SUBTLE};
                color: {Theme.TEXT_SECONDARY};
                font-weight: 700;
                font-size: 11px;
                padding: 6px 18px;
                margin-right: 4px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.ACCENT_CYAN};
                color: #ffffff;
            }}
        """)

        # Tab 1: 2D Front View (Default - Lightweight cold launch)
        self.canvas_2d = Stage2DCanvas(self)
        self.tabs.addTab(self.canvas_2d, "2D Front View")

        # Tab 2: 3D Perspective View (Volumetric & Haze)
        self.canvas_3d = Stage3DCanvas(self)
        self.tabs.addTab(self.canvas_3d, "3D Perspective View")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Right Hamburger Toggle Button
        self.btn_hamburger = QPushButton("☰")
        self.btn_hamburger.setToolTip("Toggle Control Panel")
        self.btn_hamburger.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 4px;
                color: #ffffff;
                font-size: 15px;
                font-weight: 800;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_ELEVATED};
                border-color: {Theme.ACCENT_CYAN};
            }}
        """)
        self.btn_hamburger.clicked.connect(self._toggle_drawer)

        # Build Main Body with Drawer
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        content_layout.addWidget(self.tabs, 1)

        # Side Control Drawer
        self.drawer_widget = QFrame()
        self.drawer_widget.setFixedWidth(210)
        self.drawer_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_SURFACE};
                border: 1px solid {Theme.BORDER_STRONG};
                border-radius: 6px;
            }}
        """)
        drawer_layout = QVBoxLayout(self.drawer_widget)
        drawer_layout.setContentsMargins(12, 14, 12, 14)
        drawer_layout.setSpacing(12)

        # Drawer Title
        lbl_panel = QLabel("CONTROL PANEL")
        lbl_panel.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Theme.TEXT_SECONDARY}; letter-spacing: 1px;")
        drawer_layout.addWidget(lbl_panel)

        # --- 3D Specific Section ---
        self.box_3d_controls = QFrame()
        self.box_3d_controls.setStyleSheet("border: none; background: transparent;")
        box_3d_layout = QVBoxLayout(self.box_3d_controls)
        box_3d_layout.setContentsMargins(0, 0, 0, 0)
        box_3d_layout.setSpacing(8)

        # Reset Camera Button (Standby Grey, Green on Click)
        self.btn_reset_cam = QPushButton("Reset Camera")
        self.btn_reset_cam.setStyleSheet(f"""
            QPushButton {{
                background-color: #333844;
                border: 1px solid #4a5264;
                border-radius: 4px;
                color: #ffffff;
                font-weight: 700;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: #3d4352;
            }}
        """)
        self.btn_reset_cam.clicked.connect(self._on_reset_camera_clicked)
        box_3d_layout.addWidget(self.btn_reset_cam)

        # Haze FX Switch (Green when ON, Grey when OFF)
        self.btn_haze = QPushButton("Haze: ON")
        self.btn_haze.setStyleSheet("background-color: #16a34a; border: none; border-radius: 4px; color: #ffffff; font-weight: bold; padding: 6px;")
        self.btn_haze.clicked.connect(self._on_toggle_haze)
        box_3d_layout.addWidget(self.btn_haze)

        drawer_layout.addWidget(self.box_3d_controls)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Theme.BORDER_SUBTLE}; border: none;")
        drawer_layout.addWidget(divider)

        # --- Pivot Position Section (Linked 2D & 3D) ---
        lbl_pivot = QLabel("POSISI FIXTURE")
        lbl_pivot.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {Theme.TEXT_SECONDARY};")
        drawer_layout.addWidget(lbl_pivot)

        # Pivot X
        row_px = QHBoxLayout()
        lbl_px = QLabel("Pivot X:")
        lbl_px.setFixedWidth(55)
        lbl_px.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        self.spin_pivot_x = QSpinBox()
        self.spin_pivot_x.setRange(-500, 500)
        self.spin_pivot_x.setValue(0)
        self.spin_pivot_x.setSingleStep(10)
        self.spin_pivot_x.setStyleSheet(f"background-color: {Theme.BG_INPUT}; color: #ffffff; border: 1px solid {Theme.BORDER_STRONG};")
        self.spin_pivot_x.valueChanged.connect(self._on_pivots_changed)
        row_px.addWidget(lbl_px)
        row_px.addWidget(self.spin_pivot_x)
        drawer_layout.addLayout(row_px)

        # Pivot Y
        row_py = QHBoxLayout()
        lbl_py = QLabel("Pivot Y:")
        lbl_py.setFixedWidth(55)
        lbl_py.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        self.spin_pivot_y = QSpinBox()
        self.spin_pivot_y.setRange(-300, 300)
        self.spin_pivot_y.setValue(0)
        self.spin_pivot_y.setSingleStep(10)
        self.spin_pivot_y.setStyleSheet(f"background-color: {Theme.BG_INPUT}; color: #ffffff; border: 1px solid {Theme.BORDER_STRONG};")
        self.spin_pivot_y.valueChanged.connect(self._on_pivots_changed)
        row_py.addWidget(lbl_py)
        row_py.addWidget(self.spin_pivot_y)
        drawer_layout.addLayout(row_py)

        # Pivot Z (Only active for 3D)
        self.row_pz_widget = QWidget()
        row_pz = QHBoxLayout(self.row_pz_widget)
        row_pz.setContentsMargins(0, 0, 0, 0)
        lbl_pz = QLabel("Pivot Z:")
        lbl_pz.setFixedWidth(55)
        lbl_pz.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        self.spin_pivot_z = QSpinBox()
        self.spin_pivot_z.setRange(-300, 300)
        self.spin_pivot_z.setValue(0)
        self.spin_pivot_z.setSingleStep(10)
        self.spin_pivot_z.setStyleSheet(f"background-color: {Theme.BG_INPUT}; color: #ffffff; border: 1px solid {Theme.BORDER_STRONG};")
        self.spin_pivot_z.valueChanged.connect(self._on_pivots_changed)
        row_pz.addWidget(lbl_pz)
        row_pz.addWidget(self.spin_pivot_z)
        drawer_layout.addWidget(self.row_pz_widget)

        drawer_layout.addStretch()
        content_layout.addWidget(self.drawer_widget)

        # Set Top Bar
        header_row.addStretch()
        header_row.addWidget(self.btn_hamburger)
        root_layout.addLayout(header_row)
        root_layout.addLayout(content_layout, 1)

        # Initial Tab Setup (Default: 2D view, hide 3D specific controls)
        self._on_tab_changed(0)

    def _toggle_drawer(self) -> None:
        self.drawer_widget.setVisible(not self.drawer_widget.isVisible())

    def _on_tab_changed(self, index: int) -> None:
        # Index 0: 2D Front View
        # Index 1: 3D Perspective View
        if index == 0:
            self.box_3d_controls.setVisible(False)
            self.row_pz_widget.setVisible(False)
        else:
            self.box_3d_controls.setVisible(True)
            self.row_pz_widget.setVisible(True)

    def _on_reset_camera_clicked(self) -> None:
        self.canvas_3d.reset_camera()
        # Visual feedback: flash green on click, then return to standby grey
        self.btn_reset_cam.setStyleSheet("background-color: #16a34a; border: none; border-radius: 4px; color: #ffffff; font-weight: bold; padding: 6px;")
        QTimer.singleShot(350, self._restore_reset_cam_style)

    def _restore_reset_cam_style(self) -> None:
        self.btn_reset_cam.setStyleSheet(f"""
            QPushButton {{
                background-color: #333844;
                border: 1px solid #4a5264;
                border-radius: 4px;
                color: #ffffff;
                font-weight: 700;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: #3d4352;
            }}
        """)

    def _on_toggle_haze(self) -> None:
        new_state = not self.canvas_3d.haze_enabled
        self.canvas_3d.set_haze_enabled(new_state)
        if new_state:
            self.btn_haze.setText("Haze: ON")
            self.btn_haze.setStyleSheet("background-color: #16a34a; border: none; border-radius: 4px; color: #ffffff; font-weight: bold; padding: 6px;")
        else:
            self.btn_haze.setText("Haze: OFF")
            self.btn_haze.setStyleSheet("background-color: #333844; border: 1px solid #4a5264; border-radius: 4px; color: #94a3b8; font-weight: normal; padding: 6px;")

    def _on_pivots_changed(self) -> None:
        px = self.spin_pivot_x.value()
        py = self.spin_pivot_y.value()
        pz = self.spin_pivot_z.value()
        # Saling link/sync 2D & 3D
        self.canvas_2d.set_pivots(px, py)
        self.canvas_3d.set_pivots(px, py, pz)

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

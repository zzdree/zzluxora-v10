"""
preview_tab.py — Standalone Floating Stage Visualizer Window (2D & 3D with Haze/Smoke)
Provides high-fidelity stage lighting simulation with dynamic RGBW PAR LED beam glows,
3D perspective volumetric beams, overhead truss rigging, atmospheric haze/smoke FX,
interactive camera orbit, and multi-monitor detachable window support.
"""

from __future__ import annotations
import math
import random

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpinBox, QGroupBox, QSplitter, QTabWidget,
    Qt, QPoint, QPointF, QRectF, Signal, QPainter, QColor, QPen, QPolygonF,
    QRadialGradient, QLinearGradient, QBrush, QFont, QTimer
)
from ui.styles import Theme, CONSOLE_QSS


# -----------------------------------------------------------------------------
# 1. 2D STAGE CANVAS (FRONT VIEW WITH TELEMETRY)
# -----------------------------------------------------------------------------
class Stage2DCanvas(QFrame if HAS_QT else object):
    """Front-view 2D Stage Canvas with RGBW beam projection, halos, floor bounce, and fixture telemetry."""
    fixture_selected = Signal(int, int, int)

    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setStyleSheet("background-color: #07080a; border: 1px solid #333844; border-radius: 6px;")
        self.fixtures = [
            {"id": 1, "name": "Alien AL36 #1", "channel_str": "Ch 1–8", "x": 120, "y": 80, "r": 255, "g": 180, "b": 0, "w": 40, "dim": 240},
            {"id": 2, "name": "Alien AL36 #2", "channel_str": "Ch 17–24", "x": 260, "y": 80, "r": 255, "g": 120, "b": 0, "w": 20, "dim": 255},
            {"id": 3, "name": "Alien AL36 #3", "channel_str": "Ch 33–40", "x": 400, "y": 80, "r": 255, "g": 120, "b": 0, "w": 20, "dim": 255},
            {"id": 4, "name": "Alien AL36 #4", "channel_str": "Ch 49–56", "x": 540, "y": 80, "r": 255, "g": 180, "b": 0, "w": 40, "dim": 240},
        ]
        self.selected_idx = 0
        self._drag_active = False

    def set_fixture_color(self, idx: int, r: int, g: int, b: int, w: int, dim: int) -> None:
        if 0 <= idx < len(self.fixtures):
            self.fixtures[idx]["r"] = r
            self.fixtures[idx]["g"] = g
            self.fixtures[idx]["b"] = b
            self.fixtures[idx]["w"] = w
            self.fixtures[idx]["dim"] = dim
            self.update()

    def update_dmx_frame(self, dmx_channels: list[int] | bytearray) -> None:
        """Parses DMX channels for 4 PAR LED fixtures (supports 8-CH Alien at 1,17,33,49, 8-CH contiguous, and 4-CH)."""
        if len(dmx_channels) >= 56 and (dmx_channels[16] > 0 or dmx_channels[32] > 0 or dmx_channels[48] > 0):
            # 16-channel spacing (Alien AL36 GIA stage patch: DMX001, DMX017, DMX033, DMX049)
            bases = [0, 16, 32, 48]
            labels = ["Ch 1–8", "Ch 17–24", "Ch 33–40", "Ch 49–56"]
            for par_idx, base in enumerate(bases):
                dim = dmx_channels[base]
                r = dmx_channels[base + 1]
                g = dmx_channels[base + 2]
                b = dmx_channels[base + 3]
                w = dmx_channels[base + 4]
                self.fixtures[par_idx]["channel_str"] = labels[par_idx]
                self.set_fixture_color(par_idx, r, g, b, w, dim)
        elif len(dmx_channels) >= 32:
            # 8-Channel standard contiguous footprint
            labels = ["Ch 1–8", "Ch 9–16", "Ch 17–24", "Ch 25–32"]
            for par_idx in range(4):
                base = par_idx * 8
                dim = dmx_channels[base]
                r = dmx_channels[base + 1]
                g = dmx_channels[base + 2]
                b = dmx_channels[base + 3]
                w = dmx_channels[base + 4]
                self.fixtures[par_idx]["channel_str"] = labels[par_idx]
                self.set_fixture_color(par_idx, r, g, b, w, dim)
        elif len(dmx_channels) >= 16:
            # 4-Channel legacy fallback
            for par_idx in range(4):
                base = par_idx * 4
                r = dmx_channels[base]
                g = dmx_channels[base + 1]
                b = dmx_channels[base + 2]
                w = dmx_channels[base + 3]
                dim = max(r, g, b, w)
                self.fixtures[par_idx]["channel_str"] = f"Ch {base+1}–{base+4}"
                self.set_fixture_color(par_idx, r, g, b, w, dim)

    def mousePressEvent(self, event) -> None:
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
        if not self._drag_active: return
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

        # 1. Truss Rigging Bar at Top
        pen_truss_main = QPen(QColor("#2d3340"), 6)
        painter.setPen(pen_truss_main)
        painter.drawLine(20, 80, w - 20, 80)
        # Truss diagonal cross bracing
        pen_truss_sub = QPen(QColor("#1e222a"), 2)
        painter.setPen(pen_truss_sub)
        for tx in range(25, w - 25, 40):
            painter.drawLine(tx, 72, tx + 20, 88)
            painter.drawLine(tx + 20, 88, tx + 40, 72)

        # 2. Stage Floor Platform
        painter.fillRect(0, floor_y, w, h - floor_y, QColor("#101319"))
        pen_floor = QPen(QColor(Theme.BORDER_STRONG), 2)
        painter.setPen(pen_floor)
        painter.drawLine(0, floor_y, w, floor_y)

        # 3. Render Fixtures, Volumetric Beams, Floor Pools, and Telemetry
        for idx, fix in enumerate(self.fixtures):
            fx, fy = fix["x"], fix["y"]
            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])
            dim = fix["dim"] / 255.0

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

            # E. Telemetry Badges & Labels beneath fixture
            # Fixture Name & Address
            painter.setFont(QFont("Inter", 8, QFont.Bold))
            painter.setPen(QColor(Theme.TEXT_PRIMARY))
            painter.drawText(QRectF(fx - 60, fy + 22, 120, 14), Qt.AlignCenter, fix["name"])

            # Channel Range & Dimmer %
            painter.setFont(QFont("JetBrains Mono", 8))
            painter.setPen(QColor(Theme.ACCENT_CYAN if is_sel else Theme.TEXT_MUTED))
            ch_str = fix.get("channel_str", f"Ch {idx*8+1}–{idx*8+8}")
            dim_pct = int(dim * 100)
            painter.drawText(QRectF(fx - 60, fy + 36, 120, 14), Qt.AlignCenter, f"{ch_str} | DIM {dim_pct}%")

        painter.end()


# -----------------------------------------------------------------------------
# 2. 3D STAGE CANVAS (PERSPECTIVE 3D WITH VOLUMETRIC BEAMS & HAZE/SMOKE)
# -----------------------------------------------------------------------------
class Stage3DCanvas(QFrame if HAS_QT else object):
    """
    True Perspective 3D Stage Visualizer.
    Features overhead aluminum box-truss, 3D fixture housings, perspective conical volumetric beams,
    stage floor bounce pools, orbit camera (yaw & pitch), and dynamic atmospheric haze/smoke simulation.
    """
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent)
        self.setStyleSheet("background-color: #050608; border: 1px solid #333844; border-radius: 6px;")

        # Camera Orbit Angles (Radians)
        self.yaw = math.radians(-12.0)
        self.pitch = math.radians(24.0)
        self.is_dragging = False
        self.last_mouse_pos = QPoint()

        # Fixture data (3D coordinates relative to stage center: X, Y=height, Z=depth)
        self.fixtures_3d = [
            {"name": "Alien AL36 #1", "ch": "DMX 001", "x": -220, "y": 240, "z": 0, "r": 255, "g": 180, "b": 0, "w": 40, "dim": 240},
            {"name": "Alien AL36 #2", "ch": "DMX 017", "x": -70, "y": 240, "z": 0, "r": 255, "g": 120, "b": 0, "w": 20, "dim": 255},
            {"name": "Alien AL36 #3", "ch": "DMX 033", "x": 70, "y": 240, "z": 0, "r": 255, "g": 120, "b": 0, "w": 20, "dim": 255},
            {"name": "Alien AL36 #4", "ch": "DMX 049", "x": 220, "y": 240, "z": 0, "r": 255, "g": 180, "b": 0, "w": 40, "dim": 240},
        ]

        # Atmospheric Haze / Smoke Simulation State
        self.haze_enabled = True
        self.haze_density = 0.5  # 0.0 to 1.0
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

    def set_haze_enabled(self, enabled: bool) -> None:
        self.haze_enabled = enabled
        if enabled and not self.anim_timer.isActive():
            self.anim_timer.start()
        self.update()

    def reset_camera(self) -> None:
        self.yaw = math.radians(-12.0)
        self.pitch = math.radians(24.0)
        self.update()

    def _on_animation_tick(self) -> None:
        if not self.haze_enabled:
            return
        # Drift smoke particles horizontally and billow gently
        for p in self.smoke_particles:
            p["x"] += p["speed_x"]
            p["phase"] += 0.04
            p["y"] += math.sin(p["phase"]) * 0.4
            if p["x"] > 340:
                p["x"] = -340
                p["y"] = random.uniform(30, 200)
        self.update()

    def update_dmx_frame(self, dmx_channels: list[int] | bytearray) -> None:
        """Parses DMX frame for 3D stage fixtures."""
        if len(dmx_channels) >= 56 and (dmx_channels[16] > 0 or dmx_channels[32] > 0 or dmx_channels[48] > 0):
            bases = [0, 16, 32, 48]
            labels = ["DMX 001", "DMX 017", "DMX 033", "DMX 049"]
            for idx, base in enumerate(bases):
                self.fixtures_3d[idx]["ch"] = labels[idx]
                self.fixtures_3d[idx]["dim"] = dmx_channels[base]
                self.fixtures_3d[idx]["r"] = dmx_channels[base + 1]
                self.fixtures_3d[idx]["g"] = dmx_channels[base + 2]
                self.fixtures_3d[idx]["b"] = dmx_channels[base + 3]
                self.fixtures_3d[idx]["w"] = dmx_channels[base + 4]
        elif len(dmx_channels) >= 32:
            labels = ["DMX 001", "DMX 009", "DMX 017", "DMX 025"]
            for idx in range(4):
                base = idx * 8
                self.fixtures_3d[idx]["ch"] = labels[idx]
                self.fixtures_3d[idx]["dim"] = dmx_channels[base]
                self.fixtures_3d[idx]["r"] = dmx_channels[base + 1]
                self.fixtures_3d[idx]["g"] = dmx_channels[base + 2]
                self.fixtures_3d[idx]["b"] = dmx_channels[base + 3]
                self.fixtures_3d[idx]["w"] = dmx_channels[base + 4]
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.position().toPoint()

    def mouseMoveEvent(self, event) -> None:
        if self.is_dragging:
            cur_pos = event.position().toPoint()
            dx = cur_pos.x() - self.last_mouse_pos.x()
            dy = cur_pos.y() - self.last_mouse_pos.y()
            self.last_mouse_pos = cur_pos

            # Sensitivity
            self.yaw += dx * 0.008
            self.pitch = max(math.radians(10), min(math.radians(70), self.pitch + dy * 0.008))
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def project(self, x: float, y: float, z: float, cx: float, cy: float, fov_scale: float = 460.0) -> tuple[float, float, float]:
        """Projects 3D coordinate (x, y, z) into 2D screen coordinate (sx, sy, depth)."""
        # Yaw rotation (around Y axis)
        cos_y, sin_y = math.cos(self.yaw), math.sin(self.yaw)
        x1 = x * cos_y - z * sin_y
        z1 = x * sin_y + z * cos_y

        # Pitch rotation (around X axis)
        cos_p, sin_p = math.cos(self.pitch), math.sin(self.pitch)
        y1 = y * cos_p - z1 * sin_p
        z2 = y * sin_p + z1 * cos_p + 580.0  # Camera distance

        if z2 <= 20.0: z2 = 20.0
        sx = cx + (x1 * fov_scale) / z2
        sy = cy - (y1 * fov_scale) / z2
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

        # Floor gradient (dark industrial wood finish)
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

        # 2. 3D Overhead Aluminum Box-Truss Rigging
        truss_y = 240.0
        truss_points_front = [(-280, truss_y, -10), (280, truss_y, -10)]
        truss_points_back = [(-280, truss_y + 16, 20), (280, truss_y + 16, 20)]

        tf_s = QPointF(*self.project(*truss_points_front[0], cx, cy)[:2])
        tf_e = QPointF(*self.project(*truss_points_front[1], cx, cy)[:2])
        tb_s = QPointF(*self.project(*truss_points_back[0], cx, cy)[:2])
        tb_e = QPointF(*self.project(*truss_points_back[1], cx, cy)[:2])

        # Draw main truss chord pipes
        pen_pipe = QPen(QColor("#5a6275"), 4)
        painter.setPen(pen_pipe)
        painter.drawLine(tf_s, tf_e)
        painter.drawLine(tb_s, tb_e)

        # Truss diagonal bracing bars
        pen_brace = QPen(QColor("#383e4c"), 1.5)
        painter.setPen(pen_brace)
        for tx in range(-260, 260, 40):
            p1 = QPointF(*self.project(tx, truss_y, -10, cx, cy)[:2])
            p2 = QPointF(*self.project(tx + 20, truss_y + 16, 20, cx, cy)[:2])
            p3 = QPointF(*self.project(tx + 40, truss_y, -10, cx, cy)[:2])
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

            # 3D Lens position
            lx, ly, lz = fix["x"], fix["y"] - 14, fix["z"]
            lens_pt = QPointF(*self.project(lx, ly, lz, cx, cy)[:2])

            # Target position on stage floor
            target_x = fix["x"] * 0.88
            target_z = 25.0

            # 8-point floor ellipse in 3D
            floor_ellipse_pts = []
            radius_x = 55.0
            radius_z = 35.0
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                px = target_x + math.cos(rad) * radius_x
                pz = target_z + math.sin(rad) * radius_z
                floor_ellipse_pts.append(QPointF(*self.project(px, 0, pz, cx, cy)[:2]))

            # A. Volumetric 3D Conical Beam
            beam_polygon = [lens_pt]
            beam_polygon.extend(floor_ellipse_pts)
            beam_polygon.append(floor_ellipse_pts[0])

            # Beam Gradient
            beam_center_floor = QPointF(*self.project(target_x, 0, target_z, cx, cy)[:2])
            beam_grad = QLinearGradient(lens_pt, beam_center_floor)
            beam_grad.setColorAt(0.0, QColor(r, g, b, int(200 * dim)))
            beam_grad.setColorAt(0.4, QColor(r, g, b, int(85 * dim)))
            beam_grad.setColorAt(1.0, QColor(r, g, b, int(15 * dim)))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(beam_grad))
            painter.drawPolygon(QPolygonF(beam_polygon))

            # B. Floor Reflection Pool
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
                    smoke_rad.setColorAt(0.5, QColor(160, 180, 210, int(alpha * 0.4)))
                    smoke_rad.setColorAt(1.0, QColor(120, 140, 180, 0))

                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(smoke_rad))
                    painter.drawEllipse(QPointF(sx, sy), radius_proj, radius_proj * 0.7)

        # 5. 3D Fixture Head Housings & Labels
        for fix in self.fixtures_3d:
            lx, ly, lz = fix["x"], fix["y"], fix["z"]
            head_sx, head_sy, head_sz = self.project(lx, ly, lz, cx, cy)
            scale = 450.0 / head_sz

            r = min(255, fix["r"] + fix["w"])
            g = min(255, fix["g"] + fix["w"])
            b = min(255, fix["b"] + fix["w"])
            dim = fix["dim"] / 255.0

            # Suspension Coupler
            painter.setPen(QPen(QColor("#717b8f"), 2))
            painter.drawLine(QPointF(head_sx, head_sy - 16 * scale), QPointF(head_sx, head_sy - 4 * scale))

            # Yoke Bracket
            painter.setPen(QPen(QColor("#404654"), 2.5))
            yoke_rect = QRectF(head_sx - 14 * scale, head_sy - 6 * scale, 28 * scale, 22 * scale)
            painter.drawArc(yoke_rect, 0, 180 * 16)

            # Fixture Body Cylinder
            body_radius = 16 * scale
            painter.setPen(QPen(QColor(Theme.ACCENT_AMBER if dim > 0.1 else Theme.BORDER_STRONG), 1.5))
            painter.setBrush(QColor("#14171f"))
            painter.drawEllipse(QPointF(head_sx, head_sy), body_radius, body_radius)

            # Lens Face Emitter (Emits physical color)
            lens_color = QColor(r, g, b, int(255 * max(0.2, dim)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(lens_color))
            painter.drawEllipse(QPointF(head_sx, head_sy + 2 * scale), body_radius * 0.65, body_radius * 0.65)

            # Fixture Telemetry Label
            painter.setFont(QFont("Inter", max(7, int(8 * scale)), QFont.Bold))
            painter.setPen(QColor(Theme.TEXT_PRIMARY))
            painter.drawText(
                QRectF(head_sx - 50, head_sy - 30 * scale, 100, 16),
                Qt.AlignCenter,
                f"{fix['name']}"
            )
            painter.setFont(QFont("JetBrains Mono", max(6, int(7 * scale))))
            painter.setPen(QColor(Theme.ACCENT_CYAN))
            painter.drawText(
                QRectF(head_sx - 50, head_sy - 18 * scale, 100, 14),
                Qt.AlignCenter,
                f"{fix['ch']} | {int(dim*100)}%"
            )

        # 6. Bottom Camera Hint
        painter.setFont(QFont("Inter", 8))
        painter.setPen(QColor(Theme.TEXT_MUTED))
        painter.drawText(QRectF(15, h - 25, 300, 20), Qt.AlignLeft, "3D Camera: Drag mouse untuk orbit panggung")

        painter.end()


# -----------------------------------------------------------------------------
# 3. STANDALONE STAGE VISUALIZER WINDOW (2D & 3D MULTI-TAB)
# -----------------------------------------------------------------------------
class StageVisualizerWindow(QWidget if HAS_QT else object):
    """
    Standalone Floating Window for Stage Lighting Visualization.
    Features dual-tabbed 2D Front View and 3D Perspective Stage with Haze Simulation.
    """
    def __init__(self, parent: QWidget | None = None):
        if not HAS_QT: return
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("Stage Visualizer (2D & 3D): ZZLUXORA")
        self.resize(880, 580)
        self.setStyleSheet(CONSOLE_QSS)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(10)

        # Top Control Bar
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("STAGE LIGHTING VISUALIZER (2D & 3D PERSPECTIVE)")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {Theme.TEXT_PRIMARY};")
        lbl_desc = QLabel("Simulasi Pencahayaan Panggung GIA Deliksari | Volumetric Beams, Truss Rigging, & Atmospheric Haze FX")
        lbl_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_desc)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_toggle_haze = QPushButton("HAZE FX: ON")
        self.btn_toggle_haze.setStyleSheet(f"background-color: #143521; color: {Theme.COLOR_SUCCESS}; font-weight: 800;")
        self.btn_toggle_haze.clicked.connect(self._on_toggle_haze)
        top_bar.addWidget(self.btn_toggle_haze)

        self.btn_reset_cam = QPushButton("RESET CAMERA")
        self.btn_reset_cam.clicked.connect(self._on_reset_camera)
        top_bar.addWidget(self.btn_reset_cam)

        self.btn_close = QPushButton("CLOSE")
        self.btn_close.clicked.connect(self.close)
        top_bar.addWidget(self.btn_close)

        main_layout.addLayout(top_bar)

        # Central Visualizer Tabs: 2D Front View vs 3D Perspective
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
                padding: 6px 16px;
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

        # Tab 1: 3D Perspective Stage View (Primary Visualizer)
        self.canvas_3d = Stage3DCanvas(self)
        self.tabs.addTab(self.canvas_3d, "3D PERSPECTIVE STAGE (VOLUMETRIC & HAZE)")

        # Tab 2: 2D Front View (Precision Rigging Layout)
        self.canvas_2d = Stage2DCanvas(self)
        self.tabs.addTab(self.canvas_2d, "2D FRONT VIEW (RIGGING & TELEMETRY)")

        main_layout.addWidget(self.tabs, 1)

    def _on_toggle_haze(self) -> None:
        new_state = not self.canvas_3d.haze_enabled
        self.canvas_3d.set_haze_enabled(new_state)
        if new_state:
            self.btn_toggle_haze.setText("HAZE FX: ON")
            self.btn_toggle_haze.setStyleSheet(f"background-color: #143521; color: {Theme.COLOR_SUCCESS}; font-weight: 800;")
        else:
            self.btn_toggle_haze.setText("HAZE FX: OFF")
            self.btn_toggle_haze.setStyleSheet(f"background-color: {Theme.BG_SURFACE}; color: {Theme.TEXT_MUTED}; font-weight: 700;")

    def _on_reset_camera(self) -> None:
        self.canvas_3d.reset_camera()

    def update_dmx(self, channels: list[int] | bytearray) -> None:
        """Pushes DMX channels to both 2D and 3D visualizer canvases in real time."""
        if hasattr(self, 'canvas_2d'):
            self.canvas_2d.update_dmx_frame(channels)
        if hasattr(self, 'canvas_3d'):
            self.canvas_3d.update_dmx_frame(channels)

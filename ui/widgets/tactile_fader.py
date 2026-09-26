"""
tactile_fader.py — grandMA3 Tactile Stage Lighting Console Fader Widget
Custom QWidget implementation with illuminated groove rails, analog calibration tick marks,
tactile ribbed cap, and precision DMX readout (0-255).
"""

from __future__ import annotations

from ui.qt_compat import (
    HAS_QT, QWidget, QVBoxLayout, QLabel, QLineEdit, QInputDialog,
    Qt, Signal, QRectF, QPointF, QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
)
from ui.styles import Theme


class TactileFader(QWidget if HAS_QT else object):
    """
    High-precision stage lighting fader emulating grandMA3 console hardware.
    Features illuminated LED track groove, tactile cap with center notch,
    analog calibration scale, and direct DMX value input.
    """
    valueChanged = Signal(int, int)  # (channel_id, new_value)

    def __init__(
        self,
        channel_id: int,
        label: str = "",
        initial_value: int = 0,
        is_master: bool = False,
        parent: QWidget | None = None,
    ):
        if not HAS_QT: return
        super().__init__(parent)
        self.channel_id = channel_id
        self.label_text = label if label else ("MASTER" if is_master else f"Ch {channel_id}")
        self._value = max(0, min(255, initial_value))
        self.is_master = is_master
        self.is_dragging = False

        self.setFixedWidth(56)
        self.setMinimumHeight(240)
        self.setFocusPolicy(Qt.StrongFocus)

        # Cap & Track dimensions
        self.cap_width = 34
        self.cap_height = 20
        self.track_width = 4
        self.top_margin = 24
        self.bottom_margin = 46

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        clamped = max(0, min(255, int(val)))
        if clamped != self._value:
            self._value = clamped
            self.update()
            self.valueChanged.emit(self.channel_id, self._value)

    def set_value_silent(self, val: int) -> None:
        """Sets fader value without emitting valueChanged signal (prevents loopback)."""
        clamped = max(0, min(255, int(val)))
        if clamped != self._value:
            self._value = clamped
            self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            # Check if clicked on bottom readout area -> direct value edit
            if event.position().y() >= self.height() - self.bottom_margin:
                self._open_direct_input()
                return

            self.is_dragging = True
            self._update_from_mouse_y(event.position().y())

    def mouseMoveEvent(self, event) -> None:
        if self.is_dragging:
            self._update_from_mouse_y(event.position().y())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def wheelEvent(self, event) -> None:
        delta = 5 if event.angleDelta().y() > 0 else -5
        self.value = self._value + delta

    def mouseDoubleClickEvent(self, event) -> None:
        self._open_direct_input()

    def _open_direct_input(self) -> None:
        val, ok = QInputDialog.getInt(
            self,
            f"Set Nilai DMX: {self.label_text}",
            "Nilai DMX (0 - 255):",
            self._value,
            0,
            255,
            1,
        )
        if ok:
            self.value = val

    def _track_y_bounds(self) -> tuple[float, float]:
        """Returns (y_top, y_bottom) for the center of the cap."""
        y_top = float(self.top_margin + self.cap_height / 2)
        y_bottom = float(self.height() - self.bottom_margin - self.cap_height / 2)
        return y_top, y_bottom

    def _update_from_mouse_y(self, mouse_y: float) -> None:
        y_top, y_bottom = self._track_y_bounds()
        track_len = y_bottom - y_top
        if track_len <= 0:
            return

        # Clamp mouse_y to track bounds
        clamped_y = max(y_top, min(y_bottom, mouse_y))
        # Top is 255, Bottom is 0
        norm = 1.0 - ((clamped_y - y_top) / track_len)
        self.value = int(round(norm * 255.0))

    def _cap_center_y(self) -> float:
        y_top, y_bottom = self._track_y_bounds()
        track_len = y_bottom - y_top
        norm = self._value / 255.0
        return y_bottom - (norm * track_len)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        y_top, y_bottom = self._track_y_bounds()

        # 1. Background fill
        painter.fillRect(0, 0, w, h, QColor(Theme.BG_ROOT))

        # 2. Header Label (Top)
        painter.setFont(QFont("Inter", 8, QFont.Bold))
        painter.setPen(QColor(Theme.ACCENT_AMBER if self.is_master else Theme.TEXT_SECONDARY))
        painter.drawText(
            QRectF(0, 4, w, 16),
            Qt.AlignCenter,
            "MASTER" if self.is_master else f"{self.channel_id}",
        )

        # 3. Analog Calibration Scale Lines (Tick Marks)
        pen_tick = QPen(QColor(Theme.BORDER_STRONG))
        pen_tick.setWidth(1)
        painter.setPen(pen_tick)

        track_len = y_bottom - y_top
        for step in [0.0, 0.25, 0.5, 0.75, 1.0]:
            ty = y_bottom - (step * track_len)
            is_major = step in (0.0, 0.5, 1.0)
            tick_w = 6 if is_major else 3
            if is_major:
                painter.setPen(QPen(QColor("#64748b"), 1.5))
            else:
                painter.setPen(QPen(QColor("#383e4c"), 1.0))

            # Left and Right ticks
            painter.drawLine(QPointF(cx - 14 - tick_w, ty), QPointF(cx - 14, ty))
            painter.drawLine(QPointF(cx + 14, ty), QPointF(cx + 14 + tick_w, ty))

        # 4. Fader Groove / Recessed Track
        track_rect = QRectF(cx - self.track_width / 2.0, y_top - 2, self.track_width, track_len + 4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(Theme.BG_FADER_GROOVE))
        painter.drawRoundedRect(track_rect, 2, 2)

        # 5. Illuminated LED Groove (Level Fill from bottom up to cap)
        cap_y = self._cap_center_y()
        led_height = y_bottom - cap_y
        if led_height > 0:
            led_color = QColor(Theme.ACCENT_AMBER if self.is_master else Theme.ACCENT_CYAN)
            led_rect = QRectF(cx - (self.track_width / 2.0), cap_y, self.track_width, led_height)
            painter.setBrush(QBrush(led_color))
            painter.drawRoundedRect(led_rect, 1.5, 1.5)

        # 6. Tactile Ribbed Fader Cap
        cap_left = cx - self.cap_width / 2.0
        cap_top = cap_y - self.cap_height / 2.0
        cap_rect = QRectF(cap_left, cap_top, self.cap_width, self.cap_height)

        # Gradient body
        grad = QLinearGradient(cap_left, cap_top, cap_left, cap_top + self.cap_height)
        grad.setColorAt(0.0, QColor("#434a58"))
        grad.setColorAt(0.5, QColor(Theme.BG_FADER_CAP))
        grad.setColorAt(1.0, QColor("#22262e"))

        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(Theme.BORDER_STRONG), 1))
        painter.drawRoundedRect(cap_rect, 3, 3)

        # Ribbed Texture Grooves (horizontal tactile lines on sides)
        painter.setPen(QPen(QColor("#22262e"), 1))
        for offset_y in [-5, -2, 2, 5]:
            # Left ribs
            painter.drawLine(
                QPointF(cap_left + 3, cap_y + offset_y),
                QPointF(cap_left + 8, cap_y + offset_y),
            )
            # Right ribs
            painter.drawLine(
                QPointF(cap_left + self.cap_width - 8, cap_y + offset_y),
                QPointF(cap_left + self.cap_width - 3, cap_y + offset_y),
            )

        # Center White Indicator Notch Line
        painter.setPen(QPen(QColor(Theme.TEXT_PRIMARY), 2))
        painter.drawLine(
            QPointF(cap_left + 7, cap_y),
            QPointF(cap_left + self.cap_width - 7, cap_y),
        )

        # 7. Bottom Value Box (0-255 Readout)
        val_box_rect = QRectF(4, h - self.bottom_margin + 6, w - 8, 22)
        painter.setPen(QPen(QColor(Theme.BORDER_SUBTLE), 1))
        painter.setBrush(QColor(Theme.BG_INPUT))
        painter.drawRoundedRect(val_box_rect, 3, 3)

        painter.setFont(QFont("JetBrains Mono", 9, QFont.Bold))
        painter.setPen(QColor(Theme.TEXT_PRIMARY))
        painter.drawText(val_box_rect, Qt.AlignCenter, f"{self._value}")

        # Sub-label at very bottom (e.g. channel function if available)
        painter.setFont(QFont("Inter", 7))
        painter.setPen(QColor(Theme.TEXT_MUTED))
        sub_label = self.label_text[:8] if not self.is_master else "DIM"
        painter.drawText(QRectF(2, h - 16, w - 4, 14), Qt.AlignCenter, sub_label)

        painter.end()

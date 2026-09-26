"""
qt_compat.py — Universal Qt6 Binding Compatibility Layer (PySide6 / PyQt6)
Enables ZZLUXORA v10 to run seamlessly across environments with either PySide6 or PyQt6.
Includes enum promotion to guarantee 100% API parity between Qt6 bindings.
"""

from __future__ import annotations

HAS_QT = True
try:
    import PySide6
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import (
        Qt, QTimer, QSize, QPoint, QPointF, QRect, QRectF,
        Signal, Slot, QThread, QMimeData
    )
    from PySide6.QtGui import (
        QColor, QPen, QBrush, QPainter, QLinearGradient, QRadialGradient,
        QFont, QIcon, QPixmap, QAction, QKeySequence, QDrag,
        QDragEnterEvent, QDropEvent
    )
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout,
        QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
        QStackedWidget, QMenuBar, QMenu, QFileDialog, QMessageBox,
        QTableWidget, QTableWidgetItem, QHeaderView, QListWidget,
        QListWidgetItem, QScrollArea, QSplitter, QGroupBox, QLineEdit,
        QSpinBox, QDoubleSpinBox, QComboBox, QProgressBar, QTextEdit,
        QButtonGroup, QInputDialog, QTabWidget
    )
    QT_BINDING = "PySide6"
except ImportError:
    try:
        import PyQt6
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import (
            Qt, QTimer, QSize, QPoint, QPointF, QRect, QRectF,
            pyqtSignal as Signal, pyqtSlot as Slot, QThread, QMimeData
        )
        from PyQt6.QtGui import (
            QColor, QPen, QBrush, QPainter, QLinearGradient, QRadialGradient,
            QFont, QIcon, QPixmap, QAction, QKeySequence, QDrag,
            QDragEnterEvent, QDropEvent
        )
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout,
            QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
            QStackedWidget, QMenuBar, QMenu, QFileDialog, QMessageBox,
            QTableWidget, QTableWidgetItem, QHeaderView, QListWidget,
            QListWidgetItem, QScrollArea, QSplitter, QGroupBox, QLineEdit,
            QSpinBox, QDoubleSpinBox, QComboBox, QProgressBar, QTextEdit,
            QButtonGroup, QInputDialog, QTabWidget
        )

        # Promote PyQt6 scoped enums onto parent classes for 100% PySide parity
        def _promote_enums(target, enums):
            for enum_cls in enums:
                for name, val in enum_cls.__members__.items():
                    if not hasattr(target, name):
                        try:
                            setattr(target, name, val)
                        except Exception:
                            pass

        _promote_enums(QtCore.Qt, [
            QtCore.Qt.AlignmentFlag, QtCore.Qt.Orientation, QtCore.Qt.PenStyle,
            QtCore.Qt.BrushStyle, QtCore.Qt.AspectRatioMode, QtCore.Qt.TransformationMode,
            QtCore.Qt.MouseButton, QtCore.Qt.WindowType, QtCore.Qt.DropAction,
            QtCore.Qt.ItemDataRole, QtCore.Qt.ScrollBarPolicy, QtCore.Qt.Key,
            QtCore.Qt.FocusPolicy, QtCore.Qt.ItemFlag
        ])
        _promote_enums(QtGui.QPainter, [QtGui.QPainter.RenderHint])
        _promote_enums(QtGui.QFont, [QtGui.QFont.Weight])
        _promote_enums(QtWidgets.QHeaderView, [QtWidgets.QHeaderView.ResizeMode])
        _promote_enums(QtWidgets.QMessageBox, [QtWidgets.QMessageBox.StandardButton])

        QT_BINDING = "PyQt6"
    except ImportError:
        HAS_QT = False
        QT_BINDING = "None"
        class QWidget: pass
        class QMainWindow: pass
        class QDialog: pass
        class QFrame: pass
        class QThread: pass
        class Signal:
            def __init__(self, *args, **kwargs): pass
            def emit(self, *args, **kwargs): pass
            def connect(self, *args, **kwargs): pass

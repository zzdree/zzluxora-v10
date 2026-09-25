"""
styles.py — Dark Industrial Lighting Console Styling Tokens and QSS
Inspired by grandMA3 lighting consoles and QLC+ utility.
"""

class Theme:
    # Backgrounds
    BG_ROOT = "#0e1013"
    BG_SURFACE = "#16181d"
    BG_PANEL = "#1d2127"
    BG_CARD = "#242832"
    BG_INPUT = "#121417"

    # Borders & Dividers
    BORDER_SUBTLE = "#282c34"
    BORDER_STRONG = "#3e4451"
    BORDER_FOCUS = "#00bcd4"

    # Accents & Functional Colors
    ACCENT_CYAN = "#00e5ff"
    ACCENT_AMBER = "#ffb300"
    COLOR_SUCCESS = "#00e676"  # Art-Net connected
    COLOR_DANGER = "#ff1744"   # Art-Net disconnected / Blackout
    COLOR_WARNING = "#ff9100"

    # Typography
    TEXT_PRIMARY = "#f0f2f5"
    TEXT_SECONDARY = "#abb2bf"
    TEXT_MUTED = "#5c6370"

    # DMX Channel Semantic Colors
    CH_DIMMER = "#ffd54f"
    CH_RED = "#ff5252"
    CH_GREEN = "#69f0ae"
    CH_BLUE = "#448aff"
    CH_WHITE = "#ffffff"
    CH_AMBER = "#ffab40"
    CH_STROBE = "#ea80fc"
    CH_EMPTY = "#21252b"

CONSOLE_QSS = f"""
QMainWindow {{
    background-color: {Theme.BG_ROOT};
    color: {Theme.TEXT_PRIMARY};
}}

QWidget {{
    background-color: {Theme.BG_ROOT};
    color: {Theme.TEXT_PRIMARY};
    font-family: "Segoe UI", "Roboto", "Ubuntu", sans-serif;
    font-size: 13px;
}}

/* Header Bar */
QFrame#HeaderBar {{
    background-color: {Theme.BG_SURFACE};
    border-bottom: 1px solid {Theme.BORDER_SUBTLE};
    padding: 6px 12px;
}}

QLabel#LogoTitle {{
    font-size: 15px;
    font-weight: bold;
    color: {Theme.TEXT_PRIMARY};
    letter-spacing: 1px;
}}

QLabel#ProjectPath {{
    font-size: 12px;
    color: {Theme.TEXT_MUTED};
    font-style: italic;
}}

/* Art-Net Indicator */
QLabel#ArtNetStatusConnected {{
    color: {Theme.COLOR_SUCCESS};
    font-weight: bold;
    font-size: 12px;
}}

QLabel#ArtNetStatusDisconnected {{
    color: {Theme.COLOR_DANGER};
    font-weight: bold;
    font-size: 12px;
}}

/* Buttons */
QPushButton {{
    background-color: {Theme.BG_PANEL};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 4px;
    color: {Theme.TEXT_PRIMARY};
    padding: 6px 14px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {Theme.BG_CARD};
    border-color: {Theme.ACCENT_CYAN};
}}

QPushButton:pressed {{
    background-color: {Theme.BORDER_SUBTLE};
}}

QPushButton:disabled {{
    background-color: {Theme.BG_ROOT};
    border-color: {Theme.BORDER_SUBTLE};
    color: {Theme.TEXT_MUTED};
}}

/* Blackout Button */
QPushButton#BlackoutBtn {{
    background-color: #2b0d13;
    border: 1px solid {Theme.COLOR_DANGER};
    color: {Theme.COLOR_DANGER};
    border-radius: 14px;
    font-weight: bold;
    padding: 6px 16px;
}}

QPushButton#BlackoutBtn:hover {{
    background-color: {Theme.COLOR_DANGER};
    color: #ffffff;
}}

/* Play/Pause Button */
QPushButton#PlayPauseBtn {{
    background-color: #0d2621;
    border: 1px solid {Theme.COLOR_SUCCESS};
    color: {Theme.COLOR_SUCCESS};
    border-radius: 4px;
    font-weight: bold;
    padding: 6px 14px;
}}

QPushButton#PlayPauseBtn:hover {{
    background-color: {Theme.COLOR_SUCCESS};
    color: #000000;
}}

/* Tab Widget (grandMA3 style) */
QTabWidget::pane {{
    border: 1px solid {Theme.BORDER_SUBTLE};
    background-color: {Theme.BG_SURFACE};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {Theme.BG_ROOT};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-bottom: none;
    color: {Theme.TEXT_SECONDARY};
    padding: 8px 18px;
    font-weight: 600;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {Theme.BG_SURFACE};
    border-top: 2px solid {Theme.ACCENT_CYAN};
    color: {Theme.TEXT_PRIMARY};
}}

QTabBar::tab:hover:!selected {{
    background-color: {Theme.BG_PANEL};
    color: {Theme.TEXT_PRIMARY};
}}

/* Sliders (Industrial Faders) */
QSlider::groove:vertical {{
    background: {Theme.BG_INPUT};
    width: 8px;
    border-radius: 4px;
    border: 1px solid {Theme.BORDER_SUBTLE};
}}

QSlider::sub-page:vertical {{
    background: {Theme.ACCENT_CYAN};
    border-radius: 4px;
}}

QSlider::add-page:vertical {{
    background: {Theme.BG_INPUT};
    border-radius: 4px;
}}

QSlider::handle:vertical {{
    background: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER_STRONG};
    height: 22px;
    margin: 0 -8px;
    border-radius: 3px;
}}

QSlider::handle:vertical:hover {{
    background: {Theme.ACCENT_AMBER};
}}

/* Scrollbars */
QScrollBar:horizontal {{
    background: {Theme.BG_ROOT};
    height: 10px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {Theme.BORDER_STRONG};
    min-width: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {Theme.ACCENT_CYAN};
}}

QScrollBar:vertical {{
    background: {Theme.BG_ROOT};
    width: 10px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {Theme.BORDER_STRONG};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Theme.ACCENT_CYAN};
}}

/* Progress Bar */
QProgressBar {{
    background-color: {Theme.BG_INPUT};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: 4px;
    text-align: center;
    color: {Theme.TEXT_PRIMARY};
    font-weight: bold;
    height: 20px;
}}

QProgressBar::chunk {{
    background-color: {Theme.ACCENT_CYAN};
    border-radius: 3px;
}}

/* Tables */
QTableWidget {{
    background-color: {Theme.BG_SURFACE};
    border: 1px solid {Theme.BORDER_SUBTLE};
    gridline-color: {Theme.BORDER_SUBTLE};
    color: {Theme.TEXT_PRIMARY};
}}

QHeaderView::section {{
    background-color: {Theme.BG_PANEL};
    border: 1px solid {Theme.BORDER_SUBTLE};
    color: {Theme.TEXT_SECONDARY};
    padding: 6px;
    font-weight: bold;
}}
"""

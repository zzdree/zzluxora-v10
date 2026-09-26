"""
styles.py — Pure Dark Grey & High-Contrast White Theme (grandMA3 Industrial Console)
Refined for ZZLUXORA v10.0.0 based on Feedback v3.
"""

class Theme:
    # Pure Dark Grey Backgrounds (Industrial Stage Console)
    BG_ROOT = "#1e2024"             # Root window background (Deep Charcoal Grey)
    BG_SURFACE = "#242830"          # Panels, cards, and tab containers
    BG_ELEVATED = "#2d323c"         # Headers, dialogs, floating windows
    BG_FADER_GROOVE = "#14161a"     # Recessed dark fader groove rail
    BG_FADER_CAP = "#353b47"        # Tactile ribbed fader cap
    BG_INPUT = "#181a1f"            # Text inputs, combo boxes

    # Borders & Dividers
    BORDER_SUBTLE = "#333844"       # Subtle divider lines
    BORDER_STRONG = "#4a5264"       # Active / focused borders
    BORDER_HIGHLIGHT = "#06b6d4"    # Focus neon cyan outline

    # Accents & Functional Colors (grandMA3 Inspired)
    ACCENT_AMBER = "#f59e0b"        # grandMA Amber Gold (Master Dimmer & active tab line)
    ACCENT_CYAN = "#06b6d4"         # Neon Cyan Glow (DMX channel fader rails)
    COLOR_SUCCESS = "#22c55e"       # Art-Net connected / transmitting (Green)
    COLOR_DANGER = "#ef4444"        # Art-Net disconnected / blackout outline (Red)
    COLOR_WARNING = "#eab308"       # Onset / Strobe / Shutter flash

    # Typography (High Contrast White)
    TEXT_PRIMARY = "#ffffff"        # Pure Crisp White for maximum stage readability
    TEXT_SECONDARY = "#cbd5e1"      # Light grey for labels, subheadings, file paths
    TEXT_MUTED = "#94a3b8"          # Dim grey for placeholders & unpatched numbers

    # DMX Channel Semantic Colors (Grid & Mixer Sync)
    CH_DIMMER = "#d97706"           # Amber Gold
    CH_RED = "#dc2626"              # Pure Red
    CH_GREEN = "#16a34a"            # Vivid Green
    CH_BLUE = "#2563eb"             # Royal Blue
    CH_WHITE = "#f8fafc"            # Neutral Stage White
    CH_STROBE = "#eab308"           # Electric Flash Yellow
    CH_PAN_TILT = "#8b5cf6"         # Violet Moving Head
    CH_COLOR_MACRO = "#ec4899"      # Rainbow Macro
    CH_EMPTY = "#282c34"            # Dark Grey Unpatched Cell


CONSOLE_QSS = f"""
QMainWindow, QDialog {{
    background-color: {Theme.BG_ROOT};
    color: {Theme.TEXT_PRIMARY};
}}

QWidget {{
    background-color: {Theme.BG_ROOT};
    color: {Theme.TEXT_PRIMARY};
    font-family: "Inter", "Segoe UI", "Roboto", "Ubuntu", sans-serif;
    font-size: 13px;
}}

/* Level 1: App Title Bar */
QFrame#TitleBarFrame {{
    background-color: {Theme.BG_ROOT};
    border-bottom: 1px solid {Theme.BORDER_SUBTLE};
    padding: 2px 10px;
}}

QLabel#AppTitleLabel {{
    font-size: 14px;
    font-weight: 800;
    color: {Theme.TEXT_PRIMARY};
    letter-spacing: 1px;
}}

QLabel#ProjectPathLabel {{
    font-size: 12px;
    color: {Theme.TEXT_SECONDARY};
    font-family: "JetBrains Mono", "Consolas", monospace;
}}

/* Level 2: Menu Bar */
QMenuBar {{
    background-color: {Theme.BG_SURFACE};
    border-bottom: 1px solid {Theme.BORDER_SUBTLE};
    color: {Theme.TEXT_PRIMARY};
    padding: 3px 6px;
    font-weight: 600;
}}

QMenuBar::item {{
    background: transparent;
    padding: 5px 12px;
    border-radius: 4px;
    color: {Theme.TEXT_PRIMARY};
}}

QMenuBar::item:selected {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.ACCENT_CYAN};
}}

QMenu {{
    background-color: {Theme.BG_ELEVATED};
    border: 1px solid {Theme.BORDER_STRONG};
    color: {Theme.TEXT_PRIMARY};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 20px;
    border-radius: 3px;
}}

QMenu::item:selected {{
    background-color: {Theme.ACCENT_CYAN};
    color: {Theme.BG_ROOT};
    font-weight: bold;
}}

/* Level 3: Program View Bar */
QFrame#ProgramBarFrame {{
    background-color: {Theme.BG_SURFACE};
    border-bottom: 2px solid {Theme.BORDER_SUBTLE};
    padding: 4px 12px;
}}

/* Program Workspace Tab Buttons */
QPushButton.ProgramTabBtn {{
    background-color: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    color: {Theme.TEXT_SECONDARY};
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 700;
}}

QPushButton.ProgramTabBtn:hover {{
    color: {Theme.TEXT_PRIMARY};
    background-color: {Theme.BG_ELEVATED};
}}

QPushButton.ProgramTabBtn:checked {{
    color: {Theme.TEXT_PRIMARY};
    border-bottom: 3px solid {Theme.ACCENT_AMBER};
    background-color: {Theme.BG_ELEVATED};
}}

/* Telemetry: Art-Net Badge */
QPushButton#ArtNetBadgeBtn {{
    border-radius: 3px;
    padding: 5px 12px;
    font-weight: 800;
    font-size: 11px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    border: 1px solid {Theme.BORDER_STRONG};
}}

QPushButton#ArtNetBadgeBtn[connected="true"] {{
    background-color: #143521;
    color: {Theme.COLOR_SUCCESS};
    border: 1px solid {Theme.COLOR_SUCCESS};
}}

QPushButton#ArtNetBadgeBtn[connected="false"] {{
    background-color: #3b161c;
    color: {Theme.COLOR_DANGER};
    border: 1px solid {Theme.COLOR_DANGER};
}}

/* Master Blackout Button */
QPushButton#BlackoutBtn {{
    background-color: #000000;
    color: {Theme.COLOR_DANGER};
    border: 2px solid {Theme.COLOR_DANGER};
    border-radius: 3px;
    padding: 5px 14px;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 0.5px;
}}

QPushButton#BlackoutBtn:hover {{
    background-color: {Theme.COLOR_DANGER};
    color: #ffffff;
}}

/* Play / Stop Toggle Button */
QPushButton#PlayStopToggleBtn {{
    border-radius: 4px;
    padding: 5px 16px;
    font-weight: bold;
    font-size: 12px;
}}

QPushButton#PlayStopToggleBtn[state="play"] {{
    background-color: #166534;
    color: #ffffff;
    border: 1px solid {Theme.COLOR_SUCCESS};
}}

QPushButton#PlayStopToggleBtn[state="play"]:hover {{
    background-color: {Theme.COLOR_SUCCESS};
    color: #000000;
}}

QPushButton#PlayStopToggleBtn[state="stop"] {{
    background-color: #991b1b;
    color: #ffffff;
    border: 1px solid {Theme.COLOR_DANGER};
}}

QPushButton#PlayStopToggleBtn[state="stop"]:hover {{
    background-color: {Theme.COLOR_DANGER};
    color: #ffffff;
}}

/* Standard Buttons */
QPushButton {{
    background-color: {Theme.BG_ELEVATED};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 4px;
    color: {Theme.TEXT_PRIMARY};
    padding: 6px 14px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #383f4d;
    border-color: {Theme.ACCENT_CYAN};
}}

QPushButton:pressed {{
    background-color: {Theme.ACCENT_CYAN};
    color: #000000;
}}

QPushButton:disabled {{
    background-color: #1a1c22;
    color: {Theme.TEXT_MUTED};
    border-color: {Theme.BORDER_SUBTLE};
}}

/* Scrollbars */
QScrollBar:horizontal {{
    background: {Theme.BG_ROOT};
    height: 10px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {Theme.BORDER_STRONG};
    min-width: 24px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {Theme.ACCENT_CYAN};
}}

QScrollBar:vertical {{
    background: {Theme.BG_ROOT};
    width: 10px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {Theme.BORDER_STRONG};
    min-height: 24px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Theme.ACCENT_CYAN};
}}

/* Input controls */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {Theme.BG_INPUT};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 4px;
    color: {Theme.TEXT_PRIMARY};
    padding: 6px 10px;
    font-size: 13px;
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {Theme.ACCENT_CYAN};
}}

/* Table Widget */
QTableWidget {{
    background-color: {Theme.BG_SURFACE};
    border: 1px solid {Theme.BORDER_SUBTLE};
    gridline-color: {Theme.BORDER_SUBTLE};
    color: {Theme.TEXT_PRIMARY};
}}

QHeaderView::section {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.TEXT_PRIMARY};
    padding: 6px;
    border: 1px solid {Theme.BORDER_SUBTLE};
    font-weight: bold;
}}
"""

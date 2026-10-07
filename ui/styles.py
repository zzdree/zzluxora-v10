"""
styles.py | Pure Dark Grey & High-Contrast White Theme (grandMA3 Industrial Console)
Refined for ZZLUXORA v10.0.0 based on Impeccable Design System ("The Obsidian Control Deck").
"""

from __future__ import annotations


class Theme:
    # -------------------------------------------------------------------------
    # 1. Surface & Chassis Ramp (Matte Obsidian Metal)
    # -------------------------------------------------------------------------
    BG_ROOT = "#1e2024"                 # Root window background (Deep Charcoal Grey)
    BG_SURFACE = "#242830"              # Panels, cards, and tab containers
    BG_ELEVATED = "#2d323c"             # Headers, dialogs, floating windows
    SURFACE_VOID = "#07080a"            # Deepest stage visualizer viewport canvas
    SURFACE_OBSIDIAN = "#101319"        # Stage floor platform
    SURFACE_TROUGH = "#14161a"          # Recessed fader groove rail and cable paths
    SURFACE_INPUT = "#181a1f"           # Inputs, table bases, list widgets
    SURFACE_HOVER = "#383f4d"           # Button hover state
    SURFACE_CAP = "#353b47"             # Tactile fader cap body

    # Aliases for existing backward compatibility
    BG_FADER_GROOVE = SURFACE_TROUGH
    BG_FADER_CAP = SURFACE_CAP
    BG_INPUT = SURFACE_INPUT

    # -------------------------------------------------------------------------
    # 2. Borders & Dividers
    # -------------------------------------------------------------------------
    BORDER_SUBTLE = "#333844"           # Subtle divider lines & container outlines
    BORDER_STRONG = "#4a5264"           # Active / focused borders
    BORDER_HIGHLIGHT = "#06b6d4"        # Focus neon cyan outline
    BLACKOUT_SURFACE = "#000000"        # Blackout control surface, true zero-output state
    CONTROL_DISABLED_BG = "#1a1c22"     # Disabled Qt control surface

    # -------------------------------------------------------------------------
    # 3. Accents & Functional Colors (The 10% Accent Rule)
    # -------------------------------------------------------------------------
    ACCENT_AMBER = "#f59e0b"            # grandMA Amber Gold (Master Dimmer & active tab indicator)
    ACCENT_CYAN = "#06b6d4"             # Neon Cyan Glow (Channel rails, focus rings & telemetry)
    COLOR_SUCCESS = "#22c55e"           # Art-Net connected / live transmitting (Green)
    COLOR_DANGER = "#ef4444"            # Blackout / disconnect / error (Red)
    COLOR_WARNING = "#eab308"           # Onset / Strobe / Shutter flash (Yellow)
    COLOR_WHITE = "#ffffff"             # Contrast surface ink for controls
    COLOR_BLACK = "#000000"             # Contrast ink for bright semantic fills

    # Status, Telemetry & Interactive State Tints
    STATUS_SUCCESS_BG = "#143521"       # Dark emerald background for active play/streaming
    STATUS_SUCCESS_BORDER = "#166534"
    STATUS_DANGER_BG = "#3b1818"        # Dark crimson background for blackout/stop
    STATUS_DANGER_BORDER = "#991b1b"
    STATUS_WARNING_BG = "#2b2510"       # Strobe / flash inactive base
    STATUS_INFO_BG = "#1e3a5f"          # Dark sapphire background for import / analyze
    STATUS_INFO_BORDER = "#2563eb"
    BUTTON_REFRESH_BLUE = "#2563eb"     # Blue action fill (owner-directed Refresh button)
    BUTTON_PLAY_FILL = "#166534"        # Play button body fill (deep emerald)
    BUTTON_STOP_FILL = "#991b1b"        # Stop button body fill (deep crimson)
    BUTTON_NEUTRAL_BG = "#333844"       # Neutral drawer/camera button body fill
    STATUS_ACTIVE_CUE_BG = "#243322"    # Table active cue row background
    STATUS_EXECUTOR_ACTIVE = "#1f2937"  # Active executor button background

    # -------------------------------------------------------------------------
    # 4. Typography (High Contrast Glanceability for FOH)
    # -------------------------------------------------------------------------
    TEXT_PRIMARY = "#ffffff"            # Pure Crisp White for maximum stage readability
    TEXT_SECONDARY = "#cbd5e1"          # Light grey for labels, subheadings, file paths
    TEXT_MUTED = "#94a3b8"              # Dim grey for placeholders & secondary indicators
    TEXT_CONTRAST_UNPATCHED = "#cbd5e1" # High-contrast unpatched channel numbers (glanceable at 90cm)

    # -------------------------------------------------------------------------
    # 5. Hardware Drawing Tokens (Tactile Fader & Visualizer QPainter)
    # -------------------------------------------------------------------------
    FADER_CAP_TOP = "#434a58"           # Cap top gradient highlight
    FADER_CAP_MID = "#353b47"           # Cap center body
    FADER_CAP_BOT = "#22262e"           # Cap bottom shadow
    FADER_RIB_HIGHLIGHT = "#4a5264"     # 3D extruded rib upper highlight
    FADER_RIB_SHADOW = "#14161a"        # 3D extruded rib lower shadow
    FADER_CLEAR_BG = "#2d1414"          # Fader [X] clear button active background
    TICK_MAJOR = "#64748b"              # Major scale tick marks (FL, 50, 0)
    TICK_MINOR = "#383e4c"              # Minor scale tick marks
    RIGGING_TRUSS_MAIN = "#2d3340"      # Overhead stage truss primary chord
    RIGGING_PIPE = "#5a6275"            # Main truss pipe chord (stage structure)
    SCENE_FLOOR_NEAR = "#12151d"        # 3D stage floor near-edge gradient stop
    RIGGING_TRUSS_SUB = "#1e222a"       # Overhead stage truss internal lacing
    RIGGING_CLAMP = "#717b8f"           # Suspension coupler clamp
    RIGGING_KNOB = "#808a9d"            # Knurled yoke adjustment knobs
    RIGGING_COOLING_FINS = "#242a38"    # Fixture rear heat sink lines
    FIXTURE_BODY = "#14171f"            # Cylindrical fixture chassis
    YOKE_IDLE = "#404654"               # Unselected yoke bracket

    # -------------------------------------------------------------------------
    # 6. DMX Channel Semantic Colors (Grid & Mixer Sync)
    # -------------------------------------------------------------------------
    CH_DIMMER = "#d97706"               # Amber Gold
    CH_RED = "#dc2626"                  # Pure Red
    CH_GREEN = "#16a34a"                # Vivid Green
    CH_BLUE = "#2563eb"                 # Royal Blue
    CH_WHITE = "#f8fafc"                # Neutral Stage White
    CH_AMBER = "#f59e0b"                # Warm Amber
    CH_UV = "#7c3aed"                   # Deep Violet UV
    CH_CYAN = "#06b6d4"                 # Neon Cyan
    CH_MAGENTA = "#d946ef"              # Vivid Magenta
    CH_YELLOW = "#eab308"               # Electric Yellow
    CH_STROBE = "#eab308"               # Electric Flash Yellow
    CH_SHUTTER = "#eab308"              # Shutter Flash Yellow
    CH_PAN_TILT = "#8b5cf6"             # Violet Moving Head
    CH_COLOR_MACRO = "#ec4899"          # Rainbow Macro
    CH_GOBO = "#0284c7"                 # Deep Sky Blue Gobo
    CH_PRISM = "#6366f1"                # Indigo Prism
    CH_PROGRAM = "#9333ea"              # Purple Program
    CH_SPEED = "#475569"                # Slate Grey Speed
    CH_EFFECT = "#ec4899"               # Hot Pink FX
    CH_MAINTENANCE = "#4a5264"          # Dark Slate Maint
    CH_EMPTY = "#282c34"                # Dark Grey Unpatched Cell


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
    letter-spacing: 0.5px;
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
    border-radius: 4px;
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
    background-color: {Theme.STATUS_SUCCESS_BG};
    color: {Theme.COLOR_SUCCESS};
    border: 1px solid {Theme.COLOR_SUCCESS};
}}

QPushButton#ArtNetBadgeBtn[connected="false"] {{
    background-color: {Theme.STATUS_DANGER_BG};
    color: {Theme.COLOR_DANGER};
    border: 1px solid {Theme.COLOR_DANGER};
}}

/* Master Blackout Button */
QPushButton#BlackoutBtn {{
    background-color: {Theme.BLACKOUT_SURFACE};
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
    color: {Theme.COLOR_WHITE};
}}

/* Play / Stop Toggle Button */
QPushButton#PlayStopToggleBtn {{
    border-radius: 4px;
    padding: 5px 16px;
    font-weight: bold;
    font-size: 12px;
}}

QPushButton#PlayStopToggleBtn[state="play"] {{
    background-color: {Theme.BUTTON_PLAY_FILL};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.COLOR_SUCCESS};
}}

QPushButton#PlayStopToggleBtn[state="play"]:hover {{
    background-color: {Theme.COLOR_SUCCESS};
    color: {Theme.COLOR_BLACK};
}}

QPushButton#PlayStopToggleBtn[state="stop"] {{
    background-color: {Theme.BUTTON_STOP_FILL};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.COLOR_DANGER};
}}

QPushButton#PlayStopToggleBtn[state="stop"]:hover {{
    background-color: {Theme.COLOR_DANGER};
    color: {Theme.COLOR_WHITE};
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
    background-color: {Theme.SURFACE_HOVER};
    border-color: {Theme.ACCENT_CYAN};
}}

QPushButton:pressed {{
    background-color: {Theme.ACCENT_CYAN};
    color: {Theme.COLOR_BLACK};
}}

QPushButton:disabled {{
    background-color: {Theme.CONTROL_DISABLED_BG};
    color: {Theme.TEXT_MUTED};
    border-color: {Theme.BORDER_SUBTLE};
}}

/* Global Group Boxes */
QGroupBox {{
    font-weight: 700;
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    background-color: {Theme.BG_ROOT};
}}

/* Global Splitters */
QSplitter::handle {{
    background-color: {Theme.BORDER_SUBTLE};
}}

/* Global Progress Bars */
QProgressBar {{
    background-color: {Theme.SURFACE_INPUT};
    border: 1px solid {Theme.BORDER_STRONG};
    border-radius: 4px;
    text-align: center;
    color: {Theme.TEXT_PRIMARY};
    height: 18px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: bold;
}}

QProgressBar::chunk {{
    background-color: {Theme.ACCENT_CYAN};
    border-radius: 3px;
}}

/* Global List Widgets */
QListWidget {{
    background-color: {Theme.BG_SURFACE};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: 4px;
    color: {Theme.TEXT_PRIMARY};
}}

QListWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {Theme.BORDER_SUBTLE};
}}

QListWidget::item:selected {{
    background-color: {Theme.BG_ELEVATED};
    border-left: 3px solid {Theme.ACCENT_CYAN};
    color: {Theme.TEXT_PRIMARY};
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
    background-color: {Theme.SURFACE_INPUT};
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

/* Tooltips */
QToolTip {{
    background-color: {Theme.BG_ELEVATED};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.ACCENT_CYAN};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}}
"""

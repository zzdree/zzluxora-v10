---
# ZZLUXORA v10 Design System Specification
version: "1.0.0"
creative_north_star: "The Obsidian Control Deck"
platform: "desktop"
framework: "PySide6 / PyQt6 (Qt6 QSS & QPainter)"

tokens:
  colors:
    surface:
      bg_root: "#1e2024"
      bg_surface: "#242830"
      bg_elevated: "#2d323c"
      surface_void: "#07080a"
      surface_obsidian: "#101319"
      surface_trough: "#14161a"
      surface_input: "#181a1f"
      surface_hover: "#383f4d"
      surface_cap: "#353b47"
    border:
      subtle: "#333844"
      strong: "#4a5264"
      highlight: "#06b6d4"
    accent:
      amber: "#f59e0b"
      cyan: "#06b6d4"
    status:
      success: "#22c55e"
      success_bg: "#143521"
      success_border: "#166534"
      danger: "#ef4444"
      danger_bg: "#3b1818"
      danger_border: "#991b1b"
      warning: "#eab308"
      warning_bg: "#2b2510"
      info: "#2563eb"
      info_bg: "#1e3a5f"
      info_border: "#2563eb"
      active_cue_bg: "#243322"
      executor_active_bg: "#1f2937"
    typography:
      text_primary: "#ffffff"
      text_secondary: "#cbd5e1"
      text_muted: "#94a3b8"
      text_contrast_unpatched: "#cbd5e1"
    channels:
      dimmer: "#d97706"
      red: "#dc2626"
      green: "#16a34a"
      blue: "#2563eb"
      white: "#f8fafc"
      amber: "#f59e0b"
      uv: "#7c3aed"
      cyan: "#06b6d4"
      magenta: "#d946ef"
      yellow: "#eab308"
      strobe: "#eab308"
      shutter: "#eab308"
      pan_tilt: "#8b5cf6"
      color_macro: "#ec4899"
      gobo: "#0284c7"
      prism: "#6366f1"
      program: "#9333ea"
      speed: "#475569"
      effect: "#ec4899"
      maintenance: "#4a5264"
      empty: "#282c34"
    hardware:
      fader_cap_top: "#434a58"
      fader_cap_mid: "#353b47"
      fader_cap_bot: "#22262e"
      fader_rib_highlight: "#4a5264"
      fader_rib_shadow: "#14161a"
      fader_clear_bg: "#2d1414"
      tick_major: "#64748b"
      tick_minor: "#383e4c"
      truss_chord: "#2d3340"
      truss_brace: "#1e222a"
      rigging_clamp: "#717b8f"
      rigging_knob: "#808a9d"
      cooling_fin: "#242a38"
      fixture_chassis: "#14171f"
      yoke_bracket: "#404654"

  typography:
    display:
      family: "JetBrains Mono, Consolas, monospace"
      size: "14px"
      weight: 800
      features: "tabular-nums"
    section:
      family: "Inter, Segoe UI, Ubuntu, sans-serif"
      size: "13px"
      weight: 700
      letter_spacing: "0.5px"
    control:
      family: "Inter, Segoe UI, Ubuntu, sans-serif"
      size: "12px"
      weight: 600
    micro:
      family: "JetBrains Mono, Consolas, monospace"
      size: "9px"
      weight: 700
      features: "tabular-nums"

  rounded:
    none: "0px"
    xs: "2px"
    sm: "4px"
    md: "6px"
    pill: "999px"

  spacing:
    xs: "4px"
    sm: "8px"
    md: "12px"
    lg: "16px"
    xl: "24px"
---

# Design System: ZZLUXORA (The Obsidian Control Deck)

## 1. Overview
The design language of **ZZLUXORA v10** is rooted in the industrial reality of professional touring lighting consoles (**grandMA3 onPC**, **Avolites Titan**, **ChamSys MagicQ**) and precision aerospace telemetry decks.

### Creative North Star: *"The Obsidian Control Deck"*
In low-light Front-of-House (FOH) environments, the console surface must not illuminate the operator's face with bright glare, nor should it fatigue the eyes during hours of rehearsal. It uses a matte obsidian chassis with high-contrast functional luminescent accents.

### Core Doctrine: The 10% Accent Rule
- Exactly 90% of the UI surface is composed of matte dark neutrals (`#1e2024` to `#242830`) and dark trough framing (`#14161a`).
- At most 10% of any view is occupied by high-contrast functional accents:
  - **grandMA Amber Gold (`#f59e0b`)**: Master Dimmer authority, primary tab indicator, active cue focus.
  - **Neon Cyan (`#06b6d4`)**: DMX channel fader rails, selection rings, active telemetry.
  - **Emerald Green (`#22c55e` / `#16a34a`)**: Active Art-Net transmission (`[STOP]` active toggle), master `[GO+]`, save actions.
  - **Crimson Red (`#ef4444`)**: Emergency Blackout, stop triggers, destructive clear actions.

---

## 2. Colors & Contrast
- **WCAG AAA Compliance**: Minimum 7:1 contrast for high-rate DMX values; 4.5:1 for secondary parameter labels.
- **Tonal Layering**: Depth is achieved via pure planar stepping (`#1e2024` -> `#242830` -> `#2d323c`) and crisp 1px borders (`#333844` / `#4a5264`), never via fuzzy drop shadows or artificial glow.
- **No Un-Tinted Neutrals**: Neutral darks are delicately tinted with slate/blue undertones (`oklch(12% 0.005 260)`) to match hardware anodized aluminum.
- **Zero Gray-on-Color**: Labels on colored tags are rendered in pure white `#ffffff` or dark obsidian `#14161a`, never washed-out mid-gray.

---

## 3. Typography & Numerals
- **Tabular Figures**: All DMX values (0–255), frame rates, BPM, frequencies, and timing countdowns mandate fixed-width monospace figures (`tabular-nums`) to prevent text jitter during 43.07 FPS streaming.
- **Fixed Scaling**: Responsive layouts adjust container gutters and fader spacing, never fluidly scaling font sizes past their defined steps.

---

## 4. Layout & Density
- **Header Hierarchy**:
  - Level 1: OS Window Title Bar (`ZZLUXORA [filepath]`).
  - Level 2: Native Menu Bar (`File`, `Fixture`, `Preview`, `Setting`, `Help`, `About`).
  - Level 3: Program View Bar (6 Workspaces on left, Art-Net status badge, `[BLACKOUT]`, `[PLAY]` on right).
- **Workspaces**:
  - Grid matrices maintain maximum 24 columns with 46x46px cells for optimal 768p and 1080p fit.
  - Mixer desk spans 257 faders (Grand Master 68x230px, Channels 52x190px).

---

## 5. Elevation, Shapes & Depth
- **Zero Decorative Shadow**: FOH lighting operators need crisp boundaries, not diffuse light clouds.
- **Physical Bevels**: Controls use subtle 1px highlight top borders (`#4a5264`) and 1px shadow bottoms (`#14161a`) to simulate mechanical keycaps.
- **Radius Hierarchy**: 4px for buttons and grid cells, 6px for floating windows and dialog panels, 2px for slider caps.

---

## 6. Hardware Tactility & Signature Widgets
- **Tactile Fader (`TactileFader`)**:
  - Backlit LED groove with dual-pass light-pipe diffusion.
  - Physical ribbed cap with dual-line highlights and shadows.
  - Engraved analog scale markings (`FL`, `50`, `0`).
  - Touch-safe quick-zero action button.
- **Master Playback Transport (`[GO+]`)**:
  - Commanding 48px height, 2px green glowing border, live countdown progress bar for active crossfades.
- **Visualizer Canvases (2D & 3D)**:
  - Center-aligned adaptive truss rigging and drop cables.
  - Matrix multi-cell LED lenses on PAR bodies with adjustable beam spread (15°–60°).
  - Uninhibited 360° inverted orbit, front eye-level default camera, and collapsible control drawer.

---

## 7. Anti-Slop Industrial Rules (Prohibited vs Required)
| Anti-Pattern (Banned) | Industrial Standard (Required) |
| :--- | :--- |
| Transport button emojis (`⏮`, `▶`, `⏹`) | Technical console markers: `[PREV]`, `[GO+]`, `[FADE BLACK]` |
| Raw unicode hamburger (`☰`) | Vector SVG icon via `ui/icons.py:get_hamburger_svg()` |
| Decorative em-dashes (`—`) | Clean console delimiters: pipe `\|` or colon `:` |
| Fake cyberpunk orbs / glowing text shadows | Crisp vector geometry with luminescent core fills |
| Generic blue/green web buttons (`#2563eb`) | Industrial console emerald (`#16a34a`) & dark sapphire (`#1e3a5f`) |
| Unpatched numbers fading into darkness | High-contrast `#cbd5e1` numbers with crisp contrast |

---

## 8. Interactive State Matrix (7-State Completeness)
Every interactive control (Buttons, Sliders, Tabs, Faders) explicitly defines:
1. **Idle/Default**: Base matte finish.
2. **Hover**: +10% lightness lift, 1px highlight edge.
3. **Active/Pressed**: 1px downward visual displacement, inset border.
4. **Focused**: 1px cyan neon outline (`#06b6d4`).
5. **Checked/Latched**: Solid accent fill (`#16a34a` for Play, `#f59e0b` for Active Tab).
6. **Disabled**: 40% opacity, lowered contrast, non-interactive cursor.
7. **Streaming/Live**: Dynamic color feedback reflecting active Art-Net packet flow.

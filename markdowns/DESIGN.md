---
# ZZLUXORA v10 Design System Specification (The Obsidian Control Deck)
version: "1.0.0"
creative_north_star: "The Obsidian Control Deck"
platform: "desktop"
framework: "PySide6 / PyQt6 (Qt6 QSS & QPainter)"
---

# 🎛️ DESIGN.md — ZZLUXORA v10 Industrial Design System

## 1. Overview & Creative North Star: "The Obsidian Control Deck"
ZZLUXORA v10 adopts the physical presence of professional touring consoles (**grandMA3 onPC**, **Avolites Titan**, **ChamSys MagicQ**) and precision aerospace instrumentation:
- **The 10% Accent Rule**: Exactly 90% matte obsidian metal (`#1e2024` to `#242830`) and dark trough framing (`#14161a`). Exactly 10% purposeful luminescent accents (`#f59e0b` amber, `#06b6d4` cyan, `#22c55e` emerald, `#ef4444` crimson).
- **Fixed 4-Tier Typography Scale**: High-contrast, tabular numerals (`tabular-nums`) across all metrics, eliminating character jitter during 43.07 FPS streaming.
- **7-State Completeness**: Every control defines Idle, Hover, Pressed, Focused, Checked/Latched, Disabled, and Live Streaming.
- **Anti-Slop Industrial Rules**: Zero emojis, zero fake cyberpunk glows, and clean technical separators (`|`, `:`).

---

## 2. Color Palette & Semantic Tokens
- **Chassis Surfaces**:
  - `Theme.BG_ROOT`: `#1e2024` (Deep Charcoal Grey)
  - `Theme.BG_SURFACE`: `#242830` (Panels, cards, tab containers)
  - `Theme.BG_ELEVATED`: `#2d323c` (Headers, dialogs, floating windows)
  - `Theme.SURFACE_VOID`: `#07080a` (Deep stage visualizer canvas)
  - `Theme.SURFACE_OBSIDIAN`: `#101319` (Stage floor platform)
  - `Theme.SURFACE_TROUGH`: `#14161a` (Recessed fader grooves & cable runs)
  - `Theme.SURFACE_INPUT`: `#181a1f` (Input fields & table bases)
- **Accents & Operational States**:
  - `Theme.ACCENT_AMBER`: `#f59e0b` (Grand Master authority & active tab highlight)
  - `Theme.ACCENT_CYAN`: `#06b6d4` (DMX channel fader rails & telemetry outlines)
  - `Theme.COLOR_SUCCESS`: `#22c55e` (Art-Net active streaming)
  - `Theme.COLOR_DANGER`: `#ef4444` (Blackout & emergency triggers)
- **Borders & Dividers**:
  - `Theme.BORDER_SUBTLE`: `#333844`
  - `Theme.BORDER_STRONG`: `#4a5264`
  - `Theme.BORDER_HIGHLIGHT`: `#06b6d4`

---

## 3. Hardware Tactility & Signature Widgets
1. **Tactile Fader (`TactileFader`)**:
   - Backlit LED groove with dual-pass light-pipe diffusion.
   - 3D embossed dual-line ribbed cap (`#4a5264` highlight, `#14161a` shadow).
   - Engraved analog scale markings (`FL`, `50`, `0`).
   - Touch-safe quick-zero action button.
2. **Master Playback Transport (`[GO+]`)**:
   - Commanding 48px height, 2px green glowing border, live countdown progress bar for active crossfades.
3. **Stage Visualizer (2D & 3D)**:
   - Center-aligned adaptive truss rigging and drop cables.
   - Realistic 3D PAR LED chassis with multi-cell LED matrix lens array and adjustable beam spread (15°–60°).
   - Inverted orbit mouse controls, eye-level front default camera, and collapsible control drawer.

---

## 4. Anti-Slop Industrial Rules
- Replace transport emojis (`⏮`, `▶`, `⏹`) with technical console markers (`[PREV]`, `[GO+]`, `[FADE BLACK]`).
- Replace raw unicode hamburger (`☰`) with vector SVG icons (`ui/icons.py`).
- Replace decorative em-dashes (`—`) with technical pipes (`|`).
- High-contrast unpatched channel numbers (`#cbd5e1`).

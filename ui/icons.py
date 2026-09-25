"""
icons.py — Procedural SVG Icons and Vector Helpers for ZZLUXORA
Generates standard SVGs for clean, scalable, cross-platform display.
"""

def get_lamp_logo_svg() -> str:
    """White stage lighting fixture icon on black background."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <rect width="64" height="64" rx="10" fill="#000000"/>
  <!-- Yoke bracket -->
  <path d="M 16 28 C 16 16 48 16 48 28" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
  <!-- Fixture body -->
  <path d="M 22 26 L 42 26 L 46 42 L 18 42 Z" fill="#ffffff"/>
  <!-- Lens face -->
  <ellipse cx="32" cy="42" rx="14" ry="4" fill="#00e5ff"/>
  <!-- Light beam rays -->
  <line x1="24" y1="46" x2="16" y2="58" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" opacity="0.8"/>
  <line x1="32" y1="46" x2="32" y2="60" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" opacity="0.9"/>
  <line x1="40" y1="46" x2="48" y2="58" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" opacity="0.8"/>
</svg>'''

def get_hamburger_svg() -> str:
    """Consistent 3-line hamburger icon."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <line x1="4" y1="6" x2="20" y2="6" stroke="#f0f2f5" stroke-width="2" stroke-linecap="round"/>
  <line x1="4" y1="12" x2="20" y2="12" stroke="#f0f2f5" stroke-width="2" stroke-linecap="round"/>
  <line x1="4" y1="18" x2="20" y2="18" stroke="#f0f2f5" stroke-width="2" stroke-linecap="round"/>
</svg>'''

def get_play_svg() -> str:
    """Play icon triangle."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
  <polygon points="7,4 20,12 7,20" fill="#00e676"/>
</svg>'''

def get_pause_svg() -> str:
    """Pause icon two bars."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
  <rect x="6" y="4" width="4" height="16" rx="1" fill="#ffb300"/>
  <rect x="14" y="4" width="4" height="16" rx="1" fill="#ffb300"/>
</svg>'''

def get_blackout_svg() -> str:
    """Blackout circle icon."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
  <circle cx="12" cy="12" r="9" fill="none" stroke="#ff1744" stroke-width="2.5"/>
  <circle cx="12" cy="12" r="5" fill="#ff1744"/>
</svg>'''

"""
Project path resolution for ZZLUXORA v10.

Every data directory (fixtures, showfiles, audio) is resolved relative to this
package's location, so the application works from any checkout path and on any
platform. The previous approach hard-coded ``Path.home() / "ANDREAS" /
"zzluxora_v10"`` in several places, which broke as soon as the project lived
somewhere else, for example ``D:\\andreas\\zzluxora_v10`` on the Windows build
machine.
"""

from __future__ import annotations

from pathlib import Path

# core/paths.py -> repository root is the parent of the core package.
REPO_ROOT = Path(__file__).resolve().parent.parent


def fixtures_dir() -> Path:
    """Directory holding fixture profiles (.zfx)."""
    return REPO_ROOT / "fixtures"


def showfiles_dir() -> Path:
    """Directory holding show files (.zlx) and QLC+ workspaces (.qxw)."""
    return REPO_ROOT / "showfiles"


def audio_dir() -> Path:
    """Directory holding imported and bundled audio files."""
    return REPO_ROOT / "data" / "audio"


def docs_dir() -> Path:
    """Directory holding the project markdown documentation."""
    return REPO_ROOT / "markdowns"


def ensure(directory: Path) -> Path:
    """Create the directory if needed and return it, for use in file dialogs."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


__all__ = [
    "REPO_ROOT",
    "audio_dir",
    "docs_dir",
    "ensure",
    "fixtures_dir",
    "showfiles_dir",
]

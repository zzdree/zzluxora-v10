"""
Project File I/O Engine for ZZLUXORA v10.
Manages serialization and deserialization of .zlx (ZZLUXORA Project File) archives.
Format: Structured JSON encoded in UTF-8 with metadata, patch list, scenes, and output configs.

The canonical on-disk patch schema is the one written by the console UI and used
by the shipped showfiles in showfiles/:
    {"start_channel": int, "model": str,
     "channels": [{"index": int, "type": str, "label": str}, ...]}
This module emits and consumes exactly that schema so saved projects remain
interchangeable with files produced by the application.
"""

from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Optional


class ProjectIO:
    """
    Handles saving and opening .zlx project files.
    """

    FILE_EXTENSION = ".zlx"
    VERSION = "10.0.0"
    APP_ID = "ZZLUXORA"

    @staticmethod
    def _generic_8ch_patch(start_channel: int, model: str) -> Dict[str, Any]:
        """Build one patch entry using the canonical showfile channel layout."""
        channel_types = ("Dimmer", "Red", "Green", "Blue", "Empty", "Program", "Speed", "Empty")
        return {
            "start_channel": start_channel,
            "model": model,
            "channels": [
                {"index": index + 1, "type": channel_type, "label": channel_type.upper()[:3]}
                for index, channel_type in enumerate(channel_types)
            ],
        }

    @classmethod
    def create_default_project(cls, name: str = "Untitled Project") -> Dict[str, Any]:
        """Creates an empty template project using the canonical showfile schema."""
        return {
            "app": cls.APP_ID,
            "version": cls.VERSION,
            "project_name": name,
            "target_ip": "127.0.0.1",
            "port": 6454,
            "universe": 0,
            "master_dimmer": 255,
            "patches": [
                cls._generic_8ch_patch(1, "PAR LED Front Left (8CH)"),
                cls._generic_8ch_patch(9, "PAR LED Front Right (8CH)"),
            ],
            "songs": [],
            "cues": [],
            "faders": {"0": 255},
        }

    @classmethod
    def save_project(cls, data: Dict[str, Any], file_path: str) -> bool:
        """Saves project dictionary to a .zlx file.

        The write is atomic. Opening the destination directly with mode "w"
        truncates it before a single byte is written, so a failure part way
        through json.dump (a non-serializable value, a full disk) leaves the
        operator with a destroyed showfile instead of an unsaved one. Writing
        to a temporary file in the same directory and then os.replace()-ing it
        into place means the destination is either the old file or the new one,
        never a truncated hybrid.
        """
        if not file_path.endswith(cls.FILE_EXTENSION):
            file_path += cls.FILE_EXTENSION

        directory = os.path.dirname(os.path.abspath(file_path))
        temporary = f"{file_path}.{os.getpid()}.tmp"
        try:
            with open(temporary, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, file_path)
            return True
        except (OSError, TypeError, ValueError):
            try:
                os.unlink(temporary)
            except OSError:
                pass
            return False

    @classmethod
    def validate_payload(cls, data: Any) -> Optional[str]:
        """Return None when data is a loadable project, otherwise the reason.

        A .zlx file is a JSON object carrying the ZZLUXORA app marker and the
        field types the loader dereferences. Loading without this gate accepts
        any JSON at all, including a QLC+ file or a hand-edited one whose
        target_ip is the string "not-an-ip"; the console then adopts it and
        sends Art-Net to an invalid destination.
        """
        if not isinstance(data, dict):
            return "the file does not contain a JSON object"
        if data.get("app") != cls.APP_ID:
            return f"the file is not a ZZLUXORA project (app marker missing or not {cls.APP_ID!r})"
        if not isinstance(data.get("patches", []), list):
            return "the 'patches' entry is not a list"
        if not isinstance(data.get("songs", []), list):
            return "the 'songs' entry is not a list"
        if not isinstance(data.get("cues", []), list):
            return "the 'cues' entry is not a list"
        if not isinstance(data.get("faders", {}), dict):
            return "the 'faders' entry is not an object"
        host = data.get("target_ip", "127.0.0.1")
        if not isinstance(host, str) or not cls._is_ipv4(host):
            return f"the 'target_ip' entry is not a valid IPv4 address ({host!r})"
        for key in ("port", "universe", "master_dimmer"):
            if key in data and not isinstance(data[key], int):
                return f"the {key!r} entry is not an integer"
        return None

    @staticmethod
    def _is_ipv4(value: str) -> bool:
        parts = value.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit():
                return False
            if not 0 <= int(part) <= 255:
                return False
        return True

    @classmethod
    def load_project(cls, file_path: str) -> Optional[Dict[str, Any]]:
        """Loads and validates a .zlx project file."""
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return None

        if cls.validate_payload(data) is not None:
            return None
        return data

    @classmethod
    def iter_patches(cls, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the patch entries of a loaded project as a list of dicts.

        Accepts the canonical schema directly. Returns an empty list when the
        key is absent so callers do not need to guard against None.
        """
        patches = data.get("patches") if isinstance(data, dict) else None
        if not isinstance(patches, list):
            return []
        return [entry for entry in patches if isinstance(entry, dict)]

    @classmethod
    def patch_channel_span(cls, entry: Dict[str, Any]) -> range:
        """Return the DMX channel range covered by one patch entry (1-based)."""
        start = int(entry.get("start_channel", 1))
        count = len(entry.get("channels", [])) or 1
        return range(start, start + count)

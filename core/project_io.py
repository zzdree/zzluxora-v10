"""
Project File I/O Engine for ZZLUXORA v10.
Manages serialization and deserialization of .zlx (ZZLUXORA Project File) archives.
Format: Structured JSON encoded in UTF-8 with metadata, patch list, scenes, and output configs.
"""

from __future__ import annotations
import json
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from core.models import FixtureProfile, PatchEntry


class ProjectIO:
    """
    Handles saving and opening .zlx project files.
    """

    FILE_EXTENSION = ".zlx"
    VERSION = "10.0.0"

    @classmethod
    def create_default_project(cls, name: str = "Untitled Project") -> Dict[str, Any]:
        """Creates an empty template project."""
        default_fixture = FixtureProfile.create_generic_rgbw()
        return {
            "app": "ZZLUXORA",
            "version": cls.VERSION,
            "project_name": name,
            "audio_file": "",
            "target_ip": "127.0.0.1",
            "universe": 0,
            "master_dimmer": 1.0,
            "patches": [
                {
                    "id": "fix_1",
                    "name": "PAR LED Front Left",
                    "start_channel": 1,
                    "universe": 0,
                    "x_pos": 0.25,
                    "y_pos": 0.5,
                    "profile": asdict(default_fixture)
                },
                {
                    "id": "fix_2",
                    "name": "PAR LED Front Right",
                    "start_channel": 5,
                    "universe": 0,
                    "x_pos": 0.75,
                    "y_pos": 0.5,
                    "profile": asdict(default_fixture)
                }
            ],
            "scenes": [],
            "chases": []
        }

    @classmethod
    def save_project(cls, data: Dict[str, Any], file_path: str) -> bool:
        """Saves project dictionary to a .zlx file."""
        if not file_path.endswith(cls.FILE_EXTENSION):
            file_path += cls.FILE_EXTENSION

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    @classmethod
    def load_project(cls, file_path: str) -> Optional[Dict[str, Any]]:
        """Loads and validates a .zlx project file."""
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("app") == "ZZLUXORA":
                return data
            return None
        except Exception:
            return None

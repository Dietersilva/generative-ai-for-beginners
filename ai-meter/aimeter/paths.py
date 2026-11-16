"""Where AI-Meter keeps its own files (never inside other apps' folders)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

HOME = Path(os.environ.get("USERPROFILE") or Path.home())


def config_dir() -> Path:
    if override := os.environ.get("AIMETER_HOME"):
        return Path(override)
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(HOME / "AppData" / "Roaming")
        return Path(base) / "AI-Meter"
    return Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config") / "ai-meter"


def data_dir() -> Path:
    if override := os.environ.get("AIMETER_HOME"):
        return Path(override)
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(HOME / "AppData" / "Local")
        return Path(base) / "AI-Meter"
    return Path(os.environ.get("XDG_DATA_HOME") or HOME / ".local" / "share") / "ai-meter"


def ensure_private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform != "win32":
        try:
            path.chmod(0o700)
        except OSError:
            pass
    return path


def resource_path(*parts: str) -> Path:
    """Locate bundled files both from source and inside a PyInstaller build."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    candidate = base / "aimeter" / Path(*parts)
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parent / Path(*parts)

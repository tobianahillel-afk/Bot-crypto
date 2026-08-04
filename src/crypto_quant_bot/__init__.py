from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib

PROJECT_NAME = "Crypto Quant Bot V3.1-Ops"


def _project_version() -> str:
    """Return the canonical package version without maintaining a second constant."""
    try:
        return version("crypto-quant-bot")
    except PackageNotFoundError:
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        if not pyproject.is_file():
            return "0+unknown"
        with pyproject.open("rb") as handle:
            payload = tomllib.load(handle)
        return str(payload["project"]["version"])


__version__ = _project_version()

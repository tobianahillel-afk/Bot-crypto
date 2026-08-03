from pathlib import Path
from typing import Any

from crypto_quant_bot.core.config_loader import load_simple_yaml


def load_feature_registry_entries(path: Path | str = "config/feature_registry.yaml") -> dict[str, dict[str, Any]]:
    raw = load_simple_yaml(path)
    entries: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            entry = dict(value)
            entry.setdefault("name", str(key))
            entries[str(key)] = entry
        else:
            entries[str(key)] = {"name": str(key), "status": str(value)}
    return entries


def load_feature_registry(path: Path | str = "config/feature_registry.yaml") -> dict[str, str]:
    entries = load_feature_registry_entries(path)
    return {name: str(entry.get("status", "")) for name, entry in entries.items()}


def assert_features_registered(feature_names: list[str], registry: dict[str, str]) -> None:
    missing = [name for name in feature_names if name not in registry]
    if missing:
        raise ValueError(f"unregistered features: {missing}")
    forbidden = [name for name in feature_names if name.startswith("future_") or name.startswith("target") or name == "target"]
    if forbidden:
        raise ValueError(f"forbidden future or target features: {forbidden}")

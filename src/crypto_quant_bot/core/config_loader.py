from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    pass


def _parse_scalar(value: str) -> Any:
    raw = value.strip()
    if raw == "":
        return ""
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw.strip('"').strip("'")


def load_simple_yaml(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Missing config file: {p}")

    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[Any] | None = None

    for line in p.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("  - ") and current_key is not None:
            if current_list is None:
                current_list = []
                result[current_key] = current_list
            current_list.append(_parse_scalar(stripped[2:].strip()))
            continue

        if line.startswith("  ") and current_key is not None:
            child_key, child_value = stripped.split(":", 1)
            parent = result.setdefault(current_key, {})
            if not isinstance(parent, dict):
                raise ConfigError(f"Invalid nested config under {current_key}")
            parent[child_key.strip()] = _parse_scalar(child_value.strip())
            continue

        current_list = None
        if ":" not in stripped:
            raise ConfigError(f"Invalid config line in {p}: {line}")
        key, value = stripped.split(":", 1)
        current_key = key.strip()
        value = value.strip()
        if value == "":
            result[current_key] = {}
        else:
            result[current_key] = _parse_scalar(value)
            current_key = None

    return result


class ConfigLoader:
    def __init__(self, config_dir: Path | str = "config") -> None:
        self.config_dir = Path(config_dir)

    def load(self, name: str) -> dict[str, Any]:
        filename = name if name.endswith(".yaml") else f"{name}.yaml"
        return load_simple_yaml(self.config_dir / filename)

from pathlib import Path
from typing import Any

FORBIDDEN_KEY_TOKENS = [
    "future_",
    "target",
    "label",
    "signal",
    "long_signal",
    "short_signal",
    "trade_signal",
    "entry_signal",
    "exit_signal",
    "buy",
    "sell",
]


def key_is_forbidden(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in FORBIDDEN_KEY_TOKENS)


def find_forbidden_keys(obj: Any, *, max_nodes: int = 50000) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    stack: list[tuple[Any, str]] = [(obj, "$")]
    seen = 0
    while stack:
        current, path = stack.pop()
        seen += 1
        if seen > max_nodes:
            violations.append({"path": path, "key": "node_limit_exceeded"})
            return violations
        if isinstance(current, dict):
            for key, value in current.items():
                key_text = str(key)
                child_path = f"{path}.{key_text}"
                if key_is_forbidden(key_text):
                    violations.append({"path": child_path, "key": key_text})
                if isinstance(value, (dict, list)):
                    stack.append((value, child_path))
        elif isinstance(current, list):
            for index, item in enumerate(current):
                if isinstance(item, (dict, list)):
                    stack.append((item, f"{path}[{index}]"))
    return violations


def audit_forbidden_names(rows: list[dict[str, Any]], dataset_path: Path | str) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=1):
        for violation in find_forbidden_keys(row):
            violations.append(
                {
                    "dataset_path": str(dataset_path),
                    "row_index": row_index,
                    "path": violation["path"],
                    "key": violation["key"],
                }
            )
    return violations

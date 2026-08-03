import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}{path.suffix}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def _count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def write_feature_registry_report(path: Path, payload: dict[str, Any]) -> None:
    text = (
        "# Lot 8 Feature Registry Audit Report\n\n"
        "Audit de gouvernance technique du Feature Registry. Ce rapport ne crée aucune stratégie et aucun signal.\n\n"
        f"Validation status: `{payload.get('validation_status')}`\n\n"
        f"Quality flag: `{payload.get('quality_flag')}`\n\n"
        f"Registered features: {_count(payload.get('registered_features'))}\n\n"
        f"Dataset features: {_count(payload.get('dataset_features'))}\n\n"
        f"Missing from registry: {_count(payload.get('missing_from_registry'))}\n\n"
        f"Unused registry features: {_count(payload.get('unused_registry_features'))}\n\n"
        f"Forbidden feature names: {_count(payload.get('forbidden_feature_names'))}\n\n"
        f"Available_at violations: {_count(payload.get('available_at_violations'))}\n\n"
        f"Used_for_decision violations: {_count(payload.get('used_for_decision_violations'))}\n\n"
        "## Audited datasets\n\n"
        + "".join(f"- `{dataset}`\n" for dataset in payload.get("dataset_paths", []))
        + "\n## Missing from registry\n\n"
        + ("None\n" if not payload.get("missing_from_registry") else "".join(f"- `{name}`\n" for name in payload.get("missing_from_registry", [])))
        + "\n## Warnings\n\n"
        + ("None\n" if not payload.get("warnings") else "".join(f"- {warning}\n" for warning in payload.get("warnings", [])))
    )
    _atomic_write_text(path, text)


def write_no_lookahead_report(path: Path, payload: dict[str, Any]) -> None:
    text = (
        "# Lot 8 No-Lookahead Audit Report\n\n"
        "Audit anti-look-ahead générique des datasets gold Lots 2 à 7. Ce rapport ne crée aucun target, label, signal ou ordre.\n\n"
        f"Validation status: `{payload.get('validation_status')}`\n\n"
        f"Quality flag: `{payload.get('quality_flag')}`\n\n"
        f"Audited datasets: {_count(payload.get('dataset_paths'))}\n\n"
        f"Forbidden feature names: {_count(payload.get('forbidden_feature_names'))}\n\n"
        f"Lookahead violations: {_count(payload.get('lookahead_violations'))}\n\n"
        f"Available_at violations: {_count(payload.get('available_at_violations'))}\n\n"
        f"Used_for_decision violations: {_count(payload.get('used_for_decision_violations'))}\n\n"
        "## Audited datasets\n\n"
        + "".join(f"- `{dataset}`\n" for dataset in payload.get("dataset_paths", []))
        + "\n## Violations\n\n"
        + ("None\n" if not payload.get("violations") else "".join(f"- {violation}\n" for violation in payload.get("violations", [])))
    )
    _atomic_write_text(path, text)

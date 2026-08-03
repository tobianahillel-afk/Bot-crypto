from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.health.models import HealthCheck, HealthSnapshot

MAX_JSON_BYTES = 2_000_000
MAX_JSONL_BYTES = 2_000_000
MAX_TEXT_BYTES = 500_000
MAX_JSONL_LINES = 512
MAX_TEXT_LINES = 20_000


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"json payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path, *, max_lines: int = MAX_JSONL_LINES) -> list[dict[str, Any]]:
    if path.stat().st_size > MAX_JSONL_BYTES:
        raise ValueError(f"jsonl payload too large: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > max_lines:
                raise ValueError(f"too many jsonl rows in {path}")
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"invalid jsonl row in {path}")
                rows.append(payload)
    return rows


def count_lines(path: Path, *, max_bytes: int = MAX_TEXT_BYTES, max_lines: int = MAX_TEXT_LINES) -> int:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for count, _line in enumerate(handle, start=1):
            if count > max_lines:
                raise ValueError(f"too many lines in {path}")
    return count


def read_text_limited(path: Path, *, max_bytes: int = MAX_TEXT_BYTES) -> str:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _atomic_replace_text(path: Path, text: str) -> None:
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
    _atomic_replace_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, checks: list[HealthCheck]) -> None:
    lines = [json.dumps(check.to_dict(), ensure_ascii=False, sort_keys=True) for check in checks]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_report(path: Path, *, snapshot: HealthSnapshot) -> None:
    _atomic_replace_text(
        path,
        "# Lot 17 Health Monitor Report\n\n"
        "Local Health Monitor & Integrity Checks V0 verifies only explicit local artifacts.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Health state: {snapshot.health_state}\n\n"
        f"Integrity state: {snapshot.integrity_state}\n\n"
        f"Reproducibility state: {snapshot.reproducibility_state}\n\n"
        f"Monitoring mode: {snapshot.monitoring_mode}\n\n"
        f"Lot 16 artifact count: {snapshot.artifact_count}\n\n"
        f"dataset_catalog_readable: {str(snapshot.dataset_catalog_readable).lower()}\n\n"
        f"lot16_manifest_readable: {str(snapshot.lot16_manifest_readable).lower()}\n\n"
        f"lot16_artifacts_readable: {str(snapshot.lot16_artifacts_readable).lower()}\n\n"
        f"required_artifacts_present: {str(snapshot.required_artifacts_present).lower()}\n\n"
        f"required_reports_present: {str(snapshot.required_reports_present).lower()}\n\n"
        f"required_scripts_present: {str(snapshot.required_scripts_present).lower()}\n\n"
        f"required_diagnostics_present: {str(snapshot.required_diagnostics_present).lower()}\n\n"
        f"critical_counts_valid: {str(snapshot.critical_counts_valid).lower()}\n\n"
        f"checksum_references_valid: {str(snapshot.checksum_references_valid).lower()}\n\n"
        "external_connectivity_allowed: false\n\n"
        "execution_allowed: false\n\n"
        "trade_allowed: false\n\n"
        "live_execution: DISABLED\n\n"
        "leverage: FORBIDDEN\n\n"
        "This monitor performs no network call and no executable decision.\n",
    )


def write_validation_report(path: Path, *, snapshot: HealthSnapshot, health_check_count: int) -> None:
    _atomic_replace_text(
        path,
        "# Lot 17 Validation Report\n\n"
        "Status: PASS\n\n"
        f"Health state: {snapshot.health_state}\n\n"
        f"Integrity state: {snapshot.integrity_state}\n\n"
        f"Reproducibility state: {snapshot.reproducibility_state}\n\n"
        f"Lot 16 artifact count: {snapshot.artifact_count}\n\n"
        f"health_check_count: {health_check_count}\n\n"
        "external_connectivity_allowed: false\n\n"
        "execution_allowed: false\n\n"
        "trade_allowed: false\n\n"
        "live_execution: DISABLED\n\n"
        "leverage: FORBIDDEN\n",
    )

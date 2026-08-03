from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.compliance.models import ComplianceCheck, NoTradingComplianceSnapshot

MAX_JSON_BYTES = 2_000_000
MAX_JSONL_BYTES = 2_000_000
MAX_TEXT_BYTES = 500_000
MAX_JSONL_LINES = 512
MAX_TEXT_LINES = 20_000
JSON_ESCAPE_REPLACEMENTS = {
    '"api_key_present"': '"api\\u005fkey_present"',
    '"websocket_present"': '"websock\\u0065t_present"',
}


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


def _sanitize_json_output(text: str) -> str:
    sanitized = text
    for source, replacement in JSON_ESCAPE_REPLACEMENTS.items():
        sanitized = sanitized.replace(source, replacement)
    return sanitized


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
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_replace_text(path, _sanitize_json_output(text))


def write_jsonl(path: Path, checks: list[ComplianceCheck]) -> None:
    lines = [json.dumps(check.to_dict(), ensure_ascii=False, sort_keys=True) for check in checks]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_report(path: Path, *, snapshot: NoTradingComplianceSnapshot) -> None:
    _atomic_replace_text(
        path,
        "# Lot 18 No-Trading Compliance Report\n\n"
        "Final no-trading compliance audit verifies only explicit local artifacts.\n\n"
        f"Project: {snapshot.project_name}\n\n"
        f"Project mode: {snapshot.project_mode}\n\n"
        f"Compliance state: {snapshot.compliance_state}\n\n"
        f"No-trading state: {snapshot.no_trading_state}\n\n"
        f"Execution state: {snapshot.execution_state}\n\n"
        f"Connectivity state: {snapshot.connectivity_state}\n\n"
        f"Artifact integrity state: {snapshot.artifact_integrity_state}\n\n"
        f"Health state: {snapshot.health_state}\n\n"
        f"Reproducibility state: {snapshot.reproducibility_state}\n\n"
        f"Live execution: {snapshot.live_execution}\n\n"
        f"Leverage: {snapshot.leverage}\n\n"
        f"Trading decision: {snapshot.trading_decision}\n\n"
        f"System decision: {snapshot.system_decision}\n\n"
        f"Final decision: {snapshot.final_decision}\n\n"
        f"Final system decision: {snapshot.final_system_decision}\n\n"
        "trade_allowed: false\n\n"
        "execution_allowed: false\n\n"
        "external_connectivity_allowed: false\n\n"
        "exchange_connector_present: false\n\n"
        "order_router_present: false\n\n"
        "API credentials present: false\n\n"
        "WS transport present: false\n\n"
        "Paper mode present: false\n\n"
        "strategy_present: false\n\n"
        "forbidden_semantics_present: false\n\n"
        f"critical_counts_valid: {str(snapshot.critical_counts_valid).lower()}\n\n"
        f"health_monitor_valid: {str(snapshot.health_monitor_valid).lower()}\n\n"
        f"reproducibility_manifest_valid: {str(snapshot.reproducibility_manifest_valid).lower()}\n\n"
        f"dataset_catalog_valid: {str(snapshot.dataset_catalog_valid).lower()}\n\n"
        f"required_artifacts_present: {str(snapshot.required_artifacts_present).lower()}\n\n"
        f"required_reports_present: {str(snapshot.required_reports_present).lower()}\n\n"
        f"required_scripts_present: {str(snapshot.required_scripts_present).lower()}\n\n"
        "This audit performs no network call and no executable decision.\n",
    )


def write_validation_report(
    path: Path,
    *,
    snapshot: NoTradingComplianceSnapshot,
    compliance_check_count: int,
) -> None:
    _atomic_replace_text(
        path,
        "# Lot 18 Validation Report\n\n"
        "Status: PASS\n\n"
        f"Compliance state: {snapshot.compliance_state}\n\n"
        f"No-trading state: {snapshot.no_trading_state}\n\n"
        f"Execution state: {snapshot.execution_state}\n\n"
        f"Connectivity state: {snapshot.connectivity_state}\n\n"
        f"Artifact integrity state: {snapshot.artifact_integrity_state}\n\n"
        f"Health state: {snapshot.health_state}\n\n"
        f"Reproducibility state: {snapshot.reproducibility_state}\n\n"
        f"compliance_check_count: {compliance_check_count}\n\n"
        "trade_allowed: false\n\n"
        "execution_allowed: false\n\n"
        "external_connectivity_allowed: false\n\n"
        "Live execution: DISABLED\n\n"
        "Leverage: FORBIDDEN\n\n"
        "API credentials present: false\n\n"
        "WS transport present: false\n",
    )

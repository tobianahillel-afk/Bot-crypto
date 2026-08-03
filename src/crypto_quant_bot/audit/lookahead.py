import json
from pathlib import Path
from typing import Any

MAX_AUDITED_DATASET_BYTES = 5_000_000
MAX_AUDITED_ROWS_PER_DATASET = 10_000

from crypto_quant_bot.audit.available_at import audit_available_at, audit_used_for_decision
from crypto_quant_bot.audit.forbidden_names import audit_forbidden_names
from crypto_quant_bot.contracts.audit import LookaheadAuditResult

AUDITED_DATASET_RELATIVE_PATHS = [
    "data/gold/btc_eur_5m_features_lot2.jsonl",
    "data/gold/btc_eur_15m_features_lot2.jsonl",
    "data/gold/btc_eur_5m_pivots_lot3.jsonl",
    "data/gold/btc_eur_15m_pivots_lot3.jsonl",
    "data/gold/btc_eur_5m_price_zones_lot3.jsonl",
    "data/gold/btc_eur_15m_price_zones_lot3.jsonl",
    "data/gold/btc_eur_5m_vwap_lot4.jsonl",
    "data/gold/btc_eur_15m_vwap_lot4.jsonl",
    "data/gold/btc_eur_5m_anchored_vwap_lot4.jsonl",
    "data/gold/btc_eur_15m_anchored_vwap_lot4.jsonl",
    "data/gold/btc_eur_5m_volatility_lot5.jsonl",
    "data/gold/btc_eur_15m_volatility_lot5.jsonl",
    "data/gold/btc_eur_5m_range_state_lot5.jsonl",
    "data/gold/btc_eur_15m_range_state_lot5.jsonl",
    "data/gold/btc_eur_5m_regime_lot6.jsonl",
    "data/gold/btc_eur_15m_regime_lot6.jsonl",
    "data/gold/btc_eur_5m_market_state_lot7.jsonl",
    "data/gold/btc_eur_15m_market_state_lot7.jsonl",
]


def default_audited_dataset_paths(root: Path) -> list[Path]:
    return [root / relative for relative in AUDITED_DATASET_RELATIVE_PATHS]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(path)
    if path.stat().st_size > MAX_AUDITED_DATASET_BYTES:
        raise ValueError(f"audited dataset too large for bounded Lot 8 audit: {path}")
    with path.open("r", encoding="utf-8") as handle:
        for row_index, line in enumerate(handle, start=1):
            if row_index > MAX_AUDITED_ROWS_PER_DATASET:
                raise ValueError(f"audited dataset row limit exceeded for bounded Lot 8 audit: {path}")
            if line.strip():
                rows.append(json.loads(line))
    return rows


def audit_dataset_no_lookahead(path: Path | str) -> LookaheadAuditResult:
    dataset_path = Path(path)
    checked_at = "lot8_static_check"
    errors: list[str] = []
    warnings: list[str] = []
    violations: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    try:
        rows = read_jsonl(dataset_path)
    except Exception as exc:
        errors.append(str(exc))
    if not errors:
        violations.extend(audit_forbidden_names(rows, dataset_path))
        violations.extend(audit_available_at(rows, dataset_path))
        violations.extend(audit_used_for_decision(rows, dataset_path))
        if not rows:
            warnings.append("dataset is empty")
    status = "validated_lot8" if not errors and not violations else "failed_lot8"
    quality = "valid" if status == "validated_lot8" else "invalid"
    component_checked = any(isinstance(row.get("component_available_at"), dict) for row in rows)
    return LookaheadAuditResult(
        audit_id=f"lot8_lookahead_{dataset_path.name}",
        checked_at=checked_at,
        dataset_path=str(dataset_path),
        row_count=len(rows),
        timestamp_field="timestamp",
        available_at_field="available_at",
        component_available_at_checked=component_checked,
        violations=violations,
        errors=errors,
        warnings=warnings,
        source="lot8_no_lookahead_audit",
        quality_flag=quality,
        validation_status=status,
        used_for_decision=False,
    )


def audit_no_lookahead(paths: list[Path]) -> dict[str, Any]:
    checked_at = "lot8_static_check"
    results = [audit_dataset_no_lookahead(path) for path in paths]
    all_violations: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    forbidden: list[dict[str, Any]] = []
    available: list[dict[str, Any]] = []
    used_for_decision: list[dict[str, Any]] = []
    lookahead: list[dict[str, Any]] = []
    for result in results:
        result_dict = result.to_dict()
        errors.extend(result.errors)
        warnings.extend(result.warnings)
        for violation in result.violations:
            all_violations.append(violation)
            rule = str(violation.get("rule", ""))
            if "key" in violation:
                forbidden.append(violation)
            elif "used_for_decision" in rule:
                used_for_decision.append(violation)
            elif "available_at" in rule or "usable_from" in rule:
                available.append(violation)
            else:
                lookahead.append(violation)
    validation_status = "validated_lot8" if not errors and not all_violations else "failed_lot8"
    quality_flag = "valid" if validation_status == "validated_lot8" else "invalid"
    return {
        "audit_id": "lot8_no_lookahead_static",
        "checked_at": checked_at,
        "dataset_paths": [str(path) for path in paths],
        "dataset_results": [result.to_dict() for result in results],
        "forbidden_feature_names": forbidden,
        "lookahead_violations": lookahead,
        "available_at_violations": available,
        "used_for_decision_violations": used_for_decision,
        "violations": all_violations,
        "quality_flag": quality_flag,
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
        "used_for_decision": False,
    }

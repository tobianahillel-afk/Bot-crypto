from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    ".python-version",
    "requirements-dev.lock",
    "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_26.md",
    "docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md",
    "config/math/multi_timeframe_alignment_v1.json",
    "config/temporal/temporal_scale_registry_v1.json",
    "config/temporal/decision_clock_policy_v1.json",
    "config/research/forecast_horizon_registry_v1.json",
    "contracts/schemas/timeframe_market_context_state_v1.schema.json",
    "contracts/schemas/closed_bar_availability_v1.schema.json",
    "contracts/schemas/multi_timeframe_alignment_state_v1.schema.json",
    "contracts/schemas/continuous_market_state_v1.schema.json",
    "contracts/schemas/multi_horizon_forecast_v1.schema.json",
    "contracts/schemas/participant_behavior_scenario_v1.schema.json",
    "contracts/schemas/liquidity_exit_zone_v1.schema.json",
    "src/crypto_quant_bot/contracts/timeframe_alignment.py",
    "src/crypto_quant_bot/market_analysis/alignment_adapter.py",
    "src/crypto_quant_bot/market_analysis/alignment_audit.py",
    "src/crypto_quant_bot/market_analysis/alignment_common.py",
    "src/crypto_quant_bot/market_analysis/alignment_config.py",
    "src/crypto_quant_bot/market_analysis/alignment_engine.py",
    "src/crypto_quant_bot/market_analysis/alignment_io.py",
    "src/crypto_quant_bot/market_analysis/alignment_math.py",
    "src/crypto_quant_bot/market_analysis/alignment_temporal.py",
    "scripts/run_lot26_multi_timeframe_alignment_engine.py",
    "scripts/validate_lot26.py",
    "tests/test_lot26_contracts.py",
    "tests/test_lot26_math.py",
    "tests/test_lot26_temporal.py",
    "tests/test_lot26_integration.py",
    "tests/test_lot26_io_and_runner.py",
    "data/audit/volatility_regime_confluence_timeframes_lot25.jsonl",
]

SCHEMA_FILES = [
    "contracts/schemas/timeframe_market_context_state_v1.schema.json",
    "contracts/schemas/closed_bar_availability_v1.schema.json",
    "contracts/schemas/multi_timeframe_alignment_state_v1.schema.json",
    "contracts/schemas/continuous_market_state_v1.schema.json",
    "contracts/schemas/multi_horizon_forecast_v1.schema.json",
    "contracts/schemas/participant_behavior_scenario_v1.schema.json",
    "contracts/schemas/liquidity_exit_zone_v1.schema.json",
]

FORBIDDEN_IMPLEMENTATION_FILES = [
    "src/crypto_quant_bot/market_analysis/continuous_market_state.py",
    "src/crypto_quant_bot/strategy_research/multi_horizon_forecast.py",
    "src/crypto_quant_bot/microstructure/participant_behavior.py",
]

FORBIDDEN_TEMPORARY_FILES = [
    ".github/workflows/apply-lot26-migration.yml",
    "scripts/apply_lot26_migration.py",
    "scripts/lot26_payload_00.txt",
    "scripts/lot26_payload_01.txt",
    "scripts/lot26_payload_02.txt",
    "scripts/lot26_payload_03.txt",
    "scripts/lot26_payload_04.txt",
]


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    evidence: str


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def _check(check_id: str, errors: list[str], success: str) -> Check:
    return Check(check_id, "PASS" if not errors else "FAIL", "; ".join(errors) or success)


def _required_files(root: Path) -> Check:
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]
    return _check("LOT26_REQUIRED_FILES", missing, f"{len(REQUIRED_FILES)} required files present")


def _temporary_files(root: Path) -> Check:
    present = [relative for relative in FORBIDDEN_TEMPORARY_FILES if (root / relative).exists()]
    return _check("LOT26_TEMPORARY_FILES_REMOVED", present, "one-shot migration files absent")


def _future_engines_locked(root: Path) -> Check:
    present = [relative for relative in FORBIDDEN_IMPLEMENTATION_FILES if (root / relative).exists()]
    return _check("POST_LOT26_FUTURE_ENGINES_LOCKED", present, "forecast and participant engines remain unimplemented")


def _schemas_closed(root: Path) -> Check:
    errors: list[str] = []
    for relative in SCHEMA_FILES:
        try:
            schema = _load_json(root / relative)
        except Exception as exc:
            errors.append(f"{relative}:{exc}")
            continue
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            errors.append(f"{relative}:schema not closed")
        if not isinstance(schema.get("required"), list) or not schema["required"]:
            errors.append(f"{relative}:required missing")
    return _check("LOT26_SCHEMAS_CLOSED", errors, f"{len(SCHEMA_FILES)} closed schemas validated")


def _alignment_policy(root: Path) -> Check:
    payload = _load_json(root / "config/math/multi_timeframe_alignment_v1.json")
    errors: list[str] = []
    if set(payload.get("component_weights", {})) != {"trend", "range", "momentum", "volatility", "regime", "confluence"}:
        errors.append("component weights incomplete")
    weights = [float(value) for value in payload.get("component_weights", {}).values()]
    if abs(sum(weights) - 1.0) > 1e-9:
        errors.append("component weights do not sum to one")
    time_policy = payload.get("time_policy", {})
    if time_policy.get("join_method") != "ASOF_BACKWARD":
        errors.append("join method is not ASOF_BACKWARD")
    restrictions = payload.get("promotion_restrictions", {})
    if not restrictions or any(value is not False for value in restrictions.values()):
        errors.append("promotion restrictions are not fail-closed")
    return _check("LOT26_ALIGNMENT_POLICY", errors, "alignment configuration is descriptive and fail-closed")


def _documentation_boundary(root: Path) -> Check:
    text = (root / "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md").read_text(encoding="utf-8")
    required = [
        "timebar-5m",
        "timebar-15m",
        "ASOF_BACKWARD",
        "used_for_decision=false",
        "forecast_generation_allowed=false",
        "probability_claims_allowed=false",
        "execution_allowed=false",
        "trade_allowed=false",
    ]
    errors = [token for token in required if token not in text]
    return _check("LOT26_DOCUMENTED_BOUNDARY", errors, "descriptive/non-trading boundary documented")


def _forecast_registry_locked(root: Path) -> Check:
    payload = _load_json(root / "config/research/forecast_horizon_registry_v1.json")
    errors: list[str] = []
    if payload.get("status") != "PLANNED_LOCKED_NOT_IMPLEMENTED":
        errors.append("forecast registry unlocked")
    restrictions = payload.get("lot26_restriction", {})
    if not restrictions or any(value is not False for value in restrictions.values()):
        errors.append("forecast restrictions invalid")
    return _check("LOT26_FORECASTS_LOCKED", errors, "future forecast horizons remain registry-only")


def run_checks(root: Path) -> list[Check]:
    return [
        _required_files(root),
        _temporary_files(root),
        _future_engines_locked(root),
        _schemas_closed(root),
        _alignment_policy(root),
        _documentation_boundary(root),
        _forecast_registry_locked(root),
    ]


def write_outputs(root: Path, checks: list[Check]) -> None:
    failures = [check for check in checks if check.status != "PASS"]
    verdict = "GO_LOT26_IMPLEMENTED" if not failures else "NO_GO"
    manifest = {
        "schema_version": "lot26-foundation-lifecycle-gate-v2",
        "verdict": verdict,
        "checks": [asdict(check) for check in checks],
        "documented_future_capabilities": [
            "continuous market state",
            "multi-horizon calibrated forecast",
            "participant behavior inference",
            "liquidity exit-zone inference",
        ],
        "trade_allowed": False,
        "execution_allowed": False,
    }
    manifest_path = root / "data/audit/pre_lot26_readiness_manifest.json"
    report_path = root / "reports/PRE_LOT26_ENTRY_GATE_REPORT.md"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Lot 26 Foundation and Lifecycle Gate",
        "",
        f"Verdict: **{verdict}**",
        "",
        "Lot 26 engine implementation is permitted and validated by its dedicated gates.",
        "Future continuous-state, forecast and participant engines remain locked.",
        "",
    ]
    lines.extend(f"- {check.check_id}: **{check.status}** — {check.evidence}" for check in checks)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Lot 26 foundation and lifecycle")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    checks = run_checks(root)
    if args.write_report:
        write_outputs(root, checks)
    failures = [check for check in checks if check.status != "PASS"]
    for check in checks:
        print(f"{check.check_id}: {check.status} — {check.evidence}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (  # noqa: E402
    build_lot45_artifacts,
)

GATE_MERGE = "390d0779f2be257fa8134faf8f02193a760a09c3"
SOURCE_HEAD = "019f4881aabb3c83f3f4b8b7349dd387dd319eae"
CERTIFICATION_ANCHOR = "bf6303fbcb3b73805fce6f25f76a8ec37ea45aaf"
EVIDENCE_HEAD = "6cd278817ecf83370977466f1a34794f65b3ac07"
VALIDATION_PROOF = (
    31821592585,
    9227184660,
    "sha256:efaf1a04018352fe56f420841bc56280fa28037400d2c11379cce5a9c55b25ec",
)
MUTATION_PROOF = (
    31821592626,
    9227209448,
    "sha256:3e87acd6f3d75b236df66ded62059a419b684a451d49dc9ecba7d26eb7888f6f",
)
QUALITY_PROOF = (
    31821388233,
    9227162672,
    "sha256:fd80f2e945b0b2dccfa277598f8e030ac34ccb3cb1c5be1da081a805be5cc76d",
)

STATE = ROOT / "data/audit/order_flow_delta_cvd_engine_lot45.json"
AUDIT = ROOT / "data/audit/order_flow_delta_cvd_engine_audit_lot45.json"
ORDER_FLOW = ROOT / "data/audit/order_flow_state_lot45.json"
CVD = ROOT / "data/audit/cvd_series_lot45.json"
COVERAGE = ROOT / "reports/lot45/coverage_summary.json"
MUTATION = ROOT / "reports/lot45/mutation_summary.json"

EXPECTED_HASHES = {
    STATE: "1d9244729e10999ec3406260cb894076f0ecc147166ef51478b38ff399206b90",
    AUDIT: "4573755d69ac739b2a45dd5dbdfe44786de4a2bd7c3f89d7de937064936c8488",
    ORDER_FLOW: "f7b7e04c555106c7ca312f81d3258d7afc288990c4ba2d1bfdc094d4c0c33502",
    CVD: "6a017b7b6932399ab46a654692dcafe28390f971226be8cf4a1af17f316335b6",
    COVERAGE: "fef3c99c9e4330512f7163b1e40e635a625f371b4bcbb9e84feaa83114532c73",
    MUTATION: "639d27adaf72da15375fc1ef60cb146b7bd16050b0924297ce31007e2732a07b",
}
EXPECTED_STATE = "de46340b9c3cb9a7a72bb0e809a4e1d7ab0193300a349d4c1631bbf7c0e4d5ff"
EXPECTED_AUDIT = "8524ec5ef3aac1972a8618a21ca46d4faa19f0667952ce0a7ec45d041d9281a8"
EXPECTED_ORDER_FLOW = "200585b65c124754c3e308aaf40eba2c98435ecac4f5a93815d278adcf887da0"
EXPECTED_CVD = "9f9bd3f9360e2f488a4b6d96a0e930b4353333e35debb3b47264793c1149979c"
EXPECTED_CONFIG = "2200905208b366f6230d76a35733fbde7338c3dc3902e3c6cc50999ba0d4fb30"
EXPECTED_LINEAGE = {
    "lineage_id": "lot45-from-certified-lot44-order-flow-inputs-v1",
    "entry_gate_checksum": "15ca4d69e59a0898f32eb9cbe558571ecf00ae496ec5d41075da1124393d4468",
    "entry_gate_merge_commit": GATE_MERGE,
    "lot44_state_checksum": "1a461cef0bedc0e2b34185ff538a64b1b53373b12b0633b749a34cee2b3c5541",
    "lot44_audit_checksum": "03ceda1c49746509f95e7f2ed039e8cc321e8e3cb4adbb946f1aef4ed3eba07d",
    "lot44_confidence_checksum": "7cb11e078d7f0d9ed0858229d8c6fe31a7cf653a238b280b05dbdd84d1250f05",
    "lot44_config_checksum": "dac06cb3235f3a09cbbb9b41098d7cf2593b94171659f50ef840d1633bfa95b7",
    "lot44_post_merge_checksum": "b8b531b2fcb09a30728549cc480d54d9be71504356468704c102ff085c39ea9a",
    "available_at": "2026-08-06T19:18:40.050000Z",
}
EXPECTED_SAFETY = {
    "analysis_only": True,
    "approved_size": 0,
    "execution_allowed": False,
    "external_connectivity_allowed": False,
    "market_event_publication_allowed": False,
    "network_ingestion_allowed": False,
    "order_routing_allowed": False,
    "participant_behavior_inference_explicitly_labeled": True,
    "raw_data_mutation_allowed": False,
    "real_credentials_allowed": False,
    "risk_approval_allowed": False,
    "scenario_score_is_signal": False,
    "signal_generation_allowed": False,
    "trade_allowed": False,
    "used_for_decision": False,
}
EXPECTED_REASON_CODES = [
    "LOT45_OFFLINE_ORDER_FLOW_DELTA_CVD_VALIDATED",
    "EVENT_TIME_TUMBLING_WINDOWS_ENFORCED",
    "UNKNOWN_VOLUME_PRESERVED_WITH_ZERO_SIGNED_CONTRIBUTION",
    "CVD_SESSION_RESET_POLICY_VERSIONED",
    "CLASSIFICATION_COVERAGE_AND_CONFIDENCE_BOUND",
    "NO_FUTURE_STATE_OR_LOOKAHEAD",
    "LOT46_REMAINS_LOCKED",
]
LOT46_FORBIDDEN = (
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine.py",
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine_models.py",
    "scripts/run_lot46_trade_classification_confidence_engine.py",
    "scripts/validate_lot46.py",
    "tests/test_lot46_trade_classification_confidence_engine.py",
    "data/audit/trade_classification_confidence_engine_lot46.json",
    "reports/lot_46_trade_classification_confidence_engine_report.md",
    "docs/LOT_46_TRADE_CLASSIFICATION_CONFIDENCE_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_46.md",
)


class Lot45FrozenEvidenceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot45FrozenEvidenceError(message)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_canonical(payload: dict[str, Any], field: str, expected: str) -> None:
    body = dict(payload)
    actual = body.pop(field, None)
    require(actual == expected, f"{field} changed")
    require(canonical_checksum(body) == expected, f"{field} canonical mismatch")


def _load_frozen() -> tuple[dict[str, Any], ...]:
    for path, expected in EXPECTED_HASHES.items():
        require(path.is_file(), f"missing frozen evidence: {path}")
        require(file_sha256(path) == expected, f"frozen evidence drifted: {path}")
    return tuple(
        load_json_object(path)
        for path in (STATE, AUDIT, ORDER_FLOW, CVD, COVERAGE, MUTATION)
    )


def _verify_links(
    state: dict[str, Any],
    audit: dict[str, Any],
    order_flow: dict[str, Any],
    cvd: dict[str, Any],
) -> None:
    verify_canonical(state, "output_checksum", EXPECTED_STATE)
    verify_canonical(audit, "audit_checksum", EXPECTED_AUDIT)
    verify_canonical(order_flow, "order_flow_checksum", EXPECTED_ORDER_FLOW)
    verify_canonical(cvd, "cvd_checksum", EXPECTED_CVD)
    require(state["order_flow"] == order_flow, "state/order-flow payload mismatch")
    require(state["cvd_series"] == cvd, "state/CVD payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(audit["order_flow_checksum"] == EXPECTED_ORDER_FLOW, "audit/order-flow link changed")
    require(audit["cvd_checksum"] == EXPECTED_CVD, "audit/CVD link changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source changed")
    require(audit["code_commit"] == SOURCE_HEAD, "audit source changed")
    require(audit["config_checksum"] == EXPECTED_CONFIG, "audit config checksum changed")
    require(state["safety"] == EXPECTED_SAFETY, "state safety boundary changed")
    require(audit["safety"] == EXPECTED_SAFETY, "audit safety boundary changed")
    require(state["reason_codes"] == EXPECTED_REASON_CODES, "reason codes changed")
    require(
        state["validation_state"] == "VALIDATED_OFFLINE_ORDER_FLOW_DELTA_CVD_ONLY",
        "validation state changed",
    )
    require(
        state["run_context"]["runtime_mode"] == "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "runtime mode changed",
    )
    for field, expected in EXPECTED_LINEAGE.items():
        require(state["lineage"][field] == expected, f"lineage changed: {field}")


def _verify_reference(order_flow: dict[str, Any], cvd: dict[str, Any]) -> None:
    expected_metrics = {
        "trades_total": 3,
        "buy_trades_total": 1,
        "sell_trades_total": 1,
        "unknown_trades_total": 1,
        "total_volume": "0.16",
        "buy_volume": "0.08",
        "sell_volume": "0.03",
        "unknown_volume": "0.05",
        "signed_delta": "0.05",
        "unknown_volume_ratio": "0.3125",
        "classification_coverage": "0.6875",
        "confidence_weighted_coverage": "0.6875",
    }
    for field, expected in expected_metrics.items():
        require(order_flow[field] == expected, f"reference metric changed: {field}")
    require(len(order_flow["windows"]) == 1, "reference window count changed")
    window = order_flow["windows"][0]
    require(
        window["window_checksum"]
        == "bbe4fabcc1ec72075353552a7dfbd55d21b815de7ace991df8697b78799a3ab5",
        "reference window checksum changed",
    )
    require(len(cvd["points"]) == 1, "reference CVD point count changed")
    require(cvd["points"][0]["cvd"] == "0.05", "reference CVD changed")
    require(cvd["points"][0]["signed_delta"] == "0.05", "reference CVD delta changed")


def _verify_quality(coverage: dict[str, Any], mutation: dict[str, Any]) -> None:
    require(coverage["status"] == "PASS", "coverage not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source changed")
    require(coverage["line_coverage_percent"] == 98.25, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 92.59, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake count changed")
    require(mutation["status"] == "PASS", "mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source changed")
    require(mutation["mutation_score_percent"] == 82.48, "mutation score changed")
    require(mutation["killed_mutants"] == 871, "killed mutant count changed")
    require(mutation["survived_mutants"] == 185, "survived mutant count changed")
    require(mutation["evaluated_mutants"] == 1056, "evaluated mutant count changed")
    require(mutation["completed_mutants"] == 1056, "completed mutant count changed")
    require(mutation["total_mutants"] == 1056, "total mutant count changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout present")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutation present")
    require(mutation["mutmut_run_exit_code"] == 0, "mutmut run exit changed")
    require(mutation["mutmut_results_exit_code"] == 0, "mutmut results exit changed")


def _verify_runtime_replay(
    state: dict[str, Any],
    audit: dict[str, Any],
    order_flow: dict[str, Any],
    cvd: dict[str, Any],
) -> None:
    replay = build_lot45_artifacts(ROOT, SOURCE_HEAD)
    expected = (state, audit, order_flow, cvd)
    require(replay == expected, "frozen Lot45 runtime replay diverged")


def _verify_downstream_lock() -> None:
    for relative in LOT46_FORBIDDEN:
        require(not (ROOT / relative).exists(), f"Lot46 must remain locked: {relative}")


def validate() -> dict[str, object]:
    state, audit, order_flow, cvd, coverage, mutation = _load_frozen()
    _verify_links(state, audit, order_flow, cvd)
    _verify_reference(order_flow, cvd)
    _verify_quality(coverage, mutation)
    _verify_runtime_replay(state, audit, order_flow, cvd)
    _verify_downstream_lock()
    return {
        "schema_version": "lot45-frozen-evidence-validation-v1",
        "status": "PASS",
        "verdict": "PASS_LOT45_FROZEN_EVIDENCE",
        "gate_merge": GATE_MERGE,
        "source_head": SOURCE_HEAD,
        "certification_anchor": CERTIFICATION_ANCHOR,
        "evidence_head": EVIDENCE_HEAD,
        "state_output_checksum": EXPECTED_STATE,
        "audit_checksum": EXPECTED_AUDIT,
        "order_flow_checksum": EXPECTED_ORDER_FLOW,
        "cvd_checksum": EXPECTED_CVD,
        "line_coverage_percent": coverage["line_coverage_percent"],
        "branch_coverage_percent": coverage["branch_coverage_percent"],
        "mutation_score_percent": mutation["mutation_score_percent"],
        "validation_run": VALIDATION_PROOF[0],
        "validation_artifact": VALIDATION_PROOF[1],
        "validation_artifact_digest": VALIDATION_PROOF[2],
        "mutation_run": MUTATION_PROOF[0],
        "mutation_artifact": MUTATION_PROOF[1],
        "mutation_artifact_digest": MUTATION_PROOF[2],
        "quality_run": QUALITY_PROOF[0],
        "quality_artifact": QUALITY_PROOF[1],
        "quality_artifact_digest": QUALITY_PROOF[2],
        "lot46_status": "PLANNED_LOCKED",
    }


def main() -> int:
    try:
        result = validate()
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(f"LOT45 FROZEN EVIDENCE: FAIL\n{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    load_json_object,
)

GATE_MERGE = "6bbf4fcc5543f2599378bcab93263e2c8cebcec6"
SOURCE_HEAD = "fe11756c449fccc9cccf7013feac2997024721c9"
CERTIFICATION_ANCHOR = "9015895b9af447c70fa94e0f1c2b1f488d98a5bb"
EVIDENCE_HEAD = "d2e17da18c0e6c30fb9a908d187981e125de1fc9"
SUPERSEDED_FROZEN_HEADS = (
    "e2141fb19fd9d200ada823ebcc14df26f81f5506",
    "9f8d088836776ed7319bc4d94daeed797322ca14",
    "c3a8d67478a662c4e446d52a998011d2860752ab",
    "63b0a2993d5d3194a95409be13d5ced21891e2aa",
)
VALIDATION_PROOF = (
    31735127552,
    9194818454,
    "sha256:5bd4a4968d3ff8326989aa9604507584f4324c956ab4c20491eca6fd45290533",
)
MUTATION_PROOF = (
    31735127586,
    9194907241,
    "sha256:7aadc01392145118947d9bf2ff0f390c74d753a99af0ad7d54d5e9e394538a21",
)
QUALITY_PROOF = (
    31735127653,
    9194894989,
    "sha256:c0f8bd0d6ca824846f164b461b64a4b1ec316dc360dabdabc2c3f2e6a5a10490",
)

STATE = ROOT / "data/audit/trades_and_aggressor_classification_schema_lot44.json"
AUDIT = ROOT / "data/audit/trades_and_aggressor_classification_schema_audit_lot44.json"
CONFIDENCE = ROOT / "data/audit/aggressor_confidence_state_lot44.json"
COVERAGE = ROOT / "reports/lot44/coverage_summary.json"
MUTATION = ROOT / "reports/lot44/mutation_summary.json"

EXPECTED_HASHES = {
    STATE: "c838bab414966d53647bf88a3a65e29ca8f68295940a57dc383f9ea590bf6cc7",
    AUDIT: "7b527013ac2dbf43ff86dfccff7f362aa85516e7638e35db306a21f29bfca9b2",
    CONFIDENCE: "20c5d82709d8fa2ef03e789bc691472b9015d2fe657dec7751ae0a6076cfd027",
    COVERAGE: "dea0b7ded8aa58f462210cd6499c5acff61bf9ba688e35d6dee6db964a0a7868",
    MUTATION: "cb3c35900c66cc36fcd9e54d06643cdd90f96d72de7a4021803984f36407a5c2",
}
EXPECTED_STATE = "9e37e2e25361451a86f2f8872d3caf3e725bd230ecba6b3a1b354676456210f7"
EXPECTED_AUDIT = "e0e5dff87a05c02fdf6330ccd19ff0af1b61fba879662f02174d89d4dd69aa4d"
EXPECTED_CONFIDENCE = "7cb11e078d7f0d9ed0858229d8c6fe31a7cf653a238b280b05dbdd84d1250f05"
EXPECTED_LINEAGE = {
    "entry_gate_checksum": "100d21ea18cfd7d9fe275ac0bea162c76a0bb7e5f85e319b543b4053e3c4d5ef",
    "lot43_state_checksum": "30671ea4add13eaa23f22556ea227dc7300d69f1ea3153e0486cd4e50c7bd3f6",
    "lot43_audit_checksum": "3ca8d203fdd6392941e5a86fc2905af510bd7005dcb0f3b1e6b8c820053b1e67",
    "lot43_resilience_checksum": "598c08bf863e8fed65e3045081b774a80500c8129a0eb71a6c865e74c1bf8ddb",
    "lot43_post_merge_checksum": "167c69b324377ceefd322d59fab7f42d9f7998efde94503d6d86ca4a51ed9c14",
    "trade_fixture_checksum": "b07e3a6a784c801c9ae386a33a1cbe1f936901b1549d5001bc5e53e42de9e2f8",
    "order_book_snapshot_checksum": "0d63ca7ac1ca48b44e58c0b0f1eb8946190eaf2da6745c2bbd2dd8de14f49b16",
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
DOWNSTREAM_FORBIDDEN = (
    "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine.py",
    "src/crypto_quant_bot/microstructure/order_flow_delta_and_cvd_engine_models.py",
    "scripts/run_lot45_order_flow_delta_and_cvd_engine.py",
    "scripts/validate_lot45.py",
    "tests/test_lot45_order_flow_delta_and_cvd_engine.py",
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine.py",
    "src/crypto_quant_bot/microstructure/trade_classification_confidence_engine_models.py",
    "scripts/run_lot46_trade_classification_confidence_engine.py",
    "scripts/validate_lot46.py",
    "tests/test_lot46_trade_classification_confidence_engine.py",
)


class Lot44FrozenEvidenceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Lot44FrozenEvidenceError(message)


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
        load_json_object(path) for path in (STATE, AUDIT, CONFIDENCE, COVERAGE, MUTATION)
    )


def _verify_links(
    state: dict[str, Any],
    audit: dict[str, Any],
    confidence: dict[str, Any],
) -> None:
    verify_canonical(state, "output_checksum", EXPECTED_STATE)
    verify_canonical(audit, "audit_checksum", EXPECTED_AUDIT)
    verify_canonical(confidence, "confidence_checksum", EXPECTED_CONFIDENCE)
    require(state["confidence_state"] == confidence, "state/confidence payload mismatch")
    require(audit["state_output_checksum"] == EXPECTED_STATE, "audit/state link changed")
    require(state["run_context"]["code_commit"] == SOURCE_HEAD, "state source changed")
    require(audit["code_commit"] == SOURCE_HEAD, "audit source changed")
    require(state["safety"] == EXPECTED_SAFETY, "state safety boundary changed")
    require(audit["safety"] == EXPECTED_SAFETY, "audit safety boundary changed")
    for field, expected in EXPECTED_LINEAGE.items():
        require(state["lineage"][field] == expected, f"lineage changed: {field}")


def _verify_reference(state: dict[str, Any], confidence: dict[str, Any]) -> None:
    expected = (
        ("fixture-trade-001", "UNKNOWN", "NONE", "0", "50025", "0.05"),
        ("fixture-trade-002", "BUY_AGGRESSOR", "QUOTE_TEST", "1", "50025.1", "0.08"),
        ("fixture-trade-003", "SELL_AGGRESSOR", "QUOTE_TEST", "1", "50024.9", "0.03"),
    )
    actual = tuple(
        (
            item["trade"]["trade_id"],
            item["aggressor_classification"],
            item["classification_method"],
            item["confidence"],
            item["trade"]["price"],
            item["trade"]["quantity"],
        )
        for item in state["classified_trades"]
    )
    require(actual == expected, "reference trade classification changed")
    require(
        (
            confidence["quote_test_confidence"],
            confidence["tick_rule_confidence"],
            confidence["unknown_confidence"],
        )
        == ("1", "0.5", "0"),
        "v1 confidence constants changed",
    )
    require(
        confidence["policy_version"] == "lot44-aggressor-confidence-v1",
        "confidence version changed",
    )
    require(
        confidence["semantics"] == "DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY",
        "confidence semantics changed",
    )


def _verify_metrics(state: dict[str, Any]) -> None:
    trades = state["classified_trades"]
    quantities = [
        (item["aggressor_classification"], Decimal(item["trade"]["quantity"]))
        for item in trades
    ]
    total = sum((quantity for _, quantity in quantities), Decimal("0"))
    buy = sum(
        (quantity for side, quantity in quantities if side == "BUY_AGGRESSOR"),
        Decimal("0"),
    )
    sell = sum(
        (quantity for side, quantity in quantities if side == "SELL_AGGRESSOR"),
        Decimal("0"),
    )
    unknown = sum(
        (quantity for side, quantity in quantities if side == "UNKNOWN"),
        Decimal("0"),
    )
    metrics = state["metrics"]
    require(metrics["lot_44_trades_total"] == len(trades), "trade count mismatch")
    require(metrics["lot_44_buy_trades_total"] == 1, "buy count mismatch")
    require(metrics["lot_44_sell_trades_total"] == 1, "sell count mismatch")
    require(metrics["lot_44_unknown_trades_total"] == 1, "unknown count mismatch")
    require(Decimal(metrics["total_volume"]) == total, "total volume mismatch")
    require(Decimal(metrics["buy_volume"]) == buy, "buy volume mismatch")
    require(Decimal(metrics["sell_volume"]) == sell, "sell volume mismatch")
    require(Decimal(metrics["unknown_volume"]) == unknown, "unknown volume mismatch")
    require(Decimal(metrics["unknown_volume_ratio"]) == unknown / total, "unknown ratio mismatch")


def _verify_quality(coverage: dict[str, Any], mutation: dict[str, Any]) -> None:
    require(coverage["status"] == "PASS", "coverage not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source changed")
    require(coverage["line_coverage_percent"] == 98.78, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 96.67, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake changed")
    require(mutation["status"] == "PASS", "mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source changed")
    require(mutation["mutation_score_percent"] == 80.18, "mutation score changed")
    require(mutation["killed_mutants"] == 1436, "killed mutants changed")
    require(mutation["survived_mutants"] == 355, "survived mutants changed")
    require(mutation["total_mutants"] == 1791, "total mutants changed")
    require(mutation["evaluated_mutants"] == 1791, "evaluated mutants changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout present")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutation present")


def _verify_downstream_lock() -> None:
    for relative in DOWNSTREAM_FORBIDDEN:
        require(not (ROOT / relative).exists(), f"downstream lot must remain locked: {relative}")


def validate() -> dict[str, object]:
    state, audit, confidence, coverage, mutation = _load_frozen()
    _verify_links(state, audit, confidence)
    _verify_reference(state, confidence)
    _verify_metrics(state)
    _verify_quality(coverage, mutation)
    _verify_downstream_lock()
    return {
        "schema_version": "lot44-frozen-evidence-validation-v6",
        "status": "PASS",
        "gate_merge": GATE_MERGE,
        "source_head": SOURCE_HEAD,
        "certification_anchor": CERTIFICATION_ANCHOR,
        "evidence_head": EVIDENCE_HEAD,
        "superseded_frozen_heads": list(SUPERSEDED_FROZEN_HEADS),
        "state_output_checksum": EXPECTED_STATE,
        "audit_checksum": EXPECTED_AUDIT,
        "confidence_checksum": EXPECTED_CONFIDENCE,
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
        "review_hardening": {
            "causal_event_and_receive_time": True,
            "tick_history_identity_match": True,
            "classification_tuple_exact": True,
            "state_metrics_recomputed": True,
            "confidence_v1_constants_exact": True,
            "signed_zero_normalized": True,
            "confidence_version_exact": True,
            "runtime_confidence_identifier_models_exact": True,
            "safety_mapping_immutable": True,
        },
        "lot45_status": "PLANNED_LOCKED",
        "lot46_status": "PLANNED_LOCKED",
    }


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

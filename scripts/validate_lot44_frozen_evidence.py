#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema import (  # noqa: E402
    build_lot44_artifacts,
)

GATE_MERGE = "6bbf4fcc5543f2599378bcab93263e2c8cebcec6"
SOURCE_HEAD = "d3cc4cf916ecea5166716746143a593f01b1d051"
CERTIFICATION_ANCHOR = "720b6f895672b650a7c7df96cdf68524479ae3f4"
EVIDENCE_HEAD = "8ca3edadb7e811bad428575cfe236b20dd5ed62f"
SUPERSEDED_FROZEN_HEADS = (
    "e2141fb19fd9d200ada823ebcc14df26f81f5506",
    "9f8d088836776ed7319bc4d94daeed797322ca14",
    "c3a8d67478a662c4e446d52a998011d2860752ab",
    "63b0a2993d5d3194a95409be13d5ced21891e2aa",
    "ab2eb038c66013eb50aa6e86f9c56ad5f2794a33",
    "58e958950d79390dae986cd281cd30f664a8799c",
)
VALIDATION_PROOF = (
    31736603829,
    9195388909,
    "sha256:b0f153b3ff7705efb004ff30127dfff6728c1ba71ab5ed962bf33214353ebe92",
)
MUTATION_PROOF = (
    31736603916,
    9195444786,
    "sha256:15889e3916e610fae26980cdb5a92974ee2193552a41055971690a5845378155",
)
QUALITY_PROOF = (
    31736603821,
    9195454897,
    "sha256:821f594d393c8491da5b7c98b936f886aad1016779364f6221ea774bd023c633",
)

STATE = ROOT / "data/audit/trades_and_aggressor_classification_schema_lot44.json"
AUDIT = ROOT / "data/audit/trades_and_aggressor_classification_schema_audit_lot44.json"
CONFIDENCE = ROOT / "data/audit/aggressor_confidence_state_lot44.json"
COVERAGE = ROOT / "reports/lot44/coverage_summary.json"
MUTATION = ROOT / "reports/lot44/mutation_summary.json"

EXPECTED_HASHES = {
    STATE: "f4613bcd7bd435872c00cece23cccfeaede0ac07849279841bff73360bd47c22",
    AUDIT: "d10cc1fa4f7bb247a84b23e8cb8e7b7ee2b45a2b2d107fee29d742438156cae1",
    CONFIDENCE: "20c5d82709d8fa2ef03e789bc691472b9015d2fe657dec7751ae0a6076cfd027",
    COVERAGE: "369805934c6f0ee5d0674f803e4a75651bca8a355b1f92f97d8e4b15c467e009",
    MUTATION: "a90a02e0187bd106501368a1c00102adae26bab731522baddb9f0ca8e9188627",
}
EXPECTED_STATE = "1a461cef0bedc0e2b34185ff538a64b1b53373b12b0633b749a34cee2b3c5541"
EXPECTED_AUDIT = "03ceda1c49746509f95e7f2ed039e8cc321e8e3cb4adbb946f1aef4ed3eba07d"
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


def _verify_runtime_collection_freeze() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=SOURCE_HEAD)
    supplied = list(state.classified_trades)
    candidate = replace(state, classified_trades=supplied)
    require(
        isinstance(candidate.classified_trades, tuple),
        "classified trades were not defensively frozen",
    )
    before = candidate.to_dict()
    supplied.clear()
    require(
        candidate.to_dict() == before,
        "caller-owned classified trade collection mutated frozen state",
    )


def _verify_downstream_lock() -> None:
    for relative in DOWNSTREAM_FORBIDDEN:
        require(not (ROOT / relative).exists(), f"downstream lot must remain locked: {relative}")


def validate() -> dict[str, object]:
    state, audit, confidence, coverage, mutation = _load_frozen()
    _verify_links(state, audit, confidence)
    _verify_reference(state, confidence)
    _verify_metrics(state)
    _verify_quality(coverage, mutation)
    _verify_runtime_collection_freeze()
    _verify_downstream_lock()
    return {
        "schema_version": "lot44-frozen-evidence-validation-v7",
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
            "state_trade_timestamp_envelope_exact": True,
            "classified_trade_quote_evidence_binding_exact": True,
            "classified_trades_defensively_frozen": True,
        },
        "lot45_status": "PLANNED_LOCKED",
        "lot46_status": "PLANNED_LOCKED",
    }


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

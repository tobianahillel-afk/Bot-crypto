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
SOURCE_HEAD = "2f6779fa2be6dbb78fac1a824d470e66cf2ffa9f"
CERTIFICATION_ANCHOR = "95c855ede9cccc77dc89d2ce176e531f5dcd4ee1"
EVIDENCE_HEAD = "20118feab2ddba2a67a467b28f33eee22520ab25"
SUPERSEDED_FROZEN_HEADS = (
    "e2141fb19fd9d200ada823ebcc14df26f81f5506",
    "9f8d088836776ed7319bc4d94daeed797322ca14",
)
VALIDATION_PROOF = (
    31698772338,
    9180407783,
    "sha256:4147d1afbc9b553aaff72bf5d278a5ea2a5c217e9a8ebdc56a9ce8980b21e40e",
)
MUTATION_PROOF = (
    31698772097,
    9180440721,
    "sha256:040da9e6a770edf7a6fe11e819e4ffb2a1aafbb9e8f372655949e9409fc228c7",
)

STATE = ROOT / "data/audit/trades_and_aggressor_classification_schema_lot44.json"
AUDIT = ROOT / "data/audit/trades_and_aggressor_classification_schema_audit_lot44.json"
CONFIDENCE = ROOT / "data/audit/aggressor_confidence_state_lot44.json"
COVERAGE = ROOT / "reports/lot44/coverage_summary.json"
MUTATION = ROOT / "reports/lot44/mutation_summary.json"

EXPECTED_HASHES = {
    STATE: "f78b7a1c841be9c899f590b2f99a5e94d52a61d8fa066ad92b7381e28f418954",
    AUDIT: "58666081f0bcdd41c977a3a61583ddbe5ae342dfb12eac32dd8b9df207b4e89a",
    CONFIDENCE: "20c5d82709d8fa2ef03e789bc691472b9015d2fe657dec7751ae0a6076cfd027",
    COVERAGE: "3265cec978f2ef9f488e1d791c1e7bc3f0e1da05a1f28bbd1ad53fd37eaa2f5d",
    MUTATION: "065c1a8dbbc367eedf31190b2072cd635ffa76275b74eab139ea3824635b860c",
}
EXPECTED_STATE = "3afacfb257f03026840c7f61d172bd257027bf3b625ffbe991f58c59c2410ba8"
EXPECTED_AUDIT = "a320af13bf8e18b31bb063437dfb97a6eb32657fbdeac93c58a76931109ac8a3"
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
        confidence["semantics"] == "DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY",
        "confidence semantics changed",
    )


def _verify_metrics(state: dict[str, Any]) -> None:
    trades = state["classified_trades"]
    quantities = [(item["aggressor_classification"], Decimal(item["trade"]["quantity"])) for item in trades]
    total = sum((quantity for _, quantity in quantities), Decimal("0"))
    buy = sum((quantity for side, quantity in quantities if side == "BUY_AGGRESSOR"), Decimal("0"))
    sell = sum((quantity for side, quantity in quantities if side == "SELL_AGGRESSOR"), Decimal("0"))
    unknown = sum((quantity for side, quantity in quantities if side == "UNKNOWN"), Decimal("0"))
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
    require(coverage["line_coverage_percent"] == 98.91, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 100.0, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake changed")
    require(mutation["status"] == "PASS", "mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source changed")
    require(mutation["mutation_score_percent"] == 81.66, "mutation score changed")
    require(mutation["killed_mutants"] == 1367, "killed mutants changed")
    require(mutation["survived_mutants"] == 307, "survived mutants changed")
    require(mutation["total_mutants"] == 1674, "total mutants changed")
    require(mutation["evaluated_mutants"] == 1674, "evaluated mutants changed")
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
        "schema_version": "lot44-frozen-evidence-validation-v3",
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
        "review_hardening": {
            "causal_event_and_receive_time": True,
            "tick_history_identity_match": True,
            "classification_tuple_exact": True,
            "state_metrics_recomputed": True,
            "confidence_v1_constants_exact": True,
        },
        "lot45_status": "PLANNED_LOCKED",
        "lot46_status": "PLANNED_LOCKED",
    }


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

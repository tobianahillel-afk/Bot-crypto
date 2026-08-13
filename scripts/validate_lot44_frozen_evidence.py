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

GATE_MERGE = "6bbf4fcc5543f2599378bcab93263e2c8cebcec6"
SOURCE_HEAD = "fd6d4d88608b80a7f27d561f59988072177d00b2"
CERTIFICATION_ANCHOR = "74dce49ba636cb47ae09fcef7de48bdc3d21de15"
EVIDENCE_HEAD = "dc9fb81b2b32858b75180d6b632346577df02d1e"
VALIDATION_PROOF = (
    31686334383,
    9175566934,
    "sha256:c46fe1ce78ebd7d0b3c53c92a7e2dc384e0533db01fc8a2d5c35f9cab6229a27",
)
MUTATION_PROOF = (
    31686334377,
    9175606543,
    "sha256:2ac06ae633ebe463615f94323435e8e21d6bc6bea975fed3e2647e1c01db7a10",
)

STATE = ROOT / "data/audit/trades_and_aggressor_classification_schema_lot44.json"
AUDIT = ROOT / "data/audit/trades_and_aggressor_classification_schema_audit_lot44.json"
CONFIDENCE = ROOT / "data/audit/aggressor_confidence_state_lot44.json"
COVERAGE = ROOT / "reports/lot44/coverage_summary.json"
MUTATION = ROOT / "reports/lot44/mutation_summary.json"

EXPECTED_HASHES = {
    STATE: "09c211e4fa243fcb79a01264afb4d21c8b132a0ab5b488260e595aaf7f9eb36e",
    AUDIT: "82dbb582430a0c3600981bcdbfd58f1353f8cd80d609f2cb5a9c20fcd1592374",
    CONFIDENCE: "20c5d82709d8fa2ef03e789bc691472b9015d2fe657dec7751ae0a6076cfd027",
    COVERAGE: "c0f5330701ad77cd3a6f41d43be64fc9d6c57eda96411c5ce40a9977a4223009",
    MUTATION: "155a21fe93a4b5a619cb696af5bb64f63958b61ede605212c07140917c293610",
}
EXPECTED_STATE = "13073e0c1dc620670eb9f66ae4fc3a228993f36da96899f3a85cc4ce980123c9"
EXPECTED_AUDIT = "8a818942b1e49a2755dd86eff629c31006128b2c1d3be060b1d8a170a501a836"
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
    require(audit["entry_gate_checksum"] == EXPECTED_LINEAGE["entry_gate_checksum"], "audit gate changed")
    require(audit["trade_fixture_checksum"] == EXPECTED_LINEAGE["trade_fixture_checksum"], "audit trade fixture changed")
    require(audit["order_book_snapshot_checksum"] == EXPECTED_LINEAGE["order_book_snapshot_checksum"], "audit snapshot changed")


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
    require(state["metrics"]["total_volume"] == "0.16", "total volume changed")
    require(state["metrics"]["buy_volume"] == "0.08", "buy volume changed")
    require(state["metrics"]["sell_volume"] == "0.03", "sell volume changed")
    require(state["metrics"]["unknown_volume"] == "0.05", "unknown volume changed")
    require(state["metrics"]["unknown_volume_ratio"] == "0.3125", "unknown ratio changed")
    require(confidence["quote_test_confidence"] == "1", "quote confidence changed")
    require(confidence["tick_rule_confidence"] == "0.5", "tick confidence changed")
    require(confidence["unknown_confidence"] == "0", "unknown confidence changed")
    require(confidence["semantics"] == "DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY", "confidence semantics changed")


def _verify_quality(coverage: dict[str, Any], mutation: dict[str, Any]) -> None:
    require(coverage["status"] == "PASS", "coverage not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source changed")
    require(coverage["line_coverage_percent"] == 98.86, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 100.0, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake changed")
    require(mutation["status"] == "PASS", "mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source changed")
    require(mutation["mutation_score_percent"] == 81.01, "mutation score changed")
    require(mutation["killed_mutants"] == 1237, "killed mutants changed")
    require(mutation["survived_mutants"] == 290, "survived mutants changed")
    require(mutation["total_mutants"] == 1527, "total mutants changed")
    require(mutation["evaluated_mutants"] == 1527, "evaluated mutants changed")
    require(mutation["timeout_mutants"] == 0, "mutation timeout present")
    require(mutation["suspicious_mutants"] == 0, "suspicious mutation present")


def _verify_downstream_lock() -> None:
    for relative in DOWNSTREAM_FORBIDDEN:
        require(not (ROOT / relative).exists(), f"downstream lot must remain locked: {relative}")


def validate() -> dict[str, object]:
    state, audit, confidence, coverage, mutation = _load_frozen()
    _verify_links(state, audit, confidence)
    _verify_reference(state, confidence)
    _verify_quality(coverage, mutation)
    _verify_downstream_lock()
    return {
        "schema_version": "lot44-frozen-evidence-validation-v1",
        "status": "PASS",
        "gate_merge": GATE_MERGE,
        "source_head": SOURCE_HEAD,
        "certification_anchor": CERTIFICATION_ANCHOR,
        "evidence_head": EVIDENCE_HEAD,
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
        "lot45_status": "PLANNED_LOCKED",
        "lot46_status": "PLANNED_LOCKED",
    }


def main() -> None:
    print(json.dumps(validate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

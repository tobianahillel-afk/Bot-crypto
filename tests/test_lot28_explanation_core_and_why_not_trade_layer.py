from __future__ import annotations

import json

from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer import (
    build_explanation_state,
    replay_matches,
)
from tests.lot28_fixtures import load_config, load_inputs

COMMIT = "abcdef1234567890"

GOLDEN_TEXTS = (
    "Global context is GLOBAL_CONTEXT_MIXED with weighted coverage 1.000000.",
    "Observed category support is trending=0.166955, range=0.151198, mixed=0.116448, conflict=0.130000.",
    "Multi-timeframe alignment is MTF_DIVERGENT; coherence is MTF_INCOHERENT.",
    "Aggregate descriptive evidence score is 0.564600; it is not calibrated as a probability.",
    "The descriptive sources do not support one coherent context because MTF_DIVERGENT remains explicit.",
    "All 5 configured descriptive sources are present and validated.",
    "Trending support 0.166955 and range support 0.151198 coexist with conflict support 0.130000.",
    "No calibrated confidence interval is available for the heterogeneous descriptive sources.",
    "Runtime policy is local offline analysis only.",
    "Executable promotion is blocked because the global context is mixed.",
    "Executable promotion is blocked because multi-timeframe divergence remains unresolved.",
    "Executable promotion is blocked because decision, signal, routing and execution permissions are disabled.",
    "Forecast, signal, risk approval and order details are not applicable in this offline descriptive layer.",
    "No executable action is produced; a future validated promotion gate would be required before reconsideration.",
)


def all_statements(state: object) -> list[dict[str, object]]:
    bundle = state.bundle.to_dict()  # type: ignore[attr-defined]
    result: list[dict[str, object]] = []
    for section, items in bundle.items():
        if section in {"schema_version", "why_not_trade"}:
            continue
        result.extend(items)
    return result


def test_real_lot27_lot26_explanation_matches_golden_text() -> None:
    global_context, alignment = load_inputs()
    state = build_explanation_state(global_context, alignment, load_config(), COMMIT)
    statements = all_statements(state)
    assert tuple(item["text"] for item in statements) == GOLDEN_TEXTS
    assert len(statements) == 14
    assert state.bundle.assumptions == ()
    assert state.bundle.why_not_trade.dominant_reason_code == "WNT_PERMISSIONS_DISABLED"
    assert tuple(item.reason_code for item in state.bundle.why_not_trade.reasons) == (
        "WNT_CONTEXT_MIXED",
        "WNT_MTF_DIVERGENCE",
        "WNT_PERMISSIONS_DISABLED",
    )
    assert state.bundle.why_not_trade.no_order_intent_created is True
    assert state.trade_allowed is False
    assert state.execution_allowed is False
    assert state.used_for_decision is False


def test_every_statement_and_reason_has_source_evidence() -> None:
    global_context, alignment = load_inputs()
    state = build_explanation_state(global_context, alignment, load_config(), COMMIT)
    for statement in all_statements(state):
        assert statement["evidence_refs"]
        for reference in statement["evidence_refs"]:
            assert reference["artifact_path"]
            assert len(reference["artifact_checksum"]) == 64
            assert str(reference["json_pointer"]).startswith("/")
    for reason in state.bundle.why_not_trade.reasons:
        assert reason.evidence_refs
        assert reason.order_intent_created is False


def test_output_contains_no_forbidden_direction_or_sizing_tokens() -> None:
    global_context, alignment = load_inputs()
    state = build_explanation_state(global_context, alignment, load_config(), COMMIT)
    serialized = json.dumps(state.to_dict(), sort_keys=True)
    for token in ("BUY", "SELL", "position_size"):
        assert token not in serialized


def test_replay_is_exact_and_commit_changes_identity() -> None:
    global_context, alignment = load_inputs()
    config = load_config()
    first = build_explanation_state(global_context, alignment, config, COMMIT)
    second = build_explanation_state(global_context, alignment, config, COMMIT)
    changed = build_explanation_state(global_context, alignment, config, "fedcba0987654321")
    assert replay_matches(first, second)
    assert first.output_checksum == second.output_checksum
    assert first.explanation_id != changed.explanation_id
    assert first.lineage_id != changed.lineage_id
    assert first.output_checksum != changed.output_checksum


def test_evidence_registry_covers_both_input_artifacts() -> None:
    global_context, alignment = load_inputs()
    state = build_explanation_state(global_context, alignment, load_config(), COMMIT)
    assert set(state.input_checksums) == {"global_context", "multi_timeframe_alignment"}
    assert all(len(value) == 64 for value in state.input_checksums.values())
    paths = {
        reference["artifact_path"]
        for statement in all_statements(state)
        for reference in statement["evidence_refs"]
    }
    assert paths == {
        "data/audit/global_market_context_aggregator_lot27.json",
        "data/audit/multi_timeframe_alignment_engine_lot26.json",
    }

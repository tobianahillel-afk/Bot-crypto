#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Callable
from dataclasses import replace
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Decimal, localcontext
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (  # noqa: E402
    canonical_checksum,
    load_json_object,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (  # noqa: E402
    CALCULATION_DECIMAL_ROUNDING,
    CODE_BOUND_PATHS,
    OrderFlowPolicy,
    _build_engine_state,
    build_lot45_artifacts,
    build_order_flow,
)
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (  # noqa: E402
    POLICY_VERSION,
    SESSION_POLICY_VERSION,
    WINDOW_POLICY_VERSION,
    Lot45ValidationError,
    parse_utc_timestamp,
    reject_untracked_executable_sources,
)
from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (  # noqa: E402
    ClassifiedTradeV1,
    TimestampedTradeV1,
)

GATE_MERGE = "390d0779f2be257fa8134faf8f02193a760a09c3"
SOURCE_HEAD = "89ec5c692622d80222eb63bfa2732242d4a84987"
CERTIFICATION_ANCHOR = "880b91afc0f4590d91504be47168519e4ef1aa11"
EVIDENCE_HEAD = "45c52cdd2560901b70eb8d1bcdddb0dbb5775f11"

VALIDATION_PROOF = (
    31970067676,
    9269557580,
    "sha256:d72b4cf5516559975a6282be40f6eadb2faa257dbfaa742a8fb1052c1b63a1ba",
)
MUTATION_PROOF = (
    31970067634,
    9269574905,
    "sha256:1f7d7ca74da0fad2de2b130f8e00acfcafc01160a6b089b74acf5fef204fe91d",
)
QUALITY_PROOF = (
    31970067631,
    9269584831,
    "sha256:69ade2a67752867b2a3da648b489918681c1938a633b7523ed1948b00dfc1b21",
)
QUALITY_GLOBAL_COVERAGE_SHA256 = (
    "ffbe4463824d3144ffa45b2068cd5ce776a0970ae7d7e90c2d58659ef5d1a7c1"
)
QUALITY_MUTATION_SCORE_SHA256 = (
    "678b53c31bdd93760360ead142833bd90b36319093fc2dac1f3c7a6d3af6ec3a"
)
QUALITY_ENGINEERING_DEVIATION_SHA256 = (
    "2622d31a7f9093dacb95f7aeacd7b5e0ce1f08e58eec244a7e1e21d7a8604d14"
)

STATE = ROOT / "data/audit/order_flow_delta_and_cvd_engine_lot45.json"
AUDIT = ROOT / "data/audit/order_flow_delta_and_cvd_engine_audit_lot45.json"
ORDER_FLOW = ROOT / "data/audit/order_flow_state_lot45.json"
CVD = ROOT / "data/audit/cvd_series_lot45.json"
COVERAGE = ROOT / "reports/lot45/coverage_summary.json"
MUTATION = ROOT / "reports/lot45/mutation_summary.json"
SCHEMA_ROOT = ROOT / "contracts/schemas"
OLD_STATE_ALIAS = ROOT / "data/audit/order_flow_delta_cvd_engine_lot45.json"
OLD_AUDIT_ALIAS = ROOT / "data/audit/order_flow_delta_cvd_engine_audit_lot45.json"

EXPECTED_HASHES = {
    STATE: "dd39aa211c6c3027fa05020aa408e673368ea446931cd330b478edb3d887df52",
    AUDIT: "2fb1e70b871f0f839e349b07b2d3ad8292de3cdc3643acac2125d654fbf62f37",
    ORDER_FLOW: "f9d46121e552dcea5eca7306befa47114d9602e81be32a19bc565221398724f8",
    CVD: "a8923ce2fb08a571059a411edd4e2b0dd1d0a7116727a66edd9046c0e70d352f",
    COVERAGE: "db3b3b75c3c32c755968b68b22c009c4b6558aaa0a5feff7bd6ba41fb74695a7",
    MUTATION: "2ba8ccd5b4b6a670753ce9f9c53d69a1a87eccbd32a060a207edbe38c8d8f540",
}
EXPECTED_STATE = "24cca6d239ada8471b407bd66e3d4340790155ced5bc7d1c56034b81ccabc38a"
EXPECTED_AUDIT = "260c0014be23819118d051cb6630910f0f3d4d274164c17e98bf0eff88239642"
EXPECTED_ORDER_FLOW = "3dc7a0d4836090509d12239c2a407cfa3afd736fa7d3f80ef2c2eeed3b4fa9ea"
EXPECTED_CVD = "68e6f47f0df214f74279c9749b1cfd1ac9e0cead7484bff9a098ee34481aa559"
EXPECTED_WINDOW = "09bd6b8809622b450f04e98c5d519a0fb3cc9f9b3c749eaa588f97499aebc10c"
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
UTC_TIMESTAMP_PATTERN = (
    r"^(?!0000-)(?:"
    r"(?:[0-9]{4}-(?:(?:01|03|05|07|08|10|12)-(?:0[1-9]|[12][0-9]|3[01])"
    r"|(?:04|06|09|11)-(?:0[1-9]|[12][0-9]|30)|02-(?:0[1-9]|1[0-9]|2[0-8])))"
    r"|(?:(?:[0-9]{2}(?:0[48]|[2468][048]|[13579][26])|(?:[02468][048]|[13579][26])00)-02-29)"
    r")T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\.[0-9]{6}Z$"
)
ZERO_SHA256 = "0" * 64
QUOTE_SHA256 = "1" * 64


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
    require(not OLD_STATE_ALIAS.exists(), "stale Lot45 state alias still exists")
    require(not OLD_AUDIT_ALIAS.exists(), "stale Lot45 audit alias still exists")
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

    windows = order_flow["windows"]
    points = cvd["points"]
    require(len(windows) == len(points), "CVD/window cardinality changed")
    for window, point in zip(windows, points, strict=True):
        window_body = dict(window)
        actual_window_checksum = window_body.pop("window_checksum")
        require(
            canonical_checksum(window_body) == actual_window_checksum,
            "frozen window checksum is not canonical",
        )
        require(point["window_checksum"] == actual_window_checksum, "CVD/window checksum drift")
        require(point["event_time"] == window["event_time"], "CVD/window event-time drift")
        require(point["session_id"] == window["session_id"], "CVD/window session drift")
        require(point["signed_delta"] == window["signed_delta"], "CVD/window delta drift")


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
        "confidence_weighted_volume": "0.11",
        "confidence_weighted_coverage": "0.6875",
    }
    for field, expected in expected_metrics.items():
        require(order_flow[field] == expected, f"reference metric changed: {field}")
    require(len(order_flow["windows"]) == 1, "reference window count changed")
    require(
        order_flow["windows"][0]["window_checksum"] == EXPECTED_WINDOW,
        "reference window checksum changed",
    )
    require(len(cvd["points"]) == 1, "reference CVD point count changed")
    require(cvd["points"][0]["cvd"] == "0.05", "reference CVD changed")


def _verify_quality(coverage: dict[str, Any], mutation: dict[str, Any]) -> None:
    require(coverage["status"] == "PASS", "coverage not PASS")
    require(coverage["source_head_sha"] == SOURCE_HEAD, "coverage source changed")
    require(coverage["line_coverage_percent"] == 97.36, "line coverage changed")
    require(coverage["branch_coverage_percent"] == 90.32, "branch coverage changed")
    require(coverage["anti_flake_repetitions"] == 3, "anti-flake count changed")

    require(mutation["status"] == "PASS", "mutation not PASS")
    require(mutation["source_head_sha"] == SOURCE_HEAD, "mutation source changed")
    require(mutation["mutation_score_percent"] == 81.19, "mutation score changed")
    require(mutation["killed_mutants"] == 1269, "killed mutant count changed")
    require(mutation["survived_mutants"] == 294, "survived mutant count changed")
    require(mutation["evaluated_mutants"] == 1563, "evaluated mutant count changed")
    require(mutation["completed_mutants"] == 1563, "completed mutant count changed")
    require(mutation["total_mutants"] == 1563, "total mutant count changed")
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
    require(replay == (state, audit, order_flow, cvd), "frozen Lot45 runtime replay diverged")


def _policy() -> OrderFlowPolicy:
    return OrderFlowPolicy(
        50,
        1_000_000,
        2_000_000,
        Decimal("1"),
        WINDOW_POLICY_VERSION,
        SESSION_POLICY_VERSION,
        POLICY_VERSION,
    )


def _classified(
    trade_id: str,
    quantity: str,
    unknown: bool,
    *,
    event_time: str,
    receive_time: str,
) -> ClassifiedTradeV1:
    trade = TimestampedTradeV1(
        "source-a",
        "venue-a",
        "BTC-USDT",
        "SPOT",
        trade_id,
        event_time,
        receive_time,
        Decimal("100"),
        Decimal(quantity),
        "UNKNOWN",
    )
    if unknown:
        return ClassifiedTradeV1(
            trade,
            "UNKNOWN",
            "NONE",
            Decimal("0"),
            "lot44-aggressor-confidence-v1",
            ZERO_SHA256,
            ("UNKNOWN_REFERENCE",),
        )
    return ClassifiedTradeV1(
        trade,
        "BUY_AGGRESSOR",
        "QUOTE_TEST",
        Decimal("1"),
        "lot44-aggressor-confidence-v1",
        QUOTE_SHA256,
        ("QUOTE_REFERENCE",),
    )


def _expect_lot45_rejection(action: Callable[[], object], message: str) -> None:
    try:
        action()
    except Lot45ValidationError:
        return
    raise Lot45FrozenEvidenceError(message)


def _verify_decimal_and_policy_hardening() -> None:
    require(
        CALCULATION_DECIMAL_ROUNDING == ROUND_HALF_EVEN,
        "Lot45 builder Decimal rounding contract changed",
    )
    require("src/crypto_quant_bot" in CODE_BOUND_PATHS, "package-tree binding weakened")

    first = "12345678901234567890123456789"
    second = "12345678901234567890123456788"
    trades = (
        _classified(
            "hp-w1-buy",
            first,
            False,
            event_time="2026-08-06T19:18:40.100000Z",
            receive_time="2026-08-06T19:18:40.110000Z",
        ),
        _classified(
            "hp-w1-unknown",
            "1",
            True,
            event_time="2026-08-06T19:18:40.200000Z",
            receive_time="2026-08-06T19:18:40.210000Z",
        ),
        _classified(
            "hp-w2-buy",
            second,
            False,
            event_time="2026-08-06T19:18:41.100000Z",
            receive_time="2026-08-06T19:18:41.110000Z",
        ),
        _classified(
            "hp-w2-unknown",
            "1",
            True,
            event_time="2026-08-06T19:18:41.200000Z",
            receive_time="2026-08-06T19:18:41.210000Z",
        ),
    )
    flow, cvd = build_order_flow(trades, _policy())
    for precision in (9, 28):
        for rounding in (ROUND_DOWN, ROUND_UP):
            with localcontext() as ambient:
                ambient.prec = precision
                ambient.rounding = rounding
                replayed_flow = replace(
                    flow,
                    windows=tuple(replace(window) for window in flow.windows),
                )
                replayed_cvd = replace(
                    cvd,
                    points=tuple(replace(point) for point in cvd.points),
                )
            require(replayed_flow.to_dict() == flow.to_dict(), "ambient Decimal changed flow")
            require(replayed_cvd.to_dict() == cvd.to_dict(), "ambient Decimal changed CVD")

    weighted = (
        _classified(
            "weighted-w1-buy",
            "1",
            False,
            event_time="2026-08-06T19:18:40.100000Z",
            receive_time="2026-08-06T19:18:40.110000Z",
        ),
        _classified(
            "weighted-w1-unknown",
            "1",
            True,
            event_time="2026-08-06T19:18:40.200000Z",
            receive_time="2026-08-06T19:18:40.210000Z",
        ),
        _classified(
            "weighted-w2-buy",
            "5",
            False,
            event_time="2026-08-06T19:18:41.100000Z",
            receive_time="2026-08-06T19:18:41.110000Z",
        ),
        _classified(
            "weighted-w2-unknown",
            "8",
            True,
            event_time="2026-08-06T19:18:41.200000Z",
            receive_time="2026-08-06T19:18:41.210000Z",
        ),
    )
    weighted_flow, weighted_cvd = build_order_flow(weighted, _policy())
    require(weighted_flow.confidence_weighted_volume == Decimal("6"), "raw weight lost")
    require(weighted_flow.confidence_weighted_coverage == Decimal("0.4"), "weight drift")

    first_window = weighted_flow.windows[0]
    first_point = weighted_cvd.points[0]
    _expect_lot45_rejection(
        lambda: replace(first_window, session_id="2026-08-05"),
        "forged window session accepted",
    )
    _expect_lot45_rejection(
        lambda: replace(first_point, session_id="2026-08-05"),
        "forged CVD session accepted",
    )
    _expect_lot45_rejection(
        lambda: replace(
            first_window,
            window_start="2026-08-06T19:18:40.050000Z",
            window_end="2026-08-06T19:18:40.900000Z",
        ),
        "forged tumbling window accepted",
    )


def _verify_timestamp_hardening() -> None:
    parse_utc_timestamp("2026-08-06T19:18:40.000000Z", "reference_timestamp")
    for invalid in (
        "2026-08-06T19:18:40Z",
        "2026-08-06T19:18:40.000000+00:00",
        "2026-08-06 19:18:40.000000Z",
        "2026-02-31T19:18:40.000000Z",
        "1900-02-29T19:18:40.000000Z",
    ):
        _expect_lot45_rejection(
            lambda value=invalid: parse_utc_timestamp(value, "adversarial_timestamp"),
            f"invalid runtime timestamp accepted: {invalid}",
        )

    state = load_json_object(SCHEMA_ROOT / "order_flow_delta_cvd_engine_state_v1.schema.json")
    flow = load_json_object(SCHEMA_ROOT / "order_flow_state_v1.schema.json")
    cvd = load_json_object(SCHEMA_ROOT / "cvd_series_v1.schema.json")
    state_props = state["properties"]
    nodes = [state_props[field] for field in ("event_time", "receive_time", "generated_at")]
    nodes.append(state_props["lineage"]["properties"]["available_at"])
    window_props = flow["properties"]["windows"]["items"]["properties"]
    nodes.extend(window_props[field] for field in ("window_start", "window_end", "event_time", "receive_time"))
    nodes.append(cvd["properties"]["points"]["items"]["properties"]["event_time"])
    for node in nodes:
        require(node["pattern"] == UTC_TIMESTAMP_PATTERN, "Lot45 timestamp schema pattern drifted")
        require(node.get("format") == "date-time", "Lot45 timestamp schema format drifted")
        pattern = node["pattern"]
        require(
            re.fullmatch(pattern, "2026-08-06T19:18:40.000000Z") is not None,
            "canonical UTC timestamp rejected by schema",
        )
        require(
            re.fullmatch(pattern, "2024-02-29T00:00:00.000000Z") is not None,
            "valid Gregorian leap timestamp rejected by schema",
        )
        for invalid in (
            "2026-08-06T19:18:40Z",
            "2026-02-29T19:18:40.000000Z",
            "2026-02-31T19:18:40.000000Z",
            "2026-04-31T19:18:40.000000Z",
            "1900-02-29T19:18:40.000000Z",
            "2100-02-29T19:18:40.000000Z",
        ):
            require(
                re.fullmatch(pattern, invalid) is None,
                f"calendar-invalid timestamp accepted by schema: {invalid}",
            )


def _verify_executable_source_binding() -> None:
    reject_untracked_executable_sources(ROOT, SOURCE_HEAD)
    adversarial = ROOT / "src/sitecustomize.py"
    require(not adversarial.exists(), "unexpected sitecustomize before adversarial check")
    try:
        adversarial.write_text("MARKER = 'lot45-frozen-adversarial'\n", encoding="utf-8")
        _expect_lot45_rejection(
            lambda: reject_untracked_executable_sources(ROOT, SOURCE_HEAD),
            "untracked executable source was accepted",
        )
    finally:
        adversarial.unlink(missing_ok=True)


def _verify_checksum_authenticity() -> None:
    trades = (
        _classified(
            "checksum-binding-trade",
            "1",
            False,
            event_time="2026-08-06T19:18:40.100000Z",
            receive_time="2026-08-06T19:18:40.110000Z",
        ),
    )
    flow, cvd = build_order_flow(trades, _policy())
    forged_checksum = "f" * 64
    forged_window = replace(flow.windows[0], window_checksum=forged_checksum)
    forged_flow = replace(flow, windows=(forged_window,))
    forged_flow = replace(
        forged_flow,
        order_flow_checksum=canonical_checksum(forged_flow.payload_without_checksum()),
    )
    forged_point = replace(cvd.points[0], window_checksum=forged_checksum)
    forged_cvd = replace(cvd, points=(forged_point,))
    forged_cvd = replace(
        forged_cvd,
        cvd_checksum=canonical_checksum(forged_cvd.payload_without_checksum()),
    )
    config = {
        "run_id": "lot45-frozen-checksum-adversarial",
        "correlation_id": "lot45-frozen-checksum-adversarial",
        "lineage_id": "lot45-from-certified-lot44-order-flow-inputs-v1",
        "generated_at": "2026-08-06T19:18:41.100000Z",
    }
    state44 = {"receive_time": "2026-08-06T19:18:40.050000Z"}
    _expect_lot45_rejection(
        lambda: _build_engine_state(
            config,
            SOURCE_HEAD,
            state44,
            trades,
            forged_flow,
            forged_cvd,
        ),
        "coordinated forged window/CVD checksum was accepted",
    )


def _verify_downstream_lock() -> None:
    for relative in LOT46_FORBIDDEN:
        require(not (ROOT / relative).exists(), f"Lot46 must remain locked: {relative}")


def validate() -> dict[str, object]:
    state, audit, order_flow, cvd, coverage, mutation = _load_frozen()
    _verify_links(state, audit, order_flow, cvd)
    _verify_reference(order_flow, cvd)
    _verify_quality(coverage, mutation)
    _verify_runtime_replay(state, audit, order_flow, cvd)
    _verify_decimal_and_policy_hardening()
    _verify_timestamp_hardening()
    _verify_executable_source_binding()
    _verify_checksum_authenticity()
    _verify_downstream_lock()
    return {
        "schema_version": "lot45-frozen-evidence-validation-v7",
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
        "quality_global_coverage_sha256": QUALITY_GLOBAL_COVERAGE_SHA256,
        "quality_mutation_score_sha256": QUALITY_MUTATION_SCORE_SHA256,
        "quality_engineering_deviation_sha256": QUALITY_ENGINEERING_DEVIATION_SHA256,
        "review_hardening": {
            "canonical_runtime_utc_timestamps": True,
            "calendar_valid_utc_schema_timestamps": True,
            "canonical_window_checksum_authenticity": True,
            "executable_source_inventory_bound_to_code_commit": True,
            "builder_decimal_rounding": "ROUND_HALF_EVEN",
            "complete_package_tree_binding": True,
            "raw_weighted_volume_aggregation": True,
            "event_time_session_binding": True,
            "cvd_window_metric_binding": True,
            "event_time_tumbling_window_binding": True,
        },
        "artifact_authentication_required_by_workflow": True,
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

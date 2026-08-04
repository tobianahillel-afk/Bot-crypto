from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_quant_bot.audit.available_at import (
    _walk_nested_temporal,
    audit_available_at,
    audit_used_for_decision,
)
from crypto_quant_bot.contracts.decision import DecisionContract
from crypto_quant_bot.contracts.market_data import MinimalMarketDataSnapshot
from crypto_quant_bot.contracts.range_state import RangeStatePoint
from crypto_quant_bot.contracts.replay import ReplayRecord
from crypto_quant_bot.contracts.risk import RiskDecision
from crypto_quant_bot.core.logger import JsonLogEvent, JsonLogger
from crypto_quant_bot.replay import replay_registry
from crypto_quant_bot.replay.replay_registry import ReplayRegistry
from crypto_quant_bot.security.security_policy import SecurityPolicy


def test_available_at_audit_exercises_temporal_and_nested_failures() -> None:
    rows = [
        {
            "timestamp": "2026-01-02T00:00:00Z",
            "available_at": "2026-01-01T00:00:00Z",
            "usable_from": "2026-01-03T00:00:00Z",
            "component_available_at": {
                "price": "2026-01-04T00:00:00Z",
                "volume": "",
                "regime": None,
            },
            "nearest_pivots": [
                "ignored",
                {
                    "usable_from": "2026-01-05T00:00:00Z",
                    "available_at": "2026-01-06T00:00:00Z",
                },
            ],
            "nearest_zones": [
                {
                    "usable_from": "2025-12-31T00:00:00Z",
                    "available_at": "2025-12-31T00:00:00Z",
                }
            ],
        },
        {"available_at": "", "nearest_pivots": []},
        {"available_at": None, "nearest_zones": "not-a-list"},
        {"timestamp": "2026-01-01T00:00:00Z"},
    ]
    violations = audit_available_at(rows, "dataset.jsonl")
    rules = {item["rule"] for item in violations}
    assert "available_at must be non-empty" in rules
    assert "timestamp <= available_at" in rules
    assert "usable_from <= available_at" in rules
    assert "component_available_at <= available_at" in rules
    assert "component_available_at must be non-empty string" in rules
    assert "MarketStatePoint available_at >= max(component_available_at)" in rules
    assert "usable_from <= row.available_at" in rules
    assert "nested available_at <= row.available_at" in rules
    assert all(item["dataset_path"] == "dataset.jsonl" for item in violations)


def test_nested_temporal_scan_covers_dict_list_and_node_limit() -> None:
    nested = {
        "available_at": "2026-01-03T00:00:00Z",
        "children": [
            {
                "usable_from": "2026-01-04T00:00:00Z",
                "nested": [{"available_at": "2026-01-05T00:00:00Z"}],
            },
            "ignored",
        ],
    }
    violations = _walk_nested_temporal(
        nested,
        dataset_path=Path("nested.jsonl"),
        row_index=7,
        row_available_at="2026-01-01T00:00:00Z",
    )
    paths = {item["path"] for item in violations}
    assert "$.available_at" in paths
    assert "$.children[0].usable_from" in paths
    assert "$.children[0].nested[0].available_at" in paths

    limited = _walk_nested_temporal(
        {"child": {"grandchild": {}}},
        dataset_path="limited.jsonl",
        row_index=1,
        row_available_at="2026-01-01T00:00:00Z",
        max_nodes=1,
    )
    assert limited == [
        {
            "dataset_path": "limited.jsonl",
            "row_index": 1,
            "path": "$.child",
            "rule": "nested temporal scan node limit",
            "value": 2,
            "reference": 1,
        }
    ]


def test_used_for_decision_audit_accepts_only_explicit_false() -> None:
    violations = audit_used_for_decision(
        [
            {"used_for_decision": False},
            {"used_for_decision": True},
            {},
            {"used_for_decision": 0},
        ],
        "decision.jsonl",
    )
    assert [item["row_index"] for item in violations] == [2, 3, 4]
    assert all(item["reference"] is False for item in violations)


def test_replay_registry_saves_loads_and_uses_both_directory_policies(tmp_path: Path) -> None:
    decision = DecisionContract(timestamp="2026-01-01T00:00:00Z")

    custom = ReplayRegistry(tmp_path / "custom")
    record = custom.save_decision(decision)
    assert isinstance(record, ReplayRecord)
    assert record.replay_id == decision.replay_id
    assert record.decision_id == decision.decision_id
    assert Path(record.path).name == "latest_validation_replay.json"
    assert custom.load("missing") == decision.to_dict()

    reports = ReplayRegistry(tmp_path / "reports")
    reports_record = reports.save_decision(decision)
    assert Path(reports_record.path).parent == tmp_path / "data" / "audit" / "replay_validation"

    direct = custom.base_dir / "direct.json"
    direct.write_text(json.dumps({"source": "direct"}), encoding="utf-8")
    assert custom.load("direct") == {"source": "direct"}


def test_replay_registry_cleans_temporary_file_on_replace_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry = ReplayRegistry(tmp_path / "custom")
    monkeypatch.setattr(
        replay_registry.os,
        "replace",
        lambda _source, _target: (_ for _ in ()).throw(RuntimeError("replace failed")),
    )
    with pytest.raises(RuntimeError, match="replace failed"):
        registry.save_decision(DecisionContract())
    assert list((tmp_path / "custom" / "replay_validation").glob("*.tmp")) == []
    assert list((tmp_path / "custom" / "replay_validation").glob(".*.tmp")) == []


def test_json_logger_outputs_stable_structured_lines(capsys: pytest.CaptureFixture[str]) -> None:
    event = JsonLogEvent(
        event_type="RISK_VETO",
        level="warning",
        message="échec fermé",
        context={"reason": "stale"},
        timestamp="2026-01-01T00:00:00+00:00",
    )
    payload = json.loads(event.to_json())
    assert payload == {
        "context": {"reason": "stale"},
        "event_type": "RISK_VETO",
        "level": "warning",
        "message": "échec fermé",
        "timestamp": "2026-01-01T00:00:00+00:00",
    }

    logger = JsonLogger()
    line = logger.log("HEARTBEAT", "info", "ok", None)
    captured = capsys.readouterr().out.strip()
    assert captured == line
    assert json.loads(line)["context"] == {}
    with_context = logger.log("HEARTBEAT", "info", "ok", {"latency_ms": 3})
    assert json.loads(with_context)["context"] == {"latency_ms": 3}


def test_security_and_simple_contracts_remain_fail_closed() -> None:
    security = SecurityPolicy().current_state()
    assert security.withdrawal_permission_allowed is False
    assert security.live_trading_enabled is False
    assert security.secrets_allowed_in_git is False
    assert security.validation_status == "validated_lot0"

    market = MinimalMarketDataSnapshot()
    risk = RiskDecision()
    range_state = RangeStatePoint()
    replay = ReplayRecord()
    assert market.pair == "BTC/EUR"
    assert market.has_data is False
    assert risk.trade_allowed is False
    assert risk.vetoes == ["risk_veto"]
    assert range_state.range_state == "unknown"
    assert replay.replay_id == ""
    risk.vetoes.append("local")
    assert RiskDecision().vetoes == ["risk_veto"]

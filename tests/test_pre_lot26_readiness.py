from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_pre_lot26_readiness.py"


def _load_module() -> ModuleType:
    module_name = "validate_pre_lot26_readiness_test_module"
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, object]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_lot26_foundation_lifecycle_checks_pass() -> None:
    module = _load_module()
    failures = [check for check in module.run_checks(ROOT) if check.status != "PASS"]
    assert not failures, failures


def test_temporal_registry_activates_only_initial_edge() -> None:
    payload = _load_json("config/temporal/temporal_scale_registry_v1.json")
    profile = payload["lot26_initial_profile"]
    assert isinstance(profile, dict)
    assert profile["local_scale_id"] == "timebar-5m"
    assert profile["higher_scale_id"] == "timebar-15m"
    assert profile["extensible_interface_required"] is True
    scales = payload["scales"]
    assert isinstance(scales, list)
    assert {item["scale_id"] for item in scales if item["enabled_in_lot26"] is True} == {"timebar-5m", "timebar-15m"}


def test_temporal_dimensions_are_explicitly_separate() -> None:
    payload = _load_json("config/temporal/temporal_scale_registry_v1.json")
    principles = payload["principles"]
    assert isinstance(principles, dict)
    assert principles["data_resolution_is_not_forecast_horizon"] is True
    assert principles["forecast_horizon_is_not_decision_clock"] is True
    assert principles["decision_clock_is_not_holding_horizon"] is True
    assert principles["naive_timeframe_voting_forbidden"] is True


def test_lot26_decision_clock_is_closed_local_bar_only() -> None:
    payload = _load_json("config/temporal/decision_clock_policy_v1.json")
    policy = payload["lot26_policy"]
    assert isinstance(policy, dict)
    assert policy["enabled_triggers"] == ["CLOSED_LOCAL_BAR"]
    assert policy["trade_decision_allowed"] is False


def test_forecast_horizons_are_registered_but_locked() -> None:
    payload = _load_json("config/research/forecast_horizon_registry_v1.json")
    assert payload["status"] == "PLANNED_LOCKED_NOT_IMPLEMENTED"
    horizons = payload["horizons"]
    assert isinstance(horizons, list)
    assert {item["horizon_id"] for item in horizons} >= {"30s", "5m", "15m", "1h"}
    restrictions = payload["lot26_restriction"]
    assert isinstance(restrictions, dict)
    assert all(value is False for value in restrictions.values())


def test_all_schemas_are_closed_objects() -> None:
    module = _load_module()
    for relative in module.SCHEMA_FILES:
        schema = _load_json(relative)
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert isinstance(schema["required"], list) and schema["required"]


def test_participant_and_exit_zone_taxonomy_is_complete() -> None:
    schema = _load_json("contracts/schemas/liquidity_exit_zone_v1.schema.json")
    properties = schema["properties"]
    assert isinstance(properties, dict)
    zone_type = properties["zone_type"]
    assert isinstance(zone_type, dict)
    assert set(zone_type["enum"]) == {
        "STOP_LOSS_CLUSTER", "TAKE_PROFIT_CLUSTER", "BREAK_EVEN_CLUSTER", "LIQUIDATION_CLUSTER",
        "ENTRY_CONGESTION_ZONE", "TRAPPED_POSITION_ZONE", "FORCED_EXIT_ZONE", "PASSIVE_DEFENSE_ZONE",
    }


def test_lot26_documents_forbid_forecast_and_execution() -> None:
    text = (ROOT / "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md").read_text(encoding="utf-8")
    for token in (
        "forecast_generation_allowed=false", "probability_claims_allowed=false",
        "execution_allowed=false", "trade_allowed=false", "Game Theory",
    ):
        assert token in text


def test_only_future_engines_remain_unimplemented() -> None:
    module = _load_module()
    assert not [relative for relative in module.FORBIDDEN_IMPLEMENTATION_FILES if (ROOT / relative).exists()]
    assert (ROOT / "src/crypto_quant_bot/market_analysis/alignment_engine.py").is_file()


def test_lifecycle_report_can_be_generated(tmp_path: Path) -> None:
    module = _load_module()
    checks = [module.Check("EXAMPLE", "PASS", "evidence")]
    module.write_outputs(tmp_path, checks)
    manifest = json.loads((tmp_path / "data/audit/pre_lot26_readiness_manifest.json").read_text(encoding="utf-8"))
    report = (tmp_path / "reports/PRE_LOT26_ENTRY_GATE_REPORT.md").read_text(encoding="utf-8")
    assert manifest["verdict"] == "GO_LOT26_IMPLEMENTED"
    assert "continuous market state" in manifest["documented_future_capabilities"]
    assert "**GO_LOT26_IMPLEMENTED**" in report
    assert "Lot 26 engine" in report

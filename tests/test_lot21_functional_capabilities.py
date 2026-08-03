import json
from pathlib import Path

from crypto_quant_bot.product_scope import MANDATORY_CAPABILITY_IDS

ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES_PATH = ROOT / "data" / "audit" / "product_scope_capabilities_lot21.jsonl"


def _load_capabilities() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with CAPABILITIES_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _find_capability(capabilities: list[dict[str, object]], capability_id: str) -> dict[str, object]:
    for capability in capabilities:
        if capability["capability_id"] == capability_id:
            return capability
    raise AssertionError(f"missing capability: {capability_id}")


def test_lot21_mandatory_capabilities_are_all_present():
    capabilities = _load_capabilities()
    capability_ids = [capability["capability_id"] for capability in capabilities]
    assert capability_ids == MANDATORY_CAPABILITY_IDS


def test_lot21_key_capability_blocks_are_covered():
    capabilities = _load_capabilities()
    assert _find_capability(capabilities, "research_os")["status"] == "RESEARCH_ONLY"
    assert _find_capability(capabilities, "ai_news_event_engine")["phase"] == "V7_AI_NEWS_EVENT_ENGINE"
    assert _find_capability(capabilities, "graphical_interface")["phase"] == "V8_UI_DASHBOARD"
    assert _find_capability(capabilities, "account_analysis_read_only")["phase"] == "V9_ACCOUNT_READ_ONLY"
    assert _find_capability(capabilities, "sandbox_demo_trading")["status"] == "FUTURE_DEMO_ONLY"
    assert _find_capability(capabilities, "future_personal_live_trading")["status"] == "FUTURE_LIVE_GATED"


def test_lot21_capabilities_remain_non_active():
    capabilities = _load_capabilities()
    for capability in capabilities:
        if capability["capability_id"] == "v1_defensive_audit_closure":
            assert capability["status"] == "DONE_V1_DEFENSIVE"
            assert capability["not_yet_implemented"] is False
        else:
            assert capability["not_yet_implemented"] is True
            assert capability["execution_allowed"] is False
        assert capability["external_connectivity_allowed"] is False
        assert capability["acceptance_required_before_activation"]

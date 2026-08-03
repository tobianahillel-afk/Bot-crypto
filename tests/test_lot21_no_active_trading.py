import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "audit" / "product_scope_lot21.json"
CAPABILITIES_PATH = ROOT / "data" / "audit" / "product_scope_capabilities_lot21.jsonl"


def _load_capabilities() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with CAPABILITIES_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot21_registry_keeps_global_trading_flags_blocked():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert registry["execution_allowed"] is False
    assert registry["trade_allowed"] is False
    assert registry["external_connectivity_allowed"] is False
    assert registry["live_execution"] == "DISABLED"
    assert registry["leverage"] == "FORBIDDEN"


def test_lot21_future_capabilities_are_not_active():
    capabilities = _load_capabilities()
    non_v1 = [capability for capability in capabilities if capability["capability_id"] != "v1_defensive_audit_closure"]
    assert all(capability["not_yet_implemented"] is True for capability in non_v1)
    assert all(capability["execution_allowed"] is False for capability in non_v1)
    assert all(capability["external_connectivity_allowed"] is False for capability in non_v1)


def test_lot21_scope_block_reasons_cover_required_gates():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    required_reasons = {
        "V2_SCOPE_LOCK_ONLY",
        "NO_EXECUTION_ALLOWED",
        "NO_EXTERNAL_CONNECTIVITY",
        "NO_EXCHANGE_CONNECTOR",
        "NO_ORDER_ROUTER",
        "NO_API_KEYS",
        "NO_WEBSOCKET",
        "NO_PAPER_TRADING_ACTIVE",
        "NO_LIVE_TRADING_ACTIVE",
        "EDUCATIONAL_MODE_ONLY",
        "HUMAN_REVIEW_REQUIRED_BEFORE_IMPLEMENTATION",
    }
    assert required_reasons.issubset(set(registry["scope_block_reasons"]))

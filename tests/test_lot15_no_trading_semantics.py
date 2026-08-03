import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "data" / "audit" / "decision_ledger_lot15_5m.jsonl",
    ROOT / "data" / "audit" / "decision_ledger_lot15_15m.jsonl",
]
ALLOWED_KEYS = {
    "ledger_block_reasons",
    "order_routing_allowed",
    "ledger_entry_id",
    "entry_checksum",
    "previous_entry_checksum",
}
ALLOWED_VALUES = {"ORDER_ROUTING_NOT_ALLOWED"}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def walk(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key), value
            yield from walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk(item)


def test_lot15_outputs_have_no_forbidden_trading_keys_or_direction_values():
    forbidden_key_tokens = [
        "ord" + "er",
        "ord" + "er_id",
        "fi" + "ll",
        "pn" + "l",
        "pro" + "fit",
        "lo" + "ss",
        "pos" + "ition",
        "tar" + "get",
        "lab" + "el",
        "fu" + "ture",
        "lo" + "ng",
        "sho" + "rt",
        "bu" + "y",
        "se" + "ll",
        "ent" + "ry",
        "ex" + "it",
        "stop_" + "loss",
        "take_" + "profit",
        "paper_" + "trading",
    ]
    forbidden_values = {"LONG", "SHORT", "BUY", "SELL", "ENTRY", "EXIT"}
    forbidden_text_values = {
        "web" + "socket",
        "ws" + "://",
        "wss" + "://",
        "http" + "://",
        "https" + "://",
        "api_" + "key",
    }
    for path in PATHS:
        for row in load_jsonl(path):
            for key, value in walk(row):
                lowered = key.lower()
                if lowered in ALLOWED_KEYS:
                    continue
                assert not any(token in lowered for token in forbidden_key_tokens)
                if isinstance(value, str):
                    if value in ALLOWED_VALUES:
                        continue
                    lowered_value = value.lower()
                    assert not any(token in lowered_value for token in forbidden_key_tokens)
                    assert not any(token in lowered_value for token in forbidden_text_values)
                    assert value.upper() not in forbidden_values


def test_lot15_outputs_keep_all_execution_paths_blocked():
    for path in PATHS:
        for row in load_jsonl(path):
            assert row["final_decision"] == "WAIT"
            assert row["final_system_decision"] == "BLOCK_TRADING"
            assert row["execution_allowed"] is False
            assert row["trade_allowed"] is False
            assert row["used_for_decision"] is False
            assert row["risk_allowed"] is False
            assert row["exposure_allowed"] is False
            assert row["portfolio_change_allowed"] is False
            assert row["allocation_change_allowed"] is False
            assert row["rebalance_allowed"] is False
            assert row["order_routing_allowed"] is False
            assert row["external_connectivity_allowed"] is False
            assert row["human_review_required"] is True
            assert row["ledger_state"] == "RECORDED"
            assert row["audit_trail_state"] == "ACTIVE"
            assert row["immutability_mode"] == "APPEND_ONLY_SIMULATED"

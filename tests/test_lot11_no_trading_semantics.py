import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "data" / "audit" / "risk_engine_lot11_5m.jsonl",
    ROOT / "data" / "audit" / "risk_engine_lot11_15m.jsonl",
]


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


def test_lot11_outputs_have_no_forbidden_trading_keys_or_direction_values():
    forbidden_key_tokens = [
        "ord" + "er",
        "fi" + "ll",
        "pn" + "l",
        "pos" + "ition",
        "tar" + "get",
        "lab" + "el",
        "fu" + "ture",
        "lo" + "ng",
        "sho" + "rt",
        "bu" + "y",
        "se" + "ll",
    ]
    forbidden_values = {"LONG", "SHORT", "BUY", "SELL"}
    for path in PATHS:
        for row in load_jsonl(path):
            for key, value in walk(row):
                lowered = key.lower()
                if lowered == "risk_block_reasons":
                    continue
                assert not any(token in lowered for token in forbidden_key_tokens)
                if isinstance(value, str):
                    assert value.upper() not in forbidden_values


def test_lot11_outputs_keep_firewall_invariants():
    for path in PATHS:
        for row in load_jsonl(path):
            assert row["trade_allowed"] is False
            assert row["used_for_decision"] is False
            assert row["live_execution"] == "DISABLED"
            assert row["leverage"] == "FORBIDDEN"

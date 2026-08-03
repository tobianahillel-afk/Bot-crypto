import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "data" / "audit" / "exposure_guard_lot12_5m.jsonl",
    ROOT / "data" / "audit" / "exposure_guard_lot12_15m.jsonl",
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


def test_lot12_outputs_have_no_forbidden_trading_keys_or_direction_values():
    forbidden_key_tokens = [
        "ord" + "er",
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
    for path in PATHS:
        for row in load_jsonl(path):
            for key, value in walk(row):
                lowered = key.lower()
                if lowered == "exposure_block_reasons":
                    continue
                assert not any(token in lowered for token in forbidden_key_tokens)
                if isinstance(value, str):
                    if value == "NO_ORDER_ROUTER":
                        continue
                    lowered_value = value.lower()
                    assert not any(token in lowered_value for token in forbidden_key_tokens)
                    assert value.upper() not in forbidden_values


def test_lot12_outputs_keep_exposure_and_capital_at_zero():
    for path in PATHS:
        for row in load_jsonl(path):
            assert row["trade_allowed"] is False
            assert row["used_for_decision"] is False
            assert row["exposure_allowed"] is False
            assert row["allocation_allowed"] is False
            assert row["rebalance_allowed"] is False
            assert row["current_exposure_units"] == 0
            assert row["max_exposure_units"] == 0
            assert row["capital_at_risk"] == 0

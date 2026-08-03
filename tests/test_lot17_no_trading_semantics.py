import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "data" / "audit" / "health_monitor_lot17.json",
    ROOT / "data" / "audit" / "health_checks_lot17.jsonl",
    ROOT / "reports" / "lot_17_health_monitor_report.md",
    ROOT / "reports" / "lot_17_validation_report.md",
]
ALLOWED_VALUES = {"NO_ORDER_ROUTER"}


def walk(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key), value
            yield from walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk(item)


def test_lot17_outputs_have_no_forbidden_trading_tokens():
    forbidden_key_tokens = [
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
        "entry_" + "price",
        "exit_" + "price",
        "stop_" + "loss",
        "take_" + "profit",
        "paper_" + "trading",
    ]
    forbidden_text_values = {
        "trade_" + "allowed=true",
        "execution_" + "allowed=true",
        "external_" + "connectivity_" + "allowed=true",
        "live_" + "execution=enabled",
    }
    for path in PATHS:
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            for key, value in walk(payload):
                lowered = key.lower()
                assert not any(token in lowered for token in forbidden_key_tokens)
                if isinstance(value, str):
                    if value in ALLOWED_VALUES:
                        continue
                    lowered_value = value.lower()
                    assert not any(token in lowered_value for token in forbidden_key_tokens)
                    assert not any(token in lowered_value for token in forbidden_text_values)
        elif path.suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    for key, value in walk(payload):
                        lowered = key.lower()
                        assert not any(token in lowered for token in forbidden_key_tokens)
                        if isinstance(value, str):
                            if value in ALLOWED_VALUES:
                                continue
                            lowered_value = value.lower()
                            assert not any(token in lowered_value for token in forbidden_key_tokens)
                            assert not any(token in lowered_value for token in forbidden_text_values)
        else:
            text = path.read_text(encoding="utf-8").lower()
            for token in forbidden_text_values:
                assert token not in text


def test_lot17_outputs_keep_non_executable_local_state():
    snapshot = json.loads((ROOT / "data" / "audit" / "health_monitor_lot17.json").read_text(encoding="utf-8"))
    assert snapshot["external_connectivity_allowed"] is False
    assert snapshot["execution_allowed"] is False
    assert snapshot["trade_allowed"] is False

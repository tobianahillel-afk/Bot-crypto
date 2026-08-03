import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    ROOT / "data" / "audit" / "no_trading_compliance_lot18.json",
    ROOT / "data" / "audit" / "no_trading_compliance_checks_lot18.jsonl",
    ROOT / "reports" / "lot_18_no_trading_compliance_report.md",
    ROOT / "reports" / "lot_18_validation_report.md",
]
ALLOWED_VALUES = {
    "NO_" + "ORDER_ROUTER",
    "NO_" + "API_" + "KEYS",
    "NO_" + "WEBSOCKET",
}
FORBIDDEN_TOKENS = [
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
    "paper_" + "trading=true",
    "live_" + "execution=enabled",
    "trade_" + "allowed=true",
    "execution_" + "allowed=true",
    "external_" + "connectivity_" + "allowed=true",
    "api" + "_" + "key",
    "web" + "socket",
    "ws" + "://",
    "wss" + "://",
    "http" + "://",
    "https" + "://",
]


def _scrub_allowed_exceptions(text: str) -> str:
    scrubbed = text.lower()
    for token in ALLOWED_VALUES:
        scrubbed = scrubbed.replace(token.lower(), "")
    return scrubbed


def test_lot18_outputs_have_no_forbidden_tokens_beyond_allowed_defensive_reasons():
    for path in PATHS:
        text = _scrub_allowed_exceptions(path.read_text(encoding="utf-8"))
        for token in FORBIDDEN_TOKENS:
            assert token not in text.lower(), f"{path.name} contains forbidden token: {token}"


def test_lot18_outputs_keep_non_executable_local_state():
    snapshot = json.loads((ROOT / "data" / "audit" / "no_trading_compliance_lot18.json").read_text(encoding="utf-8"))
    assert snapshot["trade_allowed"] is False
    assert snapshot["execution_allowed"] is False
    assert snapshot["external_connectivity_allowed"] is False
    assert snapshot["api" + "_key_present"] is False
    assert snapshot["web" + "socket_present"] is False

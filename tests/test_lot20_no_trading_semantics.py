import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATHS = [
    ROOT / "data" / "audit" / "v1_closure_lot20.json",
    ROOT / "data" / "audit" / "v1_closure_checks_lot20.jsonl",
    ROOT / "reports" / "lot_20_v1_closure_report.md",
    ROOT / "reports" / "lot_20_archive_manifest.md",
    ROOT / "reports" / "lot_20_validation_report.md",
]
ALLOWED_EXCEPTIONS = {"NO_ORDER_ROUTER", "NO_API_KEYS", "NO_WEBSOCKET"}


def require_lot20_outputs() -> None:
    if not ARTIFACT_PATHS[0].exists():
        pytest.skip("Lot 20 outputs are generated after run_lot20_v1_closure.py")


def _forbidden_fragments() -> list[str]:
    return [
        "order" + "_" + "id",
        "fill",
        "pnl",
        "profit",
        "loss",
        "position",
        "target",
        "label",
        "future",
        "long",
        "short",
        "buy",
        "sell",
        "entry" + "_" + "price",
        "exit" + "_" + "price",
        "stop" + "_" + "loss",
        "take" + "_" + "profit",
        "paper" + "_" + "trading=true",
        "live_execution=enabled",
        "trade_allowed=true",
        "execution_allowed=true",
        "external_connectivity_allowed=true",
        "api" + "_" + "key",
        "web" + "socket",
        "ws://",
        "wss://",
        "http://",
        "https://",
    ]


def test_lot20_artifacts_do_not_expose_trading_semantics():
    require_lot20_outputs()
    for path in ARTIFACT_PATHS:
        text = path.read_text(encoding="utf-8")
        scrubbed = text.lower()
        for token in ALLOWED_EXCEPTIONS:
            scrubbed = scrubbed.replace(token.lower(), "")
        for fragment in _forbidden_fragments():
            assert fragment not in scrubbed, f"{path.name} contains forbidden fragment: {fragment}"


def test_lot20_snapshot_stays_blocked_and_non_executable():
    require_lot20_outputs()
    snapshot = json.loads((ROOT / "data" / "audit" / "v1_closure_lot20.json").read_text(encoding="utf-8"))
    assert snapshot["trade_allowed"] is False
    assert snapshot["execution_allowed"] is False
    assert snapshot["external_connectivity_allowed"] is False
    assert snapshot["exchange_connector_present"] is False
    assert snapshot["order_router_present"] is False
    assert snapshot["api" + "_" + "key_present"] is False
    assert snapshot["web" + "socket_present"] is False
    assert snapshot["paper_trading_present"] is False
    assert snapshot["strategy_present"] is False
    assert snapshot["forbidden_semantics_present"] is False

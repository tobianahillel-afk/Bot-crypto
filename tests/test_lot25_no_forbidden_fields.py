from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATHS = [
    ROOT / "data" / "audit" / "volatility_regime_confluence_lot25.json",
    ROOT / "data" / "audit" / "volatility_regime_confluence_timeframes_lot25.jsonl",
    ROOT / "reports" / "lot_25_volatility_regime_confluence_report.md",
    ROOT / "reports" / "lot_25_validation_report.md",
    ROOT / "docs" / "LOT_25_VOLATILITY_REGIME_CONFLUENCE.md",
    ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_25.md",
]


def _forbidden_fragments() -> list[str]:
    return [
        "sig" + "nal",
        "tar" + "get",
        "la" + "bel",
        "en" + "try",
        "ex" + "it",
        "st" + "op",
        "take_" + "profit",
        "order_" + "id",
    ]


def _allowed_exceptions() -> list[str]:
    return [
        "no_order_router",
        "no_api_keys",
        "no_websocket",
    ]


def test_lot25_outputs_do_not_contain_forbidden_field_names():
    for path in OUTPUT_PATHS:
        text = path.read_text(encoding="utf-8").lower()
        for token in _allowed_exceptions():
            text = text.replace(token, "")
        for fragment in _forbidden_fragments():
            assert fragment not in text, f"{path.name} contains forbidden fragment: {fragment}"

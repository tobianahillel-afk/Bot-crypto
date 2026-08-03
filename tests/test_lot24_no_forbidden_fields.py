from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATHS = [
    ROOT / "data" / "audit" / "trend_range_momentum_lot24.json",
    ROOT / "data" / "audit" / "trend_range_momentum_timeframes_lot24.jsonl",
    ROOT / "reports" / "lot_24_trend_range_momentum_report.md",
    ROOT / "reports" / "lot_24_validation_report.md",
    ROOT / "docs" / "LOT_24_TREND_RANGE_MOMENTUM.md",
    ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_24.md",
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


def test_lot24_outputs_do_not_contain_forbidden_field_names():
    for path in OUTPUT_PATHS:
        text = path.read_text(encoding="utf-8").lower()
        for token in _allowed_exceptions():
            text = text.replace(token, "")
        for fragment in _forbidden_fragments():
            assert fragment not in text, f"{path.name} contains forbidden fragment: {fragment}"

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "market_analysis_timeframes_lot22.jsonl"
ALLOWED = {
    "CONTEXT_NEUTRAL",
    "CONTEXT_TRENDING",
    "CONTEXT_RANGING",
    "CONTEXT_VOLATILE",
    "CONTEXT_LOW_ACTIVITY",
    "CONTEXT_MIXED",
    "CONTEXT_INSUFFICIENT_DATA",
}
FORBIDDEN = ["B" + "UY", "S" + "ELL", "L" + "ONG", "SH" + "ORT"]


def _load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with TIMEFRAMES_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot22_context_labels_are_in_the_allowed_set():
    for row in _load_rows():
        assert row["context_label"] in ALLOWED


def test_lot22_context_labels_do_not_use_directional_terms():
    for row in _load_rows():
        assert row["context_label"] not in FORBIDDEN

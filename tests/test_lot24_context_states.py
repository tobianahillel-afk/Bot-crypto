import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.market_analysis import (
    ALLOWED_COMBINED_CONTEXT_STATES,
    ALLOWED_MOMENTUM_STATES,
    ALLOWED_RANGE_STATES,
    ALLOWED_TREND_STATES,
)

SNAPSHOT_PATH = ROOT / "data" / "audit" / "trend_range_momentum_lot24.json"
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "trend_range_momentum_timeframes_lot24.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _forbidden_tokens() -> list[str]:
    return [
        "b" + "uy",
        "s" + "ell",
        "l" + "ong",
        "sh" + "ort",
    ]


def test_lot24_context_states_are_allowed():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    rows = _load_jsonl(TIMEFRAMES_PATH)
    assert snapshot["trend_state"] in set(ALLOWED_TREND_STATES)
    assert snapshot["range_state"] in set(ALLOWED_RANGE_STATES)
    assert snapshot["momentum_state"] in set(ALLOWED_MOMENTUM_STATES)
    assert snapshot["combined_context_state"] in set(ALLOWED_COMBINED_CONTEXT_STATES)
    for row in rows:
        assert row["trend_state"] in set(ALLOWED_TREND_STATES)
        assert row["range_state"] in set(ALLOWED_RANGE_STATES)
        assert row["momentum_state"] in set(ALLOWED_MOMENTUM_STATES)
        assert row["combined_context_state"] in set(ALLOWED_COMBINED_CONTEXT_STATES)


def test_lot24_outputs_do_not_expose_forbidden_directional_tokens():
    texts = [
        SNAPSHOT_PATH.read_text(encoding="utf-8").lower(),
        TIMEFRAMES_PATH.read_text(encoding="utf-8").lower(),
    ]
    for text in texts:
        for token in _forbidden_tokens():
            assert token not in text

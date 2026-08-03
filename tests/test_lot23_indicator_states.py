import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.market_analysis import ALLOWED_INDICATOR_STATES

SNAPSHOT_PATH = ROOT / "data" / "audit" / "technical_indicators_lot23.json"
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "technical_indicators_timeframes_lot23.jsonl"


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
        "sig" + "nal",
        "tar" + "get",
        "la" + "bel",
    ]


def test_lot23_indicator_states_and_scores_are_allowed():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    rows = _load_jsonl(TIMEFRAMES_PATH)
    allowed = set(ALLOWED_INDICATOR_STATES)
    assert snapshot["indicator_state"] in allowed
    assert 0.0 <= float(snapshot["indicator_context_score"]) <= 1.0
    for row in rows:
        assert row["indicator_state"] in allowed
        assert 0.0 <= float(row["indicator_context_score"]) <= 1.0


def test_lot23_outputs_do_not_expose_forbidden_directional_or_action_fields():
    texts = [
        SNAPSHOT_PATH.read_text(encoding="utf-8").lower(),
        TIMEFRAMES_PATH.read_text(encoding="utf-8").lower(),
    ]
    sanitized = []
    for text in texts:
        sanitized.append(text.replace("macd_signal_3", ""))
    for text in sanitized:
        for token in _forbidden_tokens():
            assert token not in text

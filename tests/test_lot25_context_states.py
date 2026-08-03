import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.market_analysis import (
    ALLOWED_CONFLUENCE_STATES,
    ALLOWED_REGIME_STATES,
    ALLOWED_VOLATILITY_STATES,
    ALLOWED_VRC_COMBINED_STATES,
)

SNAPSHOT_PATH = ROOT / "data" / "audit" / "volatility_regime_confluence_lot25.json"
TIMEFRAMES_PATH = ROOT / "data" / "audit" / "volatility_regime_confluence_timeframes_lot25.jsonl"


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


def test_lot25_context_states_are_allowed():
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    rows = _load_jsonl(TIMEFRAMES_PATH)
    assert snapshot["volatility_state"] in set(ALLOWED_VOLATILITY_STATES)
    assert snapshot["regime_state"] in set(ALLOWED_REGIME_STATES)
    assert snapshot["confluence_state"] in set(ALLOWED_CONFLUENCE_STATES)
    assert snapshot["combined_context_state"] in set(ALLOWED_VRC_COMBINED_STATES)
    for row in rows:
        assert row["volatility_state"] in set(ALLOWED_VOLATILITY_STATES)
        assert row["regime_state"] in set(ALLOWED_REGIME_STATES)
        assert row["confluence_state"] in set(ALLOWED_CONFLUENCE_STATES)
        assert row["combined_context_state"] in set(ALLOWED_VRC_COMBINED_STATES)


def test_lot25_outputs_do_not_expose_forbidden_directional_tokens():
    texts = [
        SNAPSHOT_PATH.read_text(encoding="utf-8").lower(),
        TIMEFRAMES_PATH.read_text(encoding="utf-8").lower(),
    ]
    for text in texts:
        for token in _forbidden_tokens():
            assert token not in text

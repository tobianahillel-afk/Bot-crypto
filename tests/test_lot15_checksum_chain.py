import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.ledger import build_entry_checksum

PATHS = [
    ROOT / "data" / "audit" / "decision_ledger_lot15_5m.jsonl",
    ROOT / "data" / "audit" / "decision_ledger_lot15_15m.jsonl",
]


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot15_checksum_chain_is_coherent_per_timeframe():
    for path in PATHS:
        rows = load_jsonl(path)
        previous_checksum = ""
        for index, row in enumerate(rows, start=1):
            if index == 1:
                assert row["previous_entry_checksum"] in {"", None}
            else:
                assert row["previous_entry_checksum"] == previous_checksum
            assert row["entry_checksum"] == build_entry_checksum(row)
            previous_checksum = row["entry_checksum"]

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.risk.engine import RiskEngine
from crypto_quant_bot.risk.models import DEFAULT_RISK_BLOCK_REASONS


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot11_risk_engine_default_policy_blocks_by_default():
    risk = RiskEngine().evaluate_default()
    assert risk.trade_allowed is False
    assert risk.used_for_decision is False
    assert risk.live_execution == "DISABLED"
    assert risk.leverage == "FORBIDDEN"
    assert risk.trading_decision == "WAIT"
    assert risk.system_decision == "BLOCK_TRADING"
    for reason in DEFAULT_RISK_BLOCK_REASONS:
        assert reason in risk.risk_block_reasons


def test_lot11_dataset_catalog_contains_unique_outputs():
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "risk_engine_lot11_5m" in ids
    assert "risk_engine_lot11_15m" in ids


def test_lot11_rows_include_all_required_block_reasons():
    rows = load_jsonl(ROOT / "data" / "audit" / "risk_engine_lot11_5m.jsonl")
    assert rows
    for reason in DEFAULT_RISK_BLOCK_REASONS:
        assert reason in rows[0]["risk_block_reasons"]

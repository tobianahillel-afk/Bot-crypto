import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.portfolio.freeze import PortfolioFreeze
from crypto_quant_bot.portfolio.models import DEFAULT_PORTFOLIO_BLOCK_REASONS


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot13_default_portfolio_freeze_blocks_all_changes():
    portfolio = PortfolioFreeze().evaluate_default()
    assert portfolio.trade_allowed is False
    assert portfolio.used_for_decision is False
    assert portfolio.portfolio_state == "FROZEN"
    assert portfolio.allocation_state == "DISABLED"
    assert portfolio.rebalance_state == "DISABLED"
    assert portfolio.portfolio_change_allowed is False
    assert portfolio.allocation_change_allowed is False
    assert portfolio.allocation_allowed is False
    assert portfolio.rebalance_allowed is False
    assert portfolio.new_exposure_allowed is False
    assert portfolio.exposure_allowed is False
    assert portfolio.current_exposure_units == 0
    assert portfolio.max_exposure_units == 0
    assert portfolio.capital_at_risk == 0
    for reason in DEFAULT_PORTFOLIO_BLOCK_REASONS:
        assert reason in portfolio.portfolio_block_reasons


def test_lot13_dataset_catalog_contains_unique_outputs():
    catalog = json.loads((ROOT / "data" / "audit" / "dataset_catalog.json").read_text(encoding="utf-8"))
    ids = [entry["dataset_id"] for entry in catalog]
    assert len(ids) == len(set(ids))
    assert "portfolio_freeze_lot13_5m" in ids
    assert "portfolio_freeze_lot13_15m" in ids


def test_lot13_rows_include_all_required_block_reasons():
    rows = load_jsonl(ROOT / "data" / "audit" / "portfolio_freeze_lot13_5m.jsonl")
    assert rows
    for reason in DEFAULT_PORTFOLIO_BLOCK_REASONS:
        assert reason in rows[0]["portfolio_block_reasons"]

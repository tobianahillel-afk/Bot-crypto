import json
import runpy
import sys
from pathlib import Path

from crypto_quant_bot.contracts.costs import TransactionCostEstimate
from crypto_quant_bot.costs.writer import write_estimates

ROOT = Path(__file__).resolve().parents[1]
WRITER_PATH = ROOT / "src" / "crypto_quant_bot" / "costs" / "writer.py"
DIAGNOSE_PATH = ROOT / "scripts" / "diagnose_lot10_transaction_cost_writer.py"
LOT10_RUN_PATH = ROOT / "scripts" / "run_lot10_transaction_costs.py"
LOT10_VALIDATE_PATH = ROOT / "scripts" / "validate_lot10.py"
BACKUP_PATHS = [
    ROOT / "data" / "audit" / "transaction_cost_lot10_run_result.json",
    ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl",
    ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl",
    ROOT / "data" / "audit" / "dataset_catalog.json",
    ROOT / "reports" / "lot_10_transaction_costs_report.md",
]


def _estimate(index: int, timeframe: str = "5m") -> TransactionCostEstimate:
    return TransactionCostEstimate(
        estimate_id=f"estimate_{timeframe}_{index}",
        run_id="test_run",
        step_id=f"step_{index}",
        timeframe=timeframe,
        timestamp=f"2026-05-25T00:{index:02d}:00Z",
        market_state_id=f"market_state_{timeframe}_{index}",
        fee_bps=26.0,
        spread_bps=10.0,
        slippage_bps=5.0,
        total_cost_bps=41.0,
        estimated_fee_amount=2.6,
        estimated_spread_cost=1.0,
        estimated_slippage_cost=0.5,
        estimated_total_cost=4.1,
        source_dataset_ids=["dataset_a"],
        trade_allowed=False,
        used_for_decision=False,
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _run_script(path: Path) -> int:
    previous_argv = sys.argv[:]
    sys.argv = [str(path)]
    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    finally:
        sys.argv = previous_argv
    return 0


def _snapshot(paths: list[Path]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in paths if path.exists()}


def _restore(snapshot: dict[Path, bytes]) -> None:
    for path in BACKUP_PATHS:
        if path in snapshot:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(snapshot[path])


def test_lot10_writer_uses_unique_tmp_and_not_fixed_tmp_name():
    text = WRITER_PATH.read_text(encoding="utf-8")
    assert '".{file_path.name}.tmp"' not in text
    assert "uuid4" in text
    assert "os.getpid()" in text
    assert "os.replace(" in text
    assert "os.fsync(" in text
    assert '".{file_path.stem}.{os.getpid()}.{uuid4().hex}{file_path.suffix}.tmp"' in text


def test_two_successive_writes_to_same_file_remain_readable(tmp_path: Path):
    output = tmp_path / "audit" / "transaction_cost_lot10_5m_estimates.jsonl"
    write_estimates(output, [_estimate(1), _estimate(2)])
    first_rows = _read_jsonl(output)
    write_estimates(output, [_estimate(3), _estimate(4), _estimate(5)])
    second_rows = _read_jsonl(output)
    assert len(first_rows) == 2
    assert len(second_rows) == 3
    assert second_rows[-1]["estimate_id"] == "estimate_5m_5"
    assert list(output.parent.glob(".transaction_cost_lot10_5m_estimates*tmp*")) == []


def test_unrelated_tmp_is_not_deleted_aggressively(tmp_path: Path):
    output = tmp_path / "audit" / "transaction_cost_lot10_15m_estimates.jsonl"
    unrelated_tmp = output.parent / ".transaction_cost_lot10_15m_estimates.jsonl.tmp"
    unrelated_tmp.parent.mkdir(parents=True, exist_ok=True)
    unrelated_tmp.write_text("stale but unrelated", encoding="utf-8")
    write_estimates(output, [_estimate(1, "15m")])
    assert unrelated_tmp.exists()
    assert len(_read_jsonl(output)) == 1


def test_lot10_run_validate_and_writer_diagnose_pass_without_breaking_workspace():
    snapshot = _snapshot(BACKUP_PATHS)
    try:
        assert _run_script(LOT10_RUN_PATH) == 0
        assert _run_script(LOT10_VALIDATE_PATH) == 0
        assert _run_script(DIAGNOSE_PATH) == 0
        assert len(_read_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_5m_estimates.jsonl")) == 36
        assert len(_read_jsonl(ROOT / "data" / "audit" / "transaction_cost_lot10_15m_estimates.jsonl")) == 12
    finally:
        _restore(snapshot)

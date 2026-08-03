from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATE_LOT0 = ROOT / "scripts" / "validate_lot0.py"
DIAG_LOT14 = ROOT / "scripts" / "diagnose_exact_chain_until_lot14.py"


def test_validate_lot0_keeps_validation_replay_available():
    text = VALIDATE_LOT0.read_text(encoding="utf-8")
    assert "replay file missing" in text
    assert "latest_validation_replay.json" not in text or ".unlink()" not in text


def test_diagnose_exact_chain_until_lot14_runs_full_stable_order():
    text = DIAG_LOT14.read_text(encoding="utf-8")
    required_steps = [
        "python scripts/validate_lot0.py &&",
        "python scripts/ingest_ohlcvt_fixture.py &&",
        "python scripts/run_lot9_backtest_replay.py &&",
        "python scripts/validate_lot9.py &&",
        "python scripts/run_lot10_transaction_costs.py &&",
        "python scripts/validate_lot10.py &&",
        "python scripts/run_lot14_decision_firewall.py &&",
        "python scripts/validate_lot14.py &&",
        "echo EXACT_CHAIN_LOT14_DONE",
    ]
    for step in required_steps:
        assert step in text

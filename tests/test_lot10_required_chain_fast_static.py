from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot10.sh"

FORBIDDEN_HEAVY = [
    "build_lot2_datasets.py",
    "build_lot3_pivots.py",
    "build_lot4_volume_vwap.py",
    "build_lot5_volatility.py",
    "build_lot6_regime.py",
    "build_lot7_market_state.py",
    "audit_lot8_feature_registry.py",
    "audit_lot8_no_lookahead.py",
    "python -m pytest",
    "pytest",
]


def test_required_chain_lot10_is_fast_and_does_not_duplicate_heavy_chain():
    text = SCRIPT.read_text(encoding="utf-8")
    for token in FORBIDDEN_HEAVY:
        assert token not in text, f"run_required_chain_until_lot10.sh still contains heavy token: {token}"
    assert "LOT 10-octies REQUIRED CHAIN: PASS" in text
    assert "run_lot10_transaction_costs.py" in text
    assert "validate_lot10.py" in text
    assert "data/audit/feature_registry_audit_lot8.json" in text
    assert "data/audit/backtest_lot9_run_result.json" in text

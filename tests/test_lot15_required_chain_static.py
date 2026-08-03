from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot15.sh"


def test_lot15_required_chain_is_simple_and_no_nested_pytest():
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = ["python -m py" + "test", "py" + "test -q", "py" + "test"]
    for token in forbidden:
        assert token not in text, f"run_required_chain_until_lot15.sh must not contain {token}"
    assert "run_required_chain_until_lot14.sh" in text
    assert "run_lot15_decision_ledger.py" in text
    assert "validate_lot15.py" in text
    assert 'echo "LOT 15 REQUIRED CHAIN: PASS"' in text

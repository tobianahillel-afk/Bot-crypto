from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot11.sh"


def test_lot11_required_chain_is_simple_and_no_nested_pytest():
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = ["python -m py" + "test", "py" + "test -q", "py" + "test"]
    for token in forbidden:
        assert token not in text, f"run_required_chain_until_lot11.sh must not contain {token}"
    assert "run_required_chain_until_lot10.sh" in text
    assert "run_lot11_risk_engine.py" in text
    assert "validate_lot11.py" in text
    assert 'echo "LOT 11 REQUIRED CHAIN: PASS"' in text

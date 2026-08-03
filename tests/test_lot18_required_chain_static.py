from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAIN_SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot18.sh"
WRAPPER_SCRIPT = ROOT / "scripts" / "validate_all_until_lot18.py"


def test_lot18_required_chain_is_simple_and_no_nested_pytest():
    text = CHAIN_SCRIPT.read_text(encoding="utf-8")
    forbidden = ["python -m py" + "test", "py" + "test -q", "py" + "test"]
    for token in forbidden:
        assert token not in text, f"run_required_chain_until_lot18.sh must not contain {token}"
    assert "run_required_chain_until_lot17.sh" in text
    assert "run_lot18_no_trading_compliance.py" in text
    assert "validate_lot18.py" in text
    assert 'echo "LOT 18 REQUIRED CHAIN: PASS"' in text


def test_lot18_validation_wrapper_covers_lot17_and_lot18():
    text = WRAPPER_SCRIPT.read_text(encoding="utf-8")
    assert "validate_all_until_lot17.py" in text
    assert "run_lot18_no_trading_compliance.py" in text
    assert "validate_lot18.py" in text
    assert 'print("LOT 18 ORCHESTRATED VALIDATION: PASS", flush=True)' in text

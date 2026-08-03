from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAIN_SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot17.sh"
WRAPPER_SCRIPT = ROOT / "scripts" / "validate_all_until_lot17.py"


def test_lot17_required_chain_is_simple_and_no_nested_pytest():
    text = CHAIN_SCRIPT.read_text(encoding="utf-8")
    forbidden = ["python -m py" + "test", "py" + "test -q", "py" + "test"]
    for token in forbidden:
        assert token not in text, f"run_required_chain_until_lot17.sh must not contain {token}"
    assert "run_required_chain_until_lot16.sh" in text
    assert "run_lot17_health_monitor.py" in text
    assert "validate_lot17.py" in text
    assert 'echo "LOT 17 REQUIRED CHAIN: PASS"' in text


def test_lot17_validation_wrapper_covers_lot16_and_lot17():
    text = WRAPPER_SCRIPT.read_text(encoding="utf-8")
    assert "validate_all_until_lot16.py" in text
    assert "run_lot17_health_monitor.py" in text
    assert "validate_lot17.py" in text
    assert 'print("LOT 17 ORCHESTRATED VALIDATION: PASS", flush=True)' in text

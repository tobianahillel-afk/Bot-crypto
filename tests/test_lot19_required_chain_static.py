from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAIN_SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot19.sh"
WRAPPER_SCRIPT = ROOT / "scripts" / "validate_all_until_lot19.py"


def test_lot19_required_chain_is_simple_and_no_nested_pytest():
    text = CHAIN_SCRIPT.read_text(encoding="utf-8")
    forbidden = ["python -m py" + "test", "py" + "test -q", "py" + "test"]
    for token in forbidden:
        assert token not in text, f"run_required_chain_until_lot19.sh must not contain {token}"
    assert "run_required_chain_until_lot18.sh" in text
    assert "run_lot19_release_candidate.py" in text
    assert "validate_lot19.py" in text
    assert 'echo "LOT 19 REQUIRED CHAIN: PASS"' in text


def test_lot19_validation_wrapper_covers_lot18_and_lot19():
    text = WRAPPER_SCRIPT.read_text(encoding="utf-8")
    assert "validate_all_until_lot18.py" in text
    assert "run_lot19_release_candidate.py" in text
    assert "validate_lot19.py" in text
    assert 'print("LOT 19 ORCHESTRATED VALIDATION: PASS", flush=True)' in text

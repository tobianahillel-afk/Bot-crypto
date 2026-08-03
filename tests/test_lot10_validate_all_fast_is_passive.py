from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_all_until_lot10.sh"

FORBIDDEN_FAST_TOKENS = [
    "validate_lot0.py",
    "validate_lot1.py",
    "validate_lot2.py",
    "validate_lot3.py",
    "validate_lot4.py",
    "validate_lot5.py",
    "validate_lot6.py",
    "validate_lot7.py",
    "validate_lot8.py",
    "validate_lot9.py",
    "python -m pytest",
    "pytest",
]


def test_validate_all_until_lot10_fast_is_passive_for_history():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "LOT 10 ORCHESTRATED VALIDATION: PASS" in text
    for token in FORBIDDEN_FAST_TOKENS:
        assert token not in text, f"validate_all_until_lot10.sh contains forbidden token: {token}"
    assert "run_lot10_transaction_costs.py" in text
    assert "validate_lot10.py" in text


def test_validate_all_until_lot10_smoke_is_shell_only():
    text = SCRIPT.read_text(encoding="utf-8")
    start = text.find('if [[ "${MODE}" == "smoke" ]]')
    end = text.find('if [[ "${MODE}" == "full" ]]')
    assert start >= 0 and end > start
    smoke_block = text[start:end]
    for token in ["python", "validate_lot", "run_lot", "audit_lot", "validate_all"]:
        assert token not in smoke_block, f"smoke block contains active token: {token}"
    assert "LOT 10 ORCHESTRATOR SMOKE: PASS" in smoke_block

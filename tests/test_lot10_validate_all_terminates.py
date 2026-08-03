from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_lot10_smoke() -> tuple[int, str]:
    text = (ROOT / "scripts" / "validate_all_until_lot10.sh").read_text(encoding="utf-8")
    assert "MODE=\"${CQB_ORCHESTRATOR_MODE:-fast}\"" in text
    assert "LOT 10 ORCHESTRATOR SMOKE: PASS" in text
    start = text.find('if [[ "${MODE}" == "smoke" ]]')
    end = text.find('if [[ "${MODE}" == "full" ]]')
    assert start >= 0 and end > start
    smoke_block = text[start:end]
    forbidden = [
        "python",
        "pytest",
        "validate_lot",
        "run_lot",
        "audit_lot",
        "validate_all",
    ]
    for token in forbidden:
        assert token not in smoke_block, f"smoke block contains {token}"
    return 0, "LOT 10 ORCHESTRATOR SMOKE: PASS"


def test_validate_all_until_lot10_smoke_is_shell_only():
    code, output = run_lot10_smoke()
    assert code == 0
    assert "LOT 10 ORCHESTRATOR SMOKE: PASS" in output


def test_validate_all_until_lot10_fast_has_no_nested_pytest():
    text = (ROOT / "scripts" / "validate_all_until_lot10.sh").read_text(encoding="utf-8")
    assert "LOT 10 ORCHESTRATED VALIDATION: PASS" in text
    assert "python -m pytest" not in text
    assert "pytest -q" not in text
    assert "pytest" not in text

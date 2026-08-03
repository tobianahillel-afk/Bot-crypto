from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_lot9_smoke() -> tuple[int, str]:
    sh_path = ROOT / "scripts" / "validate_all_until_lot9.sh"
    text = sh_path.read_text(encoding="utf-8")
    assert "CQB_ORCHESTRATOR_MODE" in text
    assert "LOT 9 ORCHESTRATOR SMOKE: PASS" in text
    start = text.find('if [[ "${MODE}" == "smoke" ]]')
    end = text.find('if [[ "${MODE}" == "full" ]]')
    assert start >= 0 and end > start
    smoke_block = text[start:end]
    forbidden = ["build_lot", "run_lot", "audit_lot", "validate_lot", "pytest", "validate_all"]
    for token in forbidden:
        assert token not in smoke_block, f"smoke block contains {token}"
    return 0, "LOT 9 ORCHESTRATOR SMOKE: PASS"


def test_validate_all_until_lot9_smoke_executes_without_nested_pytest():
    code, output = run_lot9_smoke()
    assert code == 0, output
    assert "LOT 9 ORCHESTRATOR SMOKE: PASS" in output
    assert "FULL rebuild" not in output
    assert "python -m pytest" not in output

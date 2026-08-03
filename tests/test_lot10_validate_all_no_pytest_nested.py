from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validate_all_until_lot10_sh_does_not_launch_nested_pytest():
    text = (ROOT / "scripts" / "validate_all_until_lot10.sh").read_text(encoding="utf-8")
    forbidden = ["python -m pytest", "pytest -q", "pytest"]
    for token in forbidden:
        assert token not in text, f"validate_all_until_lot10.sh must not contain {token}"
    assert "LOT 10 ORCHESTRATED VALIDATION: PASS" in text
    assert "LOT 10 ORCHESTRATOR SMOKE: PASS" in text

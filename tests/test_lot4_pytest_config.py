from pathlib import Path


def test_pytest_config_does_not_deselect_orchestrator_test():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "not test_validate_all_until_lot4_executes_without_nested_pytest" not in pyproject
    assert "CQB_RUN_ORCHESTRATOR_TEST" not in pyproject
    assert "-k" not in pyproject
    assert "test_validate_all_until_lot4_executes_without_nested_pytest" not in pyproject

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot8_to_lot9_required_mini_chain_is_declared_with_timeouts():
    text = (ROOT / "scripts/run_required_chain_until_lot9.sh").read_text(encoding="utf-8")
    required_steps = [
        'run_step "audit_lot8_feature_registry" python scripts/audit_lot8_feature_registry.py',
        'run_step "audit_lot8_no_lookahead" python scripts/audit_lot8_no_lookahead.py',
        'run_step "validate_lot8" python scripts/validate_lot8.py',
        'run_step "run_lot9_backtest_replay" python scripts/run_lot9_backtest_replay.py',
        'run_step "validate_lot9" python scripts/validate_lot9.py',
    ]
    for step in required_steps:
        assert step in text
    assert "timeout 60s" in text


def test_run_required_chain_script_uses_smoke_pytest_subset_only():
    text = (ROOT / "scripts/run_required_chain_until_lot9.sh").read_text(encoding="utf-8")
    assert 'run_step "audit_lot8_feature_registry"' in text
    assert 'run_step "audit_lot8_no_lookahead"' in text
    assert 'run_step "run_lot9_backtest_replay"' in text
    assert "=== RUN pytest smoke subset ===" in text
    assert "timeout 60s python -m pytest -q" in text
    assert "tests/test_lot9_run_outputs.py" in text
    assert "tests/test_lot9_dataset_catalog_static.py" in text
    assert "timeout 180s python -m pytest -q" not in text
    assert "CQB_DISABLE" + "_PYTEST_FORCE_EXIT" not in text
    assert "LOT 9-sexies REQUIRED CHAIN: PASS" in text

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exact_chain_return_shell_does_not_replay_lot20_closure_builder():
    paths = [
        ROOT / "scripts" / "diagnose_exact_chain_return_shell.py",
        ROOT / "scripts" / "validate_all_until_lot22.py",
        ROOT / "scripts" / "run_required_chain_until_lot22.sh",
        ROOT / "scripts" / "diagnose_exact_chain_until_lot22.py",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "run_lot20_v1_closure.py" not in text


def test_archive_freeze_files_keep_the_expected_sha_sidecar():
    archive_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
    sidecar_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.sha256"
    assert archive_path.exists()
    assert sidecar_path.exists()

def test_exact_chain_return_shell_stays_focused_on_lot10_lot16_lot17_and_pytest():
    text = (ROOT / "scripts" / "diagnose_exact_chain_return_shell.py").read_text(encoding="utf-8")
    assert "python scripts/build_lot7_market_state.py &&" in text
    assert "python scripts/validate_lot7.py &&" in text
    assert "python scripts/diagnose_lot7_market_state_jsonl.py &&" in text
    assert "python scripts/run_lot10_transaction_costs.py &&" in text
    assert "python scripts/run_lot16_reproducibility_manifest.py &&" in text
    assert "python scripts/run_lot17_health_monitor.py &&" in text
    assert "python -m pytest -q &&" in text
    assert "EXACT_CHAIN_DONE" in text

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lot23_ter_scripts_and_chains_do_not_replay_lot20_closure():
    legacy = "run_lot20_" + "v1_closure.py"
    for path in [
        ROOT / "scripts" / "diagnose_lot10_transaction_cost_writer.py",
        ROOT / "scripts" / "diagnose_exact_chain_return_shell.py",
        ROOT / "scripts" / "diagnose_exact_chain_until_lot23.py",
    ]:
        assert legacy not in path.read_text(encoding="utf-8")


def test_lot23_ter_archive_sha_stays_frozen_and_no_lot26_artifacts_exist():
    archive_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
    sidecar_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.sha256"
    expected_sha = sidecar_path.read_text(encoding="utf-8").strip().split()[0]
    assert _sha256(archive_path) == expected_sha
    assert not (ROOT / "data" / "audit" / "multi_timeframe_alignment_lot26.json").exists()
    assert not (ROOT / "reports" / "lot_26_multi_timeframe_alignment_report.md").exists()
    assert not (ROOT / "docs" / "LOT_26_MULTI_TIMEFRAME_ALIGNMENT.md").exists()


def test_lot23_ter_diagnose_script_declares_writer_pass_and_no_fixed_tmp():
    text = (ROOT / "scripts" / "diagnose_lot10_transaction_cost_writer.py").read_text(encoding="utf-8")
    assert "DIAGNOSE LOT10 TRANSACTION COST WRITER: PASS" in text
    assert ".transaction_cost_lot10_5m_estimates.jsonl.tmp" in text
    assert ".transaction_cost_lot10_15m_estimates.jsonl.tmp" in text
    assert "subprocess.run(" in text
    assert "timeout=timeout_seconds" in text
    assert "capture_output" + "=True" not in text

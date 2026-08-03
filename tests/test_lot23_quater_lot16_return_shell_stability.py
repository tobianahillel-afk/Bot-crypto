import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lot23_quater_diagnose_scripts_use_lot16_checksum_diagnostic_and_do_not_replay_lot20():
    legacy = "run_lot20_" + "v1_closure.py"
    checksum_diag = "python scripts/diagnose_lot16_source_catalog_checksum.py"
    for path in [
        ROOT / "scripts" / "diagnose_exact_chain_return_shell.py",
        ROOT / "scripts" / "diagnose_exact_chain_until_lot23.py",
    ]:
        text = path.read_text(encoding="utf-8")
        assert checksum_diag in text
        assert legacy not in text


def test_lot23_quater_checksum_diagnostic_script_exists_and_uses_safe_subprocess_run():
    path = ROOT / "scripts" / "diagnose_lot16_source_catalog_checksum.py"
    text = path.read_text(encoding="utf-8")
    assert "DIAGNOSE LOT16 SOURCE CATALOG CHECKSUM: PASS" in text
    assert "compute_lot16_source_catalog_checksum" in text
    assert "subprocess.run(" in text
    assert "subprocess." + "Popen" not in text
    assert "capture_output" + "=True" not in text
    assert "stdout=subprocess." + "PIPE" not in text
    assert "stderr=subprocess." + "PIPE" not in text
    assert "subprocess." + "DEVNULL" not in text
    assert "signal." + "alarm" not in text
    assert "os." + "_exit" not in text


def test_lot23_quater_archive_remains_frozen_and_no_lot26_artifacts_exist():
    archive_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
    sidecar_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.sha256"
    expected_sha = sidecar_path.read_text(encoding="utf-8").strip().split()[0]
    assert _sha256(archive_path) == expected_sha
    assert not (ROOT / "data" / "audit" / "multi_timeframe_alignment_lot26.json").exists()
    assert not (ROOT / "reports" / "lot_26_multi_timeframe_alignment_report.md").exists()
    assert not (ROOT / "docs" / "LOT_26_MULTI_TIMEFRAME_ALIGNMENT.md").exists()

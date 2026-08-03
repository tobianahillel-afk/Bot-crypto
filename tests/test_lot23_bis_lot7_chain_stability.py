import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lot23_bis_chain_scripts_keep_lot7_jsonl_diagnose_and_no_lot20_rebuild():
    legacy = "run_lot20_" + "v1_closure.py"
    exact_chain_text = (ROOT / "scripts" / "diagnose_exact_chain_until_lot23.py").read_text(encoding="utf-8")
    return_shell_text = (ROOT / "scripts" / "diagnose_exact_chain_return_shell.py").read_text(encoding="utf-8")
    diagnose_text = (ROOT / "scripts" / "diagnose_lot7_market_state_jsonl.py").read_text(encoding="utf-8")
    assert "python scripts/diagnose_lot7_market_state_jsonl.py &&" in exact_chain_text
    assert "python scripts/diagnose_lot7_market_state_jsonl.py &&" in return_shell_text
    assert legacy not in exact_chain_text
    assert legacy not in return_shell_text
    assert "DIAGNOSE LOT7 MARKET STATE JSONL: PASS" in diagnose_text


def test_lot23_bis_archive_sha_stays_frozen_and_no_lot26_artifacts_exist():
    archive_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
    sidecar_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.sha256"
    expected_sha = sidecar_path.read_text(encoding="utf-8").strip().split()[0]
    assert _sha256(archive_path) == expected_sha
    assert not (ROOT / "data" / "audit" / "multi_timeframe_alignment_lot26.json").exists()
    assert not (ROOT / "reports" / "lot_26_multi_timeframe_alignment_report.md").exists()

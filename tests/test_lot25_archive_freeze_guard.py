import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOT21_SCOPE_PATH = ROOT / "data" / "audit" / "product_scope_lot21.json"
LOT20_CLOSURE_PATH = ROOT / "data" / "audit" / "v1_closure_lot20.json"
LOT25_SNAPSHOT_PATH = ROOT / "data" / "audit" / "volatility_regime_confluence_lot25.json"


def test_lot25_preserves_the_v1_archive_freeze_metadata():
    lot21_scope = json.loads(LOT21_SCOPE_PATH.read_text(encoding="utf-8"))
    lot20_closure = json.loads(LOT20_CLOSURE_PATH.read_text(encoding="utf-8"))
    lot25_snapshot = json.loads(LOT25_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert lot21_scope["source_v1_archive_frozen"] is True
    assert lot21_scope["source_v1_archive_sha256"] == lot20_closure["archive_sha256"]
    assert lot21_scope["source_v1_archive_size_bytes"] == lot20_closure["archive_size_bytes"]
    assert lot25_snapshot["source_v1_archive_frozen"] is True


def test_lot25_scripts_do_not_replay_the_lot20_closure_builder():
    legacy = "run_lot20_" + "v1_closure.py"
    for path in [
        ROOT / "scripts" / "run_lot25_volatility_regime_confluence.py",
        ROOT / "scripts" / "validate_lot25.py",
        ROOT / "scripts" / "validate_all_until_lot25.py",
        ROOT / "scripts" / "run_required_chain_until_lot25.sh",
        ROOT / "scripts" / "diagnose_exact_chain_until_lot25.py",
    ]:
        assert legacy not in path.read_text(encoding="utf-8")

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOT21_SCOPE_PATH = ROOT / "data" / "audit" / "product_scope_lot21.json"
LOT20_CLOSURE_PATH = ROOT / "data" / "audit" / "v1_closure_lot20.json"
LOT23_SNAPSHOT_PATH = ROOT / "data" / "audit" / "technical_indicators_lot23.json"


def test_lot23_preserves_the_v1_archive_freeze_metadata():
    lot21_scope = json.loads(LOT21_SCOPE_PATH.read_text(encoding="utf-8"))
    lot20_closure = json.loads(LOT20_CLOSURE_PATH.read_text(encoding="utf-8"))
    lot23_snapshot = json.loads(LOT23_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert lot21_scope["source_v1_archive_frozen"] is True
    assert lot21_scope["source_v1_archive_sha256"] == lot20_closure["archive_sha256"]
    assert lot21_scope["source_v1_archive_size_bytes"] == lot20_closure["archive_size_bytes"]
    assert lot23_snapshot["source_v1_archive_frozen"] is True


def test_lot23_scripts_do_not_replay_the_lot20_closure_builder():
    legacy = "run_lot20_" + "v1_closure.py"
    for path in [
        ROOT / "scripts" / "run_lot23_technical_indicators.py",
        ROOT / "scripts" / "validate_lot23.py",
        ROOT / "scripts" / "validate_all_until_lot23.py",
        ROOT / "scripts" / "run_required_chain_until_lot23.sh",
        ROOT / "scripts" / "diagnose_exact_chain_until_lot23.py",
    ]:
        assert legacy not in path.read_text(encoding="utf-8")

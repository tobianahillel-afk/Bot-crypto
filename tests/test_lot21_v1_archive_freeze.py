from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validate_v1_archive_frozen_script_exists_and_never_replays_lot20_closure():
    path = ROOT / "scripts" / "validate_v1_archive_frozen.py"
    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "run_lot20_v1_closure.py" not in text
    assert "V1 ARCHIVE FROZEN VALIDATION: PASS" in text


def test_lot21_bis_chain_scripts_no_longer_replay_lot20_closure():
    targets = [
        ROOT / "scripts" / "validate_all_until_lot21.py",
        ROOT / "scripts" / "run_required_chain_until_lot21.sh",
        ROOT / "scripts" / "diagnose_exact_chain_until_lot21.py",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "run_lot20_v1_closure.py" not in text


def test_product_scope_registry_records_the_frozen_archive_fields():
    text = (ROOT / "data" / "audit" / "product_scope_lot21.json").read_text(encoding="utf-8")
    assert '"source_v1_archive_frozen": true' in text
    assert '"source_v1_archive_sha256": "' in text

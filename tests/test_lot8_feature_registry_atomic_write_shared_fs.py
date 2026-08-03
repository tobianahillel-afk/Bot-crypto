from __future__ import annotations

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "audit_lot8_feature_registry.py"
WRITER_PATH = ROOT / "src" / "crypto_quant_bot" / "audit" / "writer.py"
OUTPUT_PATH = ROOT / "data" / "audit" / "feature_registry_audit_lot8.json"


def test_lot8_feature_registry_script_does_not_use_fixed_tmp_name():
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    assert ".feature_registry_audit_lot8.json.tmp" not in text
    assert "write_json(" in text


def test_lot8_audit_writer_uses_unique_tmp_and_atomic_replace():
    text = WRITER_PATH.read_text(encoding="utf-8")
    assert "path.parent.mkdir(parents=True, exist_ok=True)" in text
    assert "uuid4" in text
    assert "os.getpid()" in text
    assert "os.replace(" in text
    assert "os.fsync(" in text
    assert '".{path.stem}.{os.getpid()}.{uuid4().hex}{path.suffix}.tmp"' in text


def test_lot8_feature_registry_audit_remains_green_across_repeated_runs():
    backup = OUTPUT_PATH.read_bytes() if OUTPUT_PATH.exists() else None
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    try:
        for _ in range(3):
            try:
                runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
            except SystemExit as exc:
                assert exc.code == 0
            assert OUTPUT_PATH.exists()
            payload = OUTPUT_PATH.read_text(encoding="utf-8")
            assert '"validation_status": "validated_lot8"' in payload
    finally:
        if not OUTPUT_PATH.exists() and backup is not None:
            OUTPUT_PATH.write_bytes(backup)

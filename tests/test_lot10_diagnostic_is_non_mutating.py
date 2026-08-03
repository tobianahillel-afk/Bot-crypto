import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSE_PATH = ROOT / "scripts" / "diagnose_lot10_transaction_cost_writer.py"
CATALOG_PATH = ROOT / "data" / "audit" / "dataset_catalog.json"
MANIFEST_PATH = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"


def _run_script(path: Path, argv: list[str]) -> int:
    previous_argv = sys.argv[:]
    sys.argv = argv
    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    finally:
        sys.argv = previous_argv
    return 0


def test_lot10_diagnostic_is_non_mutating_by_default():
    catalog_before = CATALOG_PATH.read_bytes()
    manifest_before = MANIFEST_PATH.read_bytes()
    rc = _run_script(DIAGNOSE_PATH, [str(DIAGNOSE_PATH)])
    assert rc == 0
    assert CATALOG_PATH.read_bytes() == catalog_before
    assert MANIFEST_PATH.read_bytes() == manifest_before


def test_lot10_diagnostic_supports_explicit_rerun_mode():
    text = DIAGNOSE_PATH.read_text(encoding="utf-8")
    assert "--rerun" in text
    assert "if args.rerun" in text
    assert "diagnostic mutated tracked artifact" in text

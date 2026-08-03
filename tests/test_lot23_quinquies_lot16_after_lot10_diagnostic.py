import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOT10_DIAGNOSE_PATH = ROOT / "scripts" / "diagnose_lot10_transaction_cost_writer.py"
LOT16_RUN_PATH = ROOT / "scripts" / "run_lot16_reproducibility_manifest.py"
LOT16_VALIDATE_PATH = ROOT / "scripts" / "validate_lot16.py"
LOT16_DIAGNOSE_PATH = ROOT / "scripts" / "diagnose_lot16_source_catalog_checksum.py"
RETURN_SHELL_PATH = ROOT / "scripts" / "diagnose_exact_chain_return_shell.py"
EXACT_CHAIN_PATH = ROOT / "scripts" / "diagnose_exact_chain_until_lot23.py"
BACKUP_PATHS = [
    ROOT / "data" / "audit" / "dataset_catalog.json",
    ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json",
    ROOT / "data" / "audit" / "reproducibility_artifacts_lot16.jsonl",
    ROOT / "reports" / "lot_16_reproducibility_report.md",
    ROOT / "reports" / "lot_16_validation_report.md",
]


def _run_script(path: Path, argv: list[str] | None = None) -> int:
    previous_argv = sys.argv[:]
    sys.argv = argv or [str(path)]
    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    finally:
        sys.argv = previous_argv
    return 0


def _snapshot(paths: list[Path]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in paths if path.exists()}


def _restore(snapshot: dict[Path, bytes]) -> None:
    for path in BACKUP_PATHS:
        if path in snapshot:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(snapshot[path])


def test_lot16_checksum_stays_valid_after_default_lot10_diagnostic():
    snapshot = _snapshot(BACKUP_PATHS)
    try:
        assert _run_script(LOT16_RUN_PATH) == 0
        assert _run_script(LOT16_VALIDATE_PATH) == 0
        assert _run_script(LOT10_DIAGNOSE_PATH, [str(LOT10_DIAGNOSE_PATH)]) == 0
        assert _run_script(LOT16_DIAGNOSE_PATH) == 0
    finally:
        _restore(snapshot)


def test_chain_diagnostics_keep_lot10_diagnostic_in_default_non_mutating_mode():
    forbidden = "diagnose_lot10_transaction_cost_writer.py --rerun"
    assert forbidden not in RETURN_SHELL_PATH.read_text(encoding="utf-8")
    assert forbidden not in EXACT_CHAIN_PATH.read_text(encoding="utf-8")

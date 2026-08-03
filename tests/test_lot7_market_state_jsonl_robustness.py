import hashlib
import importlib.util
from pathlib import Path

import pytest

from crypto_quant_bot.market_state.loader import InvalidJsonlError, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
LOT7_5M_PATH = ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl"
LOT7_15M_PATH = ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_script(path: Path):
    module_name = f"test_{path.stem}_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_script_main(path: Path) -> int:
    return int(_load_script(path).main())


def test_read_jsonl_ignores_strictly_empty_lines(tmp_path: Path):
    sample = tmp_path / "sample.jsonl"
    sample.write_text('\n{"timestamp":"a"}\n\n{"timestamp":"b"}\n', encoding="utf-8")
    rows = read_jsonl(sample)
    assert [row["timestamp"] for row in rows] == ["a", "b"]


def test_read_jsonl_reports_path_and_line_for_invalid_content(tmp_path: Path):
    sample = tmp_path / "broken.jsonl"
    sample.write_text('{"timestamp":"ok"}\nnot-json\n', encoding="utf-8")
    with pytest.raises(InvalidJsonlError) as exc_info:
        read_jsonl(sample)
    message = str(exc_info.value)
    assert str(sample) in message
    assert "line 2" in message
    assert "not-json" in message


def test_build_lot7_replaces_corrupted_output_and_keeps_archive_frozen():
    archive_path = ROOT / "dist" / "crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
    before_archive_sha = _sha256(archive_path)
    original_text = LOT7_5M_PATH.read_text(encoding="utf-8")
    try:
        LOT7_5M_PATH.write_text('{"timestamp":"ok"}\nnot-json\n', encoding="utf-8")
        assert _run_script_main(ROOT / "scripts" / "build_lot7_market_state.py") == 0
        rows = read_jsonl(LOT7_5M_PATH)
        assert len(rows) == 36
        assert rows[0]["timeframe"] == "5m"
    finally:
        needs_restore = True
        if LOT7_5M_PATH.exists():
            try:
                needs_restore = len(read_jsonl(LOT7_5M_PATH)) != 36
            except InvalidJsonlError:
                needs_restore = True
        if needs_restore:
            LOT7_5M_PATH.write_text(original_text, encoding="utf-8")
        assert _run_script_main(ROOT / "scripts" / "run_lot16_reproducibility_manifest.py") == 0
        assert _run_script_main(ROOT / "scripts" / "run_lot17_health_monitor.py") == 0
    after_archive_sha = _sha256(archive_path)
    assert before_archive_sha == after_archive_sha


def test_validate_lot7_and_lot7_jsonl_diagnose_pass_after_rebuild():
    assert _run_script_main(ROOT / "scripts" / "validate_lot7.py") == 0
    assert _run_script_main(ROOT / "scripts" / "diagnose_lot7_market_state_jsonl.py") == 0
    assert len(read_jsonl(LOT7_15M_PATH)) == 12

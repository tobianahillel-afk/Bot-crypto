from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot24_required_chain_shell_is_simple_and_linear():
    text = (ROOT / "scripts" / "run_required_chain_until_lot24.sh").read_text(encoding="utf-8")
    assert "PIPE" not in text
    assert "DEVNULL" not in text
    assert "pytest" not in text
    assert "run_required_chain_until_lot23.sh" in text
    assert "python scripts/diagnose_lot7_market_state_jsonl.py" in text
    assert "python scripts/diagnose_lot10_transaction_cost_writer.py" in text
    assert "python scripts/diagnose_lot16_source_catalog_checksum.py" in text
    assert "python scripts/validate_v1_archive_frozen.py" in text
    assert "python scripts/run_lot24_trend_range_momentum.py" in text
    assert "python scripts/validate_lot24.py" in text
    assert "run_lot20_" + "v1_closure.py" not in text
    assert "LOT 24 REQUIRED CHAIN: PASS" in text


def test_lot24_orchestrated_validation_wraps_lot23_then_lot24():
    text = (ROOT / "scripts" / "validate_all_until_lot24.py").read_text(encoding="utf-8")
    assert '["python", "scripts/validate_all_until_lot23.py"]' in text
    assert '["python", "scripts/diagnose_lot7_market_state_jsonl.py"]' in text
    assert '["python", "scripts/diagnose_lot10_transaction_cost_writer.py"]' in text
    assert '["python", "scripts/diagnose_lot16_source_catalog_checksum.py"]' in text
    assert '["python", "scripts/validate_v1_archive_frozen.py"]' in text
    assert '["python", "scripts/run_lot24_trend_range_momentum.py"]' in text
    assert '["python", "scripts/validate_lot24.py"]' in text
    assert "run_lot20_" + "v1_closure.py" not in text
    assert "LOT 24 ORCHESTRATED VALIDATION: PASS" in text

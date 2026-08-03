from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot10.sh"
FORBIDDEN_IN_SMOKE_BLOCK = [
    "subprocess.run",
    "subprocess.call",
    "Popen",
    "os." + "system",
    "python -m pytest",
    "pytest -q",
    "validate_all",
    "run_required_chain",
    "run_lot9_backtest_replay.py",
    "run_lot10_transaction_costs.py",
    "python - <<",
]


def _smoke_block() -> str:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "=== RUN passive smoke subset ===" in text
    assert "=== DONE passive smoke subset ===" in text
    return text.split("=== RUN passive smoke subset ===", 1)[1].split("=== DONE passive smoke subset ===", 1)[0]


def test_lot10_required_chain_uses_shell_only_passive_smoke_subset():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "LOT 10-octies REQUIRED CHAIN: PASS" in text
    assert "python - <<" not in text
    assert "python -m pytest" not in text
    block = _smoke_block()
    assert "LOT 10 PASSIVE SMOKE SUBSET: PASS" in block
    assert "transaction_cost_lot10_run_result.json" in block
    assert "transaction_cost_lot10_5m_estimates.jsonl" in block
    assert "transaction_cost_lot10_15m_estimates.jsonl" in block
    for token in FORBIDDEN_IN_SMOKE_BLOCK:
        assert token not in block, f"passive smoke block contains forbidden active token: {token}"


def test_lot10_required_chain_omits_shell_lingering_check_from_required_chain():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "check_no_lingering_direct_children" not in text
    assert "pgrep -P $$" not in text
    assert "ps -o pid,ppid,stat,cmd" not in text
    assert text.rstrip().endswith('echo "LOT 10-octies REQUIRED CHAIN: PASS"\nexit 0')

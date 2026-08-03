from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot10.sh"

FORBIDDEN = [
    "pgrep -P $$",
    "ps -o pid,ppid,stat,cmd",
    'children="$(' ,
    'live_children="$(' ,
]


def test_lot10_required_chain_has_no_shell_lingering_check():
    text = SCRIPT.read_text(encoding="utf-8")
    for token in FORBIDDEN:
        assert token not in text, f"run_required_chain_until_lot10.sh contains forbidden shell lingering check token: {token}"
    assert "LOT 10-octies REQUIRED CHAIN: PASS" in text

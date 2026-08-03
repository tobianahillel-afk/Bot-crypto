from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot10_lingering_process_diagnostic_exists_and_is_passive():
    path = ROOT / "scripts" / "diagnose_lot10_lingering_processes.py"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "DIAGNOSE LOT10 LINGERING PROCESSES: PASS" in text
    assert "subprocess" not in text
    assert "Popen" not in text
    assert "os." + "system" not in text
    assert "signal." not in text
    assert "SUSPECT_TOKENS" in text

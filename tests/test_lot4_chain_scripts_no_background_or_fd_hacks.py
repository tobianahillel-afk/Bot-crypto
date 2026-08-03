from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "scripts" / "validate_lot0.py",
    ROOT / "scripts" / "ingest_ohlcvt_fixture.py",
    ROOT / "scripts" / "validate_lot1.py",
    ROOT / "scripts" / "build_lot2_datasets.py",
    ROOT / "scripts" / "validate_lot2.py",
    ROOT / "scripts" / "build_lot3_pivots.py",
    ROOT / "scripts" / "validate_lot3.py",
    ROOT / "scripts" / "build_lot4_volume_vwap.py",
    ROOT / "scripts" / "validate_lot4.py",
]
SUB = "subprocess"


def forbidden_tokens() -> list[str]:
    return [
        "multi" + "processing",
        "threading." + "Thread",
        "daemon" + "=False",
        "atexit." + "register",
        SUB + "." + "Popen",
        "os." + "fork",
        "p" + "ty",
        "asyncio." + "create_task",
        "os." + "system",
        "os." + "spawn",
        "os." + "posix_spawn",
        "os." + "_exit",
        "signal." + "alarm",
        "close_standard" + "_streams",
        "os." + "dup2",
        "DEV" + "NULL",
        "PIPE",
        "capture_output" + "=True",
    ]


def test_lot4_chain_scripts_have_no_background_or_fd_hacks() -> None:
    offenders: list[str] = []
    for script in SCRIPTS:
        text = script.read_text(encoding="utf-8", errors="replace")
        for token in forbidden_tokens():
            if token in text:
                offenders.append(f"{script.relative_to(ROOT).as_posix()} contains {token}")
    assert offenders == []

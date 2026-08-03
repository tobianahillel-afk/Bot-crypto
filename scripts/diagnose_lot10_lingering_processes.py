#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUSPECT_TOKENS = [
    "run_required_chain_until_lot10.sh",
    "validate_all_until_lot10.py",
    "run_lot10_transaction_costs.py",
    "validate_lot10.py",
    "run_lot9_backtest_replay.py",
    "validate_lot9.py",
    "audit_lot8_feature_registry.py",
    "audit_lot8_no_lookahead.py",
    "validate_lot8.py",
]


def _cmdline(pid: str) -> str:
    try:
        raw = Path("/proc") / pid / "cmdline"
        return raw.read_bytes().replace(b"\x00", b" ").decode("utf-8", errors="replace")
    except OSError:
        return ""


def main() -> int:
    current = os.getpid()
    print(f"DIAGNOSE LOT10 LINGERING PROCESSES parent_pid={current}", flush=True)
    suspects: list[tuple[int, str]] = []
    proc = Path("/proc")
    if proc.exists():
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            if pid == current:
                continue
            cmd = _cmdline(entry.name)
            if not cmd:
                continue
            if any(token in cmd for token in SUSPECT_TOKENS):
                if "diagnose_lot10_lingering_processes.py" in cmd:
                    continue
                suspects.append((pid, cmd))
    if suspects:
        print("Lingering suspicious processes detected:", flush=True)
        for pid, cmd in suspects:
            print(f"  pid={pid} cmd={cmd}", flush=True)
        return 1
    print("DIAGNOSE LOT10 LINGERING PROCESSES: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

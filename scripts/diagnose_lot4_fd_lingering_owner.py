#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ROOT_TEXT = str(ROOT)

STEPS: list[tuple[str, list[str], int]] = [
    ("validate_lot0", ["python", "scripts/validate_lot0.py"], 60),
    ("ingest_ohlcvt_fixture", ["python", "scripts/ingest_ohlcvt_fixture.py"], 60),
    ("validate_lot1", ["python", "scripts/validate_lot1.py"], 60),
    ("build_lot2_datasets", ["python", "scripts/build_lot2_datasets.py"], 60),
    ("validate_lot2", ["python", "scripts/validate_lot2.py"], 60),
    ("build_lot3_pivots", ["python", "scripts/build_lot3_pivots.py"], 60),
    ("validate_lot3", ["python", "scripts/validate_lot3.py"], 60),
    ("build_lot4_volume_vwap", ["python", "scripts/build_lot4_volume_vwap.py"], 60),
    ("validate_lot4", ["python", "scripts/validate_lot4.py"], 60),
]


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    ppid: int
    cmdline: str
    cwd: str
    fd1: str
    fd2: str


def flush_streams() -> None:
    sys.stdout.flush()
    sys.stderr.flush()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _read_link(path: Path) -> str:
    try:
        return os.readlink(path)
    except OSError:
        return ""


def _cmdline(pid_dir: Path) -> str:
    raw = _read_text(pid_dir / "cmdline")
    if raw:
        return raw.replace("\x00", " ").strip()
    return _read_text(pid_dir / "comm").strip()


def _ppid(pid_dir: Path) -> int:
    status = _read_text(pid_dir / "status")
    for line in status.splitlines():
        if line.startswith("PPid:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])
    return -1


def read_processes() -> dict[int, ProcessInfo]:
    processes: dict[int, ProcessInfo] = {}
    proc = Path("/proc")
    if not proc.exists():
        return processes
    for child in proc.iterdir():
        if not child.name.isdigit():
            continue
        pid = int(child.name)
        cmdline = _cmdline(child)
        cwd = _read_link(child / "cwd")
        fd1 = _read_link(child / "fd" / "1")
        fd2 = _read_link(child / "fd" / "2")
        processes[pid] = ProcessInfo(pid=pid, ppid=_ppid(child), cmdline=cmdline, cwd=cwd, fd1=fd1, fd2=fd2)
    return processes


def ancestor_pids(processes: dict[int, ProcessInfo], pid: int) -> set[int]:
    ancestors: set[int] = set()
    current = processes.get(pid)
    while current and current.ppid > 0 and current.ppid not in ancestors:
        ancestors.add(current.ppid)
        current = processes.get(current.ppid)
    return ancestors


def descendant_pids(processes: dict[int, ProcessInfo], root_pid: int) -> set[int]:
    descendants: set[int] = set()
    changed = True
    while changed:
        changed = False
        for pid, info in processes.items():
            if pid == root_pid or pid in descendants:
                continue
            if info.ppid == root_pid or info.ppid in descendants:
                descendants.add(pid)
                changed = True
    return descendants


def project_related(info: ProcessInfo) -> bool:
    payload = f"{info.cmdline}\n{info.cwd}"
    if ROOT_TEXT in payload:
        return True
    if "crypto_quant_bot" in payload and "python" in payload:
        return True
    return False


def inherited_standard_fd(info: ProcessInfo, stdout_link: str, stderr_link: str) -> bool:
    return bool(stdout_link and info.fd1 == stdout_link) or bool(stderr_link and info.fd2 == stderr_link)


def describe(info: ProcessInfo) -> str:
    return (
        f"pid={info.pid} ppid={info.ppid} cmd={info.cmdline!r} "
        f"cwd={info.cwd!r} fd1={info.fd1!r} fd2={info.fd2!r}"
    )


def lingering_after_step(baseline_pids: set[int], protected_pids: set[int]) -> list[ProcessInfo]:
    processes = read_processes()
    stdout_link = _read_link(Path("/proc/self/fd/1"))
    stderr_link = _read_link(Path("/proc/self/fd/2"))
    descendants = descendant_pids(processes, os.getpid())
    offenders: list[ProcessInfo] = []
    for pid, info in sorted(processes.items()):
        if pid in baseline_pids or pid in protected_pids or pid == os.getpid():
            continue
        if pid in descendants or project_related(info) or inherited_standard_fd(info, stdout_link, stderr_link):
            offenders.append(info)
    return offenders


def run_step(label: str, command: list[str], timeout_seconds: int) -> int:
    print(f"BEFORE:{label}", flush=True)
    print(f"COMMAND:{label}:{' '.join(command)}", flush=True)
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - started
        print(
            f"TIMEOUT:{label}:rc=124:duration_seconds={duration:.3f}:timeout_seconds={timeout_seconds}",
            flush=True,
        )
        flush_streams()
        return 124
    duration = time.monotonic() - started
    rc = int(result.returncode)
    print(f"AFTER:{label}:rc={rc}:duration_seconds={duration:.3f}", flush=True)
    flush_streams()
    return rc


def main() -> int:
    initial_processes = read_processes()
    baseline_pids = set(initial_processes)
    protected_pids = ancestor_pids(initial_processes, os.getpid()) | {os.getpid()}
    for label, command, timeout_seconds in STEPS:
        rc = run_step(label, command, timeout_seconds)
        if rc != 0:
            print(f"DIAGNOSE LOT4 FD LINGERING OWNER: FAIL first_step={label} rc={rc}", flush=True)
            flush_streams()
            return rc
        offenders = lingering_after_step(baseline_pids, protected_pids)
        if offenders:
            print(f"LINGERING_AFTER:{label}:count={len(offenders)}", flush=True)
            for offender in offenders[:20]:
                print(f"LINGERING_PROCESS:{label}:{describe(offender)}", flush=True)
            print(f"DIAGNOSE LOT4 FD LINGERING OWNER: FAIL owner={label}", flush=True)
            flush_streams()
            return 1
        print(f"NO_LINGERING_AFTER:{label}", flush=True)
    print("DIAGNOSE LOT4 FD LINGERING OWNER: PASS", flush=True)
    flush_streams()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

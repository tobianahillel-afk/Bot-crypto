#!/usr/bin/env python3
"""Replay the complete Lot 0-25 required chain on its certified historical baseline."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRE_LOT26_CERTIFIED_COMMIT = "ecb1d3ac9c569cfa49b88f0779dc451fd4c92210"
WORKTREE = Path("/tmp/crypto-quant-bot-pre-lot26-certified")


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=360,
        check=False,
    )


def _cleanup_worktree() -> None:
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(WORKTREE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    shutil.rmtree(WORKTREE, ignore_errors=True)


def main() -> int:
    ancestry = _run(
        ["git", "merge-base", "--is-ancestor", PRE_LOT26_CERTIFIED_COMMIT, "HEAD"],
        cwd=ROOT,
    )
    if ancestry.returncode != 0:
        print("PRE_LOT26_CERTIFIED_COMMIT_NOT_IN_CURRENT_HISTORY", file=sys.stderr)
        return 1

    _cleanup_worktree()
    added = _run(
        ["git", "worktree", "add", "--detach", str(WORKTREE), PRE_LOT26_CERTIFIED_COMMIT],
        cwd=ROOT,
    )
    if added.returncode != 0:
        if added.stdout:
            print(added.stdout, end="")
        if added.stderr:
            print(added.stderr, end="", file=sys.stderr)
        return added.returncode

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(WORKTREE / "src")
        completed = _run(
            ["bash", "scripts/run_required_chain_until_lot25.sh"],
            cwd=WORKTREE,
            env=env,
        )
        print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        if completed.returncode != 0:
            return completed.returncode
        if "LOT 25 REQUIRED CHAIN: PASS" not in completed.stdout:
            print("HISTORICAL_CHAIN_PASS_MARKER_MISSING", file=sys.stderr)
            return 1
        print(f"P0_6_HISTORICAL_CHAIN: PASS certified_commit={PRE_LOT26_CERTIFIED_COMMIT}")
        return 0
    finally:
        _cleanup_worktree()


if __name__ == "__main__":
    raise SystemExit(main())

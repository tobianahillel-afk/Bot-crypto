#!/usr/bin/env python3
"""Enforce repository-wide line and branch coverage thresholds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COVERAGE = ROOT / "coverage.json"
DEFAULT_REPORT = ROOT / "reports" / "quality" / "global_coverage_gate.json"


def _percentage(covered: int, total: int) -> float:
    return 100.0 if total == 0 else 100.0 * covered / total


def evaluate(path: Path, line_minimum: float, branch_minimum: float) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    totals = payload["totals"]
    covered_lines = int(totals["covered_lines"])
    statements = int(totals["num_statements"])
    covered_branches = int(totals.get("covered_branches", 0))
    branches = int(totals.get("num_branches", 0))
    line_percent = _percentage(covered_lines, statements)
    branch_percent = _percentage(covered_branches, branches)
    status = "PASS" if line_percent >= line_minimum and branch_percent >= branch_minimum else "FAIL"
    return {
        "schema_version": "global-coverage-gate-v1",
        "covered_lines": covered_lines,
        "statements": statements,
        "line_percent": round(line_percent, 2),
        "line_minimum": line_minimum,
        "covered_branches": covered_branches,
        "branches": branches,
        "branch_percent": round(branch_percent, 2),
        "branch_minimum": branch_minimum,
        "status": status,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--line-minimum", type=float, default=90.0)
    parser.add_argument("--branch-minimum", type=float, default=85.0)
    args = parser.parse_args()

    result = evaluate(args.coverage, args.line_minimum, args.branch_minimum)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

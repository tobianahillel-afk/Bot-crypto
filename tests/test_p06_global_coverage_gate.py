from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_global_coverage import evaluate


def write_coverage(
    path: Path,
    *,
    covered_lines: int,
    statements: int,
    covered_branches: int,
    branches: int,
) -> None:
    path.write_text(
        json.dumps(
            {
                "totals": {
                    "covered_lines": covered_lines,
                    "num_statements": statements,
                    "covered_branches": covered_branches,
                    "num_branches": branches,
                }
            }
        ),
        encoding="utf-8",
    )


def test_global_coverage_gate_passes_exact_thresholds(tmp_path: Path) -> None:
    coverage = tmp_path / "coverage.json"
    write_coverage(
        coverage,
        covered_lines=90,
        statements=100,
        covered_branches=85,
        branches=100,
    )
    result = evaluate(coverage, 90.0, 85.0)
    assert result["status"] == "PASS"
    assert result["line_percent"] == 90.0
    assert result["branch_percent"] == 85.0


@pytest.mark.parametrize(
    ("covered_lines", "covered_branches", "expected_line", "expected_branch"),
    [
        (89, 85, 89.0, 85.0),
        (90, 84, 90.0, 84.0),
        (0, 0, 0.0, 0.0),
    ],
)
def test_global_coverage_gate_fails_either_threshold(
    tmp_path: Path,
    covered_lines: int,
    covered_branches: int,
    expected_line: float,
    expected_branch: float,
) -> None:
    coverage = tmp_path / "coverage.json"
    write_coverage(
        coverage,
        covered_lines=covered_lines,
        statements=100,
        covered_branches=covered_branches,
        branches=100,
    )
    result = evaluate(coverage, 90.0, 85.0)
    assert result["status"] == "FAIL"
    assert result["line_percent"] == expected_line
    assert result["branch_percent"] == expected_branch


def test_zero_statement_and_branch_files_are_fully_covered(tmp_path: Path) -> None:
    coverage = tmp_path / "coverage.json"
    write_coverage(
        coverage,
        covered_lines=0,
        statements=0,
        covered_branches=0,
        branches=0,
    )
    result = evaluate(coverage, 90.0, 85.0)
    assert result["status"] == "PASS"
    assert result["line_percent"] == 100.0
    assert result["branch_percent"] == 100.0


def test_global_coverage_gate_uses_independent_line_and_branch_denominators(
    tmp_path: Path,
) -> None:
    coverage = tmp_path / "coverage.json"
    write_coverage(
        coverage,
        covered_lines=95,
        statements=100,
        covered_branches=9,
        branches=10,
    )
    result = evaluate(coverage, 90.0, 85.0)
    assert result["status"] == "PASS"
    assert result["line_percent"] == 95.0
    assert result["branch_percent"] == 90.0


def test_invalid_coverage_payload_fails_closed(tmp_path: Path) -> None:
    coverage = tmp_path / "coverage.json"
    coverage.write_text("{}", encoding="utf-8")
    with pytest.raises(KeyError):
        evaluate(coverage, 90.0, 85.0)

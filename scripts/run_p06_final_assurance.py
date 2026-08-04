#!/usr/bin/env python3
"""Run and persist the exact-commit P0.6 final assurance evidence."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "quality" / "p06_final_assurance"
REPORT_JSON = ROOT / "reports" / "P0_6_FINAL_PRE_LOT26_ASSURANCE_REPORT.json"
REPORT_MD = ROOT / "reports" / "P0_6_FINAL_PRE_LOT26_ASSURANCE_REPORT.md"
HISTORICAL_MUTATION_TARGETS = (
    "crypto_quant_bot.market_analysis.technical_indicators.x__clamp__mutmut_*",
    "crypto_quant_bot.market_analysis.technical_indicators.x__rsi__mutmut_*",
    "crypto_quant_bot.market_analysis.technical_indicators.x__bollinger__mutmut_*",
    "crypto_quant_bot.market_analysis.technical_indicators.x__rate_of_change__mutmut_*",
    "crypto_quant_bot.market_analysis.numeric.x_require_finite_float__mutmut_*",
)


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    output_path: str

    @property
    def status(self) -> str:
        return "PASS" if self.returncode == 0 else "FAIL"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")


def _write_log(name: str, output: str) -> str:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"{_slug(name)}.log"
    path.write_text(output, encoding="utf-8")
    return str(path.relative_to(ROOT))


def _run(
    name: str,
    command: Sequence[str],
    *,
    timeout: int = 900,
    env: dict[str, str] | None = None,
) -> CommandResult:
    try:
        completed = subprocess.run(
            list(command),
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = completed.stdout
        if completed.stderr:
            output += "\n--- STDERR ---\n" + completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        output = f"{stdout}\n--- TIMEOUT ---\n{stderr}"
        returncode = 124
    output_path = _write_log(name, output)
    print(f"{name}: {'PASS' if returncode == 0 else 'FAIL'}")
    return CommandResult(name, tuple(command), returncode, output_path)


def _custom_result(
    name: str,
    command: Sequence[str],
    returncode: int,
    output: str,
) -> CommandResult:
    output_path = _write_log(name, output)
    print(f"{name}: {'PASS' if returncode == 0 else 'FAIL'}")
    return CommandResult(name, tuple(command), returncode, output_path)


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _parse_pytest_count(path: Path) -> int | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"(\d+) passed", text)
    return int(matches[-1]) if matches else None


def _mutation_score(
    path: Path,
    schema_version: str,
    *,
    aggregate: bool,
) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(
        r"🎉\s*(\d+).*?⏰\s*(\d+).*?🤔\s*(\d+).*?🙁\s*(\d+)",
        text,
        flags=re.DOTALL,
    )
    selected = matches if aggregate else matches[-1:]
    killed = sum(int(item[0]) for item in selected)
    timeout = sum(int(item[1]) for item in selected)
    suspicious = sum(int(item[2]) for item in selected)
    survived = sum(int(item[3]) for item in selected)
    evaluated = killed + timeout + suspicious + survived
    score = 0.0 if evaluated == 0 else 100.0 * (killed + timeout) / evaluated
    return {
        "schema_version": schema_version,
        "summaries_aggregated": len(selected),
        "killed": killed,
        "timeout": timeout,
        "suspicious": suspicious,
        "survived": survived,
        "evaluated": evaluated,
        "score_percent": round(score, 2),
        "minimum_score_percent": 80.0,
        "status": "PASS" if evaluated > 0 and score >= 80.0 else "FAIL",
    }


def _workspace_status() -> CommandResult:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    ignored_prefixes = ("reports/quality/p06_final_assurance/", ".coverage")
    unexpected = []
    for line in completed.stdout.splitlines():
        path = line[3:].strip()
        if not path.startswith(ignored_prefixes):
            unexpected.append(line)
    return _custom_result(
        "clean workspace after historical replay",
        ("git", "status", "--porcelain", "--untracked-files=all"),
        0 if not unexpected else 1,
        "\n".join(unexpected),
    )


def _historical_coverage(env: dict[str, str]) -> list[CommandResult]:
    results = [
        _run("coverage erase", ["coverage", "erase"], env=env),
        _run(
            "historical Lot 0-25 chain",
            [
                "coverage",
                "run",
                "--parallel-mode",
                "scripts/run_historical_chain_under_coverage.py",
            ],
            timeout=600,
            env=env,
        ),
        _run("coverage combine historical", ["coverage", "combine"], env=env),
    ]
    coverage_path = ROOT / ".coverage"
    saved = coverage_path.read_bytes() if coverage_path.is_file() else b""
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=ROOT, check=True)
    subprocess.run(
        ["git", "clean", "-fd", "-e", "reports/quality/p06_final_assurance/"],
        cwd=ROOT,
        check=True,
    )
    if saved:
        coverage_path.write_bytes(saved)
    results.append(_workspace_status())
    return results


def _changed_python_files() -> list[str]:
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            "origin/main...HEAD",
            "--",
            "*.py",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        path
        for path in completed.stdout.splitlines()
        if path and (ROOT / path).is_file()
    ]


def _run_static_checks(env: dict[str, str]) -> list[CommandResult]:
    commands = (
        (
            "compile",
            [sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests"],
        ),
        (
            "critical ruff",
            ["ruff", "check", "--select", "E9,F63,F7,F82", "src", "scripts", "tests"],
        ),
        ("mypy", ["mypy", "src/crypto_quant_bot"]),
        (
            "legacy architecture",
            [sys.executable, "scripts/validate_architecture_boundaries.py"],
        ),
        (
            "all-domain architecture",
            [sys.executable, "scripts/validate_domain_architecture.py"],
        ),
        ("semantic roadmap", [sys.executable, "scripts/audit_roadmap_semantics.py"]),
        ("traceability", [sys.executable, "scripts/validate_traceability_contract.py"]),
        (
            "numeric coercion",
            [sys.executable, "scripts/check_no_silent_numeric_coercion.py"],
        ),
        ("roadmap", [sys.executable, "scripts/validate_roadmap_documentation.py"]),
        (
            "pre-Lot26 readiness",
            [
                sys.executable,
                "scripts/validate_pre_lot26_readiness.py",
                "--write-report",
            ],
        ),
        ("quality inventory", [sys.executable, "scripts/quality_inventory.py"]),
        (
            "engineering deviations",
            [sys.executable, "scripts/validate_engineering_deviations.py"],
        ),
    )
    return [_run(name, command, env=env) for name, command in commands]


def _run_changed_file_ruff(env: dict[str, str]) -> CommandResult:
    changed = _changed_python_files()
    if not changed:
        return _custom_result(
            "changed-file ruff",
            ("ruff", "check"),
            0,
            "No changed Python files",
        )
    return _run("changed-file ruff", ["ruff", "check", *changed], env=env)


def _coverage_metrics() -> tuple[float, float]:
    payload = json.loads((ROOT / "coverage.json").read_text(encoding="utf-8"))
    totals = payload["totals"]
    statements = int(totals["num_statements"])
    covered_lines = int(totals["covered_lines"])
    branches = int(totals["num_branches"])
    covered_branches = int(totals["covered_branches"])
    line_percent = 100.0 if statements == 0 else 100.0 * covered_lines / statements
    branch_percent = 100.0 if branches == 0 else 100.0 * covered_branches / branches
    return line_percent, branch_percent


def _historical_mutation(
    env: dict[str, str],
) -> tuple[CommandResult, dict[str, object]]:
    shutil.rmtree(ROOT / "mutants", ignore_errors=True)
    targets = " ".join(f"'{target}'" for target in HISTORICAL_MUTATION_TARGETS)
    script = (
        "set -euo pipefail; for target in "
        + targets
        + '; do mutmut run "$target"; done; mutmut results'
    )
    result = _run(
        "historical mutation",
        ["bash", "-lc", script],
        timeout=2400,
        env=env,
    )
    score = _mutation_score(
        ROOT / result.output_path,
        "historical-mutation-score-v1",
        aggregate=True,
    )
    shutil.rmtree(ROOT / "mutants", ignore_errors=True)
    return result, score


def _replace_toml_array(text: str, key: str, next_key: str, values: list[str]) -> str:
    start = text.index(f"{key} = [")
    end = text.index(f"]\n{next_key}", start) + 2
    body = "\n".join(f'  "{value}",' for value in values)
    replacement = f"{key} = [\n{body}\n]\n"
    return text[:start] + replacement + text[end:]


def _patch_extended_mutation_config(text: str) -> str:
    text = _replace_toml_array(
        text,
        "source_paths",
        "only_mutate",
        ["src/crypto_quant_bot/contracts/"],
    )
    text = _replace_toml_array(
        text,
        "only_mutate",
        "pytest_add_cli_args_test_selection",
        ["src/crypto_quant_bot/contracts/decision_evidence.py"],
    )
    return _replace_toml_array(
        text,
        "pytest_add_cli_args_test_selection",
        "also_copy",
        [
            "tests/test_p06_decision_evidence.py",
            "tests/test_p06_decision_evidence_properties.py",
        ],
    )


def _extended_mutation(
    env: dict[str, str],
) -> tuple[list[CommandResult], dict[str, object]]:
    pyproject = ROOT / "pyproject.toml"
    original = pyproject.read_text(encoding="utf-8")
    results: list[CommandResult] = []
    score: dict[str, object]
    try:
        pyproject.write_text(
            _patch_extended_mutation_config(original),
            encoding="utf-8",
        )
        shutil.rmtree(ROOT / "mutants", ignore_errors=True)
        result = _run(
            "extended P0.6 mutation",
            ["mutmut", "run"],
            timeout=2400,
            env=env,
        )
        results.append(result)
        score = _mutation_score(
            ROOT / result.output_path,
            "p0-6-decision-evidence-mutation-score-v1",
            aggregate=False,
        )
    finally:
        pyproject.write_text(original, encoding="utf-8")
        shutil.rmtree(ROOT / "mutants", ignore_errors=True)
    results.append(
        _run(
            "source immutability after mutation",
            ["git", "diff", "--exit-code", "--", "src/crypto_quant_bot"],
            env=env,
        )
    )
    return results, score


def _check_rows(results: list[CommandResult]) -> list[dict[str, object]]:
    return [
        {
            "name": item.name,
            "status": item.status,
            "returncode": item.returncode,
            "command": list(item.command),
            "output_path": item.output_path,
        }
        for item in results
    ]


def _write_reports(payload: dict[str, object]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checks = payload["checks"]
    assert isinstance(checks, list)
    historical = payload["historical_mutation"]
    extended = payload["extended_mutation"]
    assert isinstance(historical, dict)
    assert isinstance(extended, dict)
    lines = [
        "# P0.6 — Final Pre-Lot26 Assurance Report",
        "",
        f"Evidence commit: `{payload['evidence_commit']}`  ",
        f"Generated at: `{payload['generated_at']}`  ",
        f"Overall status: **{payload['status']}**",
        "",
        "## Quantitative evidence",
        "",
        f"- Tests: **{payload['test_count']} passed**",
        f"- Line coverage: **{payload['line_coverage_percent']}%** (minimum 90%)",
        f"- Branch coverage: **{payload['branch_coverage_percent']}%** (minimum 85%)",
        f"- Historical mutation: **{historical['score_percent']}%**",
        f"- P0.6 decision-evidence mutation: **{extended['score_percent']}%**",
        f"- Anti-flake repetitions: **{payload['flake_repetitions_passed']}/3 PASS**",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "|---|---:|---|",
    ]
    for item in checks:
        assert isinstance(item, dict)
        lines.append(
            f"| {item['name']} | {item['status']} | `{item['output_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Safety invariants",
            "",
            "```text",
            "TradingDecision = WAIT",
            "SystemDecision = BLOCK_TRADING",
            "trade_allowed = false",
            "execution_allowed = false",
            "approved_size = 0",
            "live_execution = DISABLED",
            "leverage = FORBIDDEN",
            "withdrawals = FORBIDDEN",
            "```",
            "",
            "Lot 26 remains unimplemented until this PR is reviewed and merged.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_flake_repetitions(
    env: dict[str, str],
) -> tuple[list[CommandResult], int]:
    results = []
    passed = 0
    for attempt in range(1, 4):
        result = _run(
            f"flake repetition {attempt}",
            ["pytest", "-q"],
            timeout=1200,
            env=env,
        )
        results.append(result)
        passed += int(result.returncode == 0)
    return results, passed


def _build_payload(
    *,
    evidence_commit: str,
    results: list[CommandResult],
    test_count: int | None,
    line_percent: float,
    branch_percent: float,
    historical_mutation: dict[str, object],
    extended_mutation: dict[str, object],
    flake_passed: int,
) -> dict[str, object]:
    commands_passed = all(item.returncode == 0 for item in results)
    coverage_passed = line_percent >= 90.0 and branch_percent >= 85.0
    mutation_passed = (
        historical_mutation["status"] == "PASS"
        and extended_mutation["status"] == "PASS"
    )
    status = (
        "PASS"
        if commands_passed
        and coverage_passed
        and mutation_passed
        and flake_passed == 3
        else "FAIL"
    )
    return {
        "schema_version": "p0-6-final-assurance-report-v2",
        "evidence_commit": evidence_commit,
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "test_count": test_count,
        "line_coverage_percent": round(line_percent, 2),
        "line_coverage_minimum_percent": 90.0,
        "branch_coverage_percent": round(branch_percent, 2),
        "branch_coverage_minimum_percent": 85.0,
        "historical_mutation": historical_mutation,
        "extended_mutation": extended_mutation,
        "flake_repetitions_passed": flake_passed,
        "checks": _check_rows(results),
        "lot26_implemented": False,
        "lot26_branch_created": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "live_execution": "DISABLED",
    }


def main() -> int:
    evidence_commit = _git("rev-parse", "HEAD")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    results = _historical_coverage(env)
    results.extend(_run_static_checks(env))
    results.append(_run_changed_file_ruff(env))
    pytest_result = _run(
        "full pytest coverage",
        [
            "pytest",
            "-q",
            "--cov",
            "--cov-branch",
            "--cov-append",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml",
            "--cov-report=json:coverage.json",
        ],
        timeout=1200,
        env=env,
    )
    results.append(pytest_result)
    line_percent, branch_percent = _coverage_metrics()
    test_count = _parse_pytest_count(ROOT / pytest_result.output_path)
    results.append(_run("bandit", ["bandit", "-q", "-r", "src", "-ll"], env=env))
    results.append(
        _run("pip audit", ["pip-audit", "-r", "requirements-dev.lock"], env=env)
    )
    flake_results, flake_passed = _run_flake_repetitions(env)
    results.extend(flake_results)
    historical_result, historical_score = _historical_mutation(env)
    results.append(historical_result)
    extended_results, extended_score = _extended_mutation(env)
    results.extend(extended_results)
    payload = _build_payload(
        evidence_commit=evidence_commit,
        results=results,
        test_count=test_count,
        line_percent=line_percent,
        branch_percent=branch_percent,
        historical_mutation=historical_score,
        extended_mutation=extended_score,
        flake_passed=flake_passed,
    )
    _write_reports(payload)
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

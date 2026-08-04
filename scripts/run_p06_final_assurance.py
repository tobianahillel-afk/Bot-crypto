#!/usr/bin/env python3
"""Run and persist the exact-commit P0.6 final assurance evidence."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "quality" / "p06_final_assurance"
REPORT_JSON = ROOT / "reports" / "P0_6_FINAL_PRE_LOT26_ASSURANCE_REPORT.json"
REPORT_MD = ROOT / "reports" / "P0_6_FINAL_PRE_LOT26_ASSURANCE_REPORT.md"


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


def _run(
    name: str,
    command: Sequence[str],
    *,
    timeout: int = 900,
    env: dict[str, str] | None = None,
) -> CommandResult:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
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
    log_path = REPORT_DIR / f"{_slug(name)}.log"
    log_path.write_text(output, encoding="utf-8")
    print(f"{name}: {'PASS' if completed.returncode == 0 else 'FAIL'}")
    return CommandResult(
        name=name,
        command=tuple(command),
        returncode=completed.returncode,
        output_path=str(log_path.relative_to(ROOT)),
    )


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


def _parse_mutation(path: Path, schema_version: str) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(
        r"🎉\s*(\d+).*?⏰\s*(\d+).*?🤔\s*(\d+).*?🙁\s*(\d+)",
        text,
        flags=re.DOTALL,
    )
    if not matches:
        return {
            "schema_version": schema_version,
            "status": "FAIL",
            "reason": "mutation summary not found",
        }
    killed, timeout, suspicious, survived = map(int, matches[-1])
    evaluated = killed + timeout + suspicious + survived
    score = 0.0 if evaluated == 0 else 100.0 * (killed + timeout) / evaluated
    return {
        "schema_version": schema_version,
        "killed": killed,
        "timeout": timeout,
        "suspicious": suspicious,
        "survived": survived,
        "evaluated": evaluated,
        "score_percent": round(score, 2),
        "minimum_score_percent": 80.0,
        "status": "PASS" if evaluated > 0 and score >= 80.0 else "FAIL",
    }


def _patch_extended_mutation_config(text: str) -> str:
    start = text.index("only_mutate = [")
    end = text.index("]\npytest_add_cli_args_test_selection", start) + 2
    replacement = '''only_mutate = [
  "src/crypto_quant_bot/contracts/decision_evidence.py",
  "src/crypto_quant_bot/market_analysis/trend_range_momentum.py",
  "src/crypto_quant_bot/market_analysis/volatility_regime_confluence.py",
]'''
    text = text[:start] + replacement + text[end:]
    start = text.index("pytest_add_cli_args_test_selection = [")
    end = text.index("]\nalso_copy", start) + 2
    replacement = '''pytest_add_cli_args_test_selection = [
  "tests/test_p06_decision_evidence.py",
  "tests/test_p06_decision_evidence_properties.py",
  "tests/test_p06_trend_range_momentum_complete.py",
  "tests/test_p06_vrc_complete.py",
]'''
    return text[:start] + replacement + text[end:]


def _historical_coverage(env: dict[str, str]) -> list[CommandResult]:
    results = [
        _run("coverage erase", ["coverage", "erase"], env=env),
        _run(
            "historical Lot 0-25 chain",
            ["coverage", "run", "--parallel-mode", "scripts/run_historical_chain_under_coverage.py"],
            timeout=600,
            env=env,
        ),
        _run("coverage combine historical", ["coverage", "combine"], env=env),
    ]
    coverage_path = ROOT / ".coverage"
    saved = coverage_path.read_bytes() if coverage_path.is_file() else b""
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=ROOT, check=True)
    subprocess.run(["git", "clean", "-fd"], cwd=ROOT, check=True)
    if saved:
        coverage_path.write_bytes(saved)
    clean = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    status_path = REPORT_DIR / "workspace_after_historical.log"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(clean.stdout, encoding="utf-8")
    results.append(
        CommandResult(
            name="clean workspace after historical replay",
            command=("git", "status", "--porcelain"),
            returncode=0 if not clean.stdout.strip() else 1,
            output_path=str(status_path.relative_to(ROOT)),
        )
    )
    return results


def _write_reports(payload: dict[str, object]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checks = payload["checks"]
    assert isinstance(checks, list)
    lines = [
        "# P0.6 — Final Pre-Lot26 Assurance Report",
        "",
        f"Evidence commit: `{payload['evidence_commit']}`  ",
        f"Generated at: `{payload['generated_at']}`  ",
        f"Overall status: **{payload['status']}**",
        "",
        "## Quality evidence",
        "",
        f"- Tests: **{payload.get('test_count')} passed**",
        f"- Global line coverage: **{payload.get('line_coverage_percent')}%** (minimum 90%)",
        f"- Global branch coverage: **{payload.get('branch_coverage_percent')}%** (minimum 85%)",
        f"- Historical mutation: **{payload['historical_mutation']['score_percent']}%**",
        f"- Extended P0.6 mutation: **{payload['extended_mutation']['score_percent']}%**",
        f"- Flake repetitions: **{payload.get('flake_repetitions_passed')}/3 PASS**",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "|---|---:|---|",
    ]
    for item in checks:
        assert isinstance(item, dict)
        lines.append(f"| {item['name']} | {item['status']} | `{item['output_path']}` |")
    lines.extend(
        [
            "",
            "## Semantic and architecture guarantees",
            "",
            "- 21 canonical versions and Lots 0–177 are validated.",
            "- Capability and critical-contract ownership is single-owner and machine checked.",
            "- Cross-domain imports and private-boundary access are enforced.",
            "- `DecisionEvidenceEnvelopeV1` is mandatory for Lot 26 outputs.",
            "- Model retraining is offline, champion/challenger, gated and non-self-modifying live.",
            "- Economic promotion maximizes net utility under hard risk constraints, never gross PnL alone.",
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
            "## Verdict",
            "",
            "`GO_P0_6_FINAL_ASSURANCE` only when the overall status above is PASS. Lot 26 remains locked until this PR is human-reviewed and merged.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    evidence_commit = _git("rev-parse", "HEAD")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    results: list[CommandResult] = []

    results.extend(_historical_coverage(env))
    static_commands = [
        ("compile", [sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests"]),
        ("ruff", ["ruff", "check", "src", "scripts", "tests"]),
        ("mypy", ["mypy", "src/crypto_quant_bot"]),
        ("legacy architecture", [sys.executable, "scripts/validate_architecture_boundaries.py"]),
        ("all-domain architecture", [sys.executable, "scripts/validate_domain_architecture.py"]),
        ("semantic roadmap", [sys.executable, "scripts/audit_roadmap_semantics.py"]),
        ("traceability", [sys.executable, "scripts/validate_traceability_contract.py"]),
        ("numeric coercion", [sys.executable, "scripts/check_no_silent_numeric_coercion.py"]),
        ("roadmap", [sys.executable, "scripts/validate_roadmap_documentation.py"]),
        ("pre-Lot26 readiness", [sys.executable, "scripts/validate_pre_lot26_readiness.py", "--write-report"]),
    ]
    for name, command in static_commands:
        results.append(_run(name, command, env=env))

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
    results.append(_run("bandit", ["bandit", "-q", "-r", "src", "-ll"], env=env))
    results.append(_run("pip audit", ["pip-audit", "-r", "requirements-dev.lock"], env=env))

    flake_passed = 0
    for attempt in range(1, 4):
        result = _run(
            f"flake repetition {attempt}",
            ["pytest", "-q"],
            timeout=1200,
            env=env,
        )
        results.append(result)
        if result.returncode == 0:
            flake_passed += 1

    shutil.rmtree(ROOT / "mutants", ignore_errors=True)
    historical_mutation_result = _run("historical mutation", ["mutmut", "run"], timeout=1800, env=env)
    results.append(historical_mutation_result)
    historical_mutation = _parse_mutation(
        ROOT / historical_mutation_result.output_path,
        "historical-mutation-score-v1",
    )

    pyproject = ROOT / "pyproject.toml"
    original_pyproject = pyproject.read_text(encoding="utf-8")
    try:
        pyproject.write_text(_patch_extended_mutation_config(original_pyproject), encoding="utf-8")
        shutil.rmtree(ROOT / "mutants", ignore_errors=True)
        extended_mutation_result = _run(
            "extended P0.6 mutation",
            ["mutmut", "run"],
            timeout=2400,
            env=env,
        )
        results.append(extended_mutation_result)
        extended_mutation = _parse_mutation(
            ROOT / extended_mutation_result.output_path,
            "p0-6-extended-mutation-score-v1",
        )
    finally:
        pyproject.write_text(original_pyproject, encoding="utf-8")
        shutil.rmtree(ROOT / "mutants", ignore_errors=True)

    coverage = json.loads((ROOT / "coverage.json").read_text(encoding="utf-8"))
    totals = coverage["totals"]
    line_percent = float(totals["percent_covered"])
    branch_percent = 100.0 * int(totals["covered_branches"]) / int(totals["num_branches"])
    test_count = _parse_pytest_count(ROOT / pytest_result.output_path)

    checks = [
        {
            "name": item.name,
            "status": item.status,
            "returncode": item.returncode,
            "command": list(item.command),
            "output_path": item.output_path,
        }
        for item in results
    ]
    all_commands_passed = all(item.returncode == 0 for item in results)
    coverage_passed = line_percent >= 90.0 and branch_percent >= 85.0
    mutation_passed = (
        historical_mutation.get("status") == "PASS"
        and extended_mutation.get("status") == "PASS"
    )
    status = (
        "PASS"
        if all_commands_passed
        and coverage_passed
        and mutation_passed
        and flake_passed == 3
        else "FAIL"
    )
    payload: dict[str, object] = {
        "schema_version": "p0-6-final-assurance-report-v1",
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
        "checks": checks,
        "lot26_implemented": False,
        "lot26_branch_created": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "live_execution": "DISABLED",
    }
    _write_reports(payload)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EXPECTED_CONFIG_SHA256 = "cb6ac1d3c392df67b5eb15d4c07a8fc818772025ec05e142190b0b667308bd76"
DIRECT_LOCKED_TOOLS = {
    "bandit": "1.8.0",
    "diff-cover": "9.2.0",
    "hypothesis": "6.161.0",
    "mypy": "1.18.0",
    "mutmut": "3.5.0",
    "pip-audit": "2.9.0",
    "pytest": "8.4.0",
    "pytest-cov": "7.1.0",
    "radon": "6.0.1",
    "ruff": "0.12.0",
}

REQUIRED_FILES = [
    ".python-version",
    "requirements-dev.in",
    "requirements-dev.lock",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    "docs/PRE_LOT26_ENTRY_GATE.md",
    "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_26.md",
    "docs/adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md",
    "docs/contracts/LOT26_TEMPORAL_CONTRACTS.md",
    "docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md",
    "docs/roadmap/V02_LOT26_NORMATIVE_ADDENDUM.md",
    "contracts/schemas/timeframe_market_context_state_v1.schema.json",
    "contracts/schemas/closed_bar_availability_v1.schema.json",
    "contracts/schemas/multi_timeframe_alignment_state_v1.schema.json",
    "config/math/multi_timeframe_alignment_v1.json",
    "reports/P0_INSTITUTIONAL_HARDENING_REPORT.md",
    "data/audit/volatility_regime_confluence_timeframes_lot25.jsonl",
]

FORBIDDEN_IMPLEMENTATION_FILES = [
    "src/crypto_quant_bot/market_analysis/multi_timeframe_alignment_engine.py",
    "src/crypto_quant_bot/market_analysis/multi_timeframe_alignment_engine_models.py",
    "scripts/run_lot26_multi_timeframe_alignment_engine.py",
    "data/audit/multi_timeframe_alignment_engine_lot26.json",
]

REQUIRED_DOC_TOKENS = {
    "docs/adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md": [
        "available_at <= decision_time",
        "ASOF_BACKWARD",
        "bar_close_time",
        "open_bars",
    ],
    "docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md": [
        "overall_agreement_score",
        "weighted_coverage_ratio",
        "agreement score",
        "probability",
        "0.70",
        "0.75",
    ],
    "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md": [
        "PLANNED_LOCKED",
        "used_for_decision=false",
        "execution_allowed=false",
        "Game Theory",
    ],
    "docs/roadmap/V04_MICROSTRUCTURE_LIQUIDITY_GAME_THEORY.md": [
        "Lots 37 à 52",
        "participant_behavior = inference_explicitly_labeled",
        "execution_allowed=false",
    ],
    "README.md": [
        "Lot 25",
        "Lot 26",
        "flux continu",
        "ASOF_BACKWARD",
        "Game Theory",
    ],
}


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    evidence: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_config(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    weights = payload.get("component_weights")
    if not isinstance(weights, dict) or set(weights) != {
        "trend", "range", "momentum", "volatility", "regime", "confluence"
    }:
        errors.append("component_weights keys invalid")
    else:
        numeric = [float(value) for value in weights.values()]
        if any(value <= 0.0 for value in numeric):
            errors.append("component weights must be positive")
        if abs(sum(numeric) - 1.0) > 1e-9:
            errors.append("component weights must sum to 1")

    tf = payload.get("canonical_timeframes", {})
    if tf.get("local") != "5m" or tf.get("higher") != "15m":
        errors.append("canonical timeframe pair must be 5m/15m")
    if tf.get("continuous_ingestion") is not True or tf.get("open_bars_allowed") is not False:
        errors.append("continuous/closed-bar policy invalid")

    time_policy = payload.get("time_policy", {})
    if time_policy.get("join_method") != "ASOF_BACKWARD":
        errors.append("join_method must be ASOF_BACKWARD")
    if time_policy.get("eligibility_rule") != "available_at <= decision_time":
        errors.append("eligibility rule invalid")

    restrictions = payload.get("promotion_restrictions", {})
    if any(value is not False for value in restrictions.values()):
        errors.append("all promotion permissions must be false")

    thresholds = payload.get("classification_thresholds", {})
    aligned = float(thresholds.get("aligned_minimum", -1))
    partial = float(thresholds.get("partial_minimum", -1))
    if not 0.0 <= partial < aligned <= 1.0:
        errors.append("classification thresholds invalid")

    matrices = payload.get("categorical_compatibility", {})
    for name in ("range", "regime"):
        matrix = matrices.get(name)
        if not isinstance(matrix, dict) or not matrix:
            errors.append(f"{name} matrix missing")
            continue
        states = set(matrix)
        for source, row in matrix.items():
            if not isinstance(row, dict) or set(row) != states:
                errors.append(f"{name} matrix incomplete at {source}")
                continue
            for target, value in row.items():
                number = float(value)
                if not 0.0 <= number <= 1.0:
                    errors.append(f"{name} matrix out of bounds {source}/{target}")
                reverse = matrix.get(target, {}).get(source)
                if reverse is None or abs(number - float(reverse)) > 1e-9:
                    errors.append(f"{name} matrix not symmetric {source}/{target}")
    return errors


def _git_changed_files(root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", "origin/main...HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def run_checks(root: Path) -> list[Check]:
    checks: list[Check] = []

    missing = [path for path in REQUIRED_FILES if not (root / path).exists()]
    checks.append(Check("PRE26_FILES", "PASS" if not missing else "FAIL", "missing=" + ",".join(missing)))

    forbidden = [path for path in FORBIDDEN_IMPLEMENTATION_FILES if (root / path).exists()]
    checks.append(
        Check(
            "PRE26_NO_LOT26_IMPLEMENTATION",
            "PASS" if not forbidden else "FAIL",
            "present=" + ",".join(forbidden),
        )
    )

    config_path = root / "config/math/multi_timeframe_alignment_v1.json"
    try:
        config = _load_json(config_path)
        config_errors = validate_config(config)
        actual_sha = _sha256(config_path)
    except Exception as exc:
        config_errors = [f"config read error: {exc}"]
        actual_sha = ""
    if actual_sha != EXPECTED_CONFIG_SHA256:
        config_errors.append(f"config checksum {actual_sha} != {EXPECTED_CONFIG_SHA256}")
    checks.append(
        Check(
            "PRE26_CONFIG",
            "PASS" if not config_errors else "FAIL",
            "; ".join(config_errors) or f"sha256={actual_sha}",
        )
    )

    schema_errors: list[str] = []
    for relative in (
        "contracts/schemas/timeframe_market_context_state_v1.schema.json",
        "contracts/schemas/closed_bar_availability_v1.schema.json",
        "contracts/schemas/multi_timeframe_alignment_state_v1.schema.json",
    ):
        try:
            schema = _load_json(root / relative)
            if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
                schema_errors.append(f"{relative} must be closed object schema")
            if not schema.get("required"):
                schema_errors.append(f"{relative} required list missing")
        except Exception as exc:
            schema_errors.append(f"{relative}: {exc}")
    checks.append(Check("PRE26_SCHEMAS", "PASS" if not schema_errors else "FAIL", "; ".join(schema_errors)))

    doc_errors: list[str] = []
    for relative, tokens in REQUIRED_DOC_TOKENS.items():
        path = root / relative
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for token in tokens:
            if token not in text:
                doc_errors.append(f"{relative} missing {token}")
    checks.append(Check("PRE26_DOCUMENTATION", "PASS" if not doc_errors else "FAIL", "; ".join(doc_errors)))

    lot25_errors: list[str] = []
    lot25_path = root / "data/audit/volatility_regime_confluence_timeframes_lot25.jsonl"
    if lot25_path.exists():
        rows = [json.loads(line) for line in lot25_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if {row.get("timeframe") for row in rows} != {"5m", "15m"}:
            lot25_errors.append("Lot25 artifacts must contain exact 5m/15m states")
        if any(row.get("execution_allowed", False) or row.get("trade_allowed", False) for row in rows):
            lot25_errors.append("Lot25 artifact unexpectedly executable")
    else:
        lot25_errors.append("Lot25 timeframe artifact missing")
    checks.append(Check("PRE26_LOT25_BASELINE", "PASS" if not lot25_errors else "FAIL", "; ".join(lot25_errors)))

    python_value = (
        (root / ".python-version").read_text(encoding="utf-8").strip()
        if (root / ".python-version").exists()
        else ""
    )
    checks.append(Check("PRE26_PYTHON", "PASS" if python_value == "3.11.9" else "FAIL", python_value))

    lock_errors: list[str] = []
    lock_path = root / "requirements-dev.lock"
    lock_text = lock_path.read_text(encoding="utf-8") if lock_path.exists() else ""
    if any(operator in lock_text for operator in (">=", "<=", "~=", "!=")):
        lock_errors.append("lock contains non-exact operator")
    normalized: dict[str, str] = {}
    for line in lock_text.splitlines():
        if "==" in line and not line.startswith("#"):
            name, version = line.split("==", 1)
            normalized[name.lower().replace("_", "-")] = version.split(";", 1)[0].strip()
    for name, version in DIRECT_LOCKED_TOOLS.items():
        if normalized.get(name) != version:
            lock_errors.append(f"{name}={normalized.get(name)} expected {version}")
    checks.append(Check("PRE26_DEPENDENCY_LOCK", "PASS" if not lock_errors else "FAIL", "; ".join(lock_errors)))

    historical_errors: list[str] = []
    for changed in _git_changed_files(root):
        match = re.match(
            r"(docs/(LOT|ACCEPTANCE_CRITERIA)_([0-9]+)|data/audit/.*lot([0-9]+))",
            changed,
        )
        if match:
            lot_text = match.group(3) or match.group(4)
            if lot_text and int(lot_text) <= 25:
                historical_errors.append(changed)
        if changed.startswith("src/crypto_quant_bot/"):
            historical_errors.append(changed)
    checks.append(
        Check(
            "PRE26_HISTORICAL_IMMUTABILITY",
            "PASS" if not historical_errors else "FAIL",
            "changed=" + ",".join(historical_errors),
        )
    )

    invariants = [
        "trade_allowed = false",
        "execution_allowed = false",
        "live_execution = DISABLED",
        "leverage = FORBIDDEN",
    ]
    readme = (root / "README.md").read_text(encoding="utf-8")
    missing_invariants = [value for value in invariants if value not in readme]
    checks.append(
        Check(
            "PRE26_NO_TRADING_INVARIANTS",
            "PASS" if not missing_invariants else "FAIL",
            "missing=" + ",".join(missing_invariants),
        )
    )

    return checks


def write_outputs(root: Path, checks: list[Check]) -> None:
    status = "GO" if all(check.status == "PASS" for check in checks) else "NO_GO"
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    manifest = {
        "schema_version": "pre-lot26-readiness-manifest-v1",
        "generated_at": generated_at,
        "project": "Crypto Quant Bot V3.1-Ops",
        "baseline": "Lot25+P0",
        "next_lot": 26,
        "lot26_status": "PLANNED_LOCKED",
        "config_sha256": EXPECTED_CONFIG_SHA256,
        "checks": [asdict(check) for check in checks],
        "verdict": status,
        "trading_state": "DISABLED",
    }
    audit_path = root / "data/audit/pre_lot26_readiness_manifest.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Pre-Lot26 Entry Gate Report",
        "",
        f"Generated at: `{generated_at}`  ",
        "Project: **Crypto Quant Bot V3.1-Ops**  ",
        "Baseline: **Lot 25 + institutional P0**  ",
        "Lot 26 implementation: **not started**",
        "",
        "## Results",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in checks:
        evidence = check.evidence.replace("|", "\\|")
        lines.append(f"| `{check.check_id}` | **{check.status}** | {evidence} |")
    lines.extend(
        [
            "",
            "## Continuous flow decision",
            "",
            "Ingestion remains continuous. Closed 5m states trigger evaluation and use the last eligible",
            "closed 15m state through an as-of backward join. Open/future bars are forbidden.",
            "",
            "## Game Theory boundary",
            "",
            "Stops, take-profit behavior, liquidity sweeps and participant inference remain owned by",
            "V4 / Lots 37–52 and are not part of Lot 26.",
            "",
            "## Verdict",
            "",
            f"**{status}** to start Lot 26 only after this exact commit is green in CI and a human review",
            "explicitly unlocks the lot. All trading permissions remain disabled.",
            "",
        ]
    )
    report = root / "reports/PRE_LOT26_ENTRY_GATE_REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    checks = run_checks(root)
    if args.write_report:
        write_outputs(root, checks)
    for check in checks:
        print(f"{check.check_id}: {check.status} — {check.evidence}")
    passed = all(check.status == "PASS" for check in checks)
    print("PRE_LOT26_READINESS: " + ("GO" if passed else "NO_GO"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

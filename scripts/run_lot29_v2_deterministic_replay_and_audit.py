from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.market_analysis.alignment_io import load_json, write_json_atomic  # noqa: E402
from crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit import (  # noqa: E402
    MAX_VALIDATOR_STDOUT_BYTES,
    build_replay_state,
    replay_matches,
    run_validator,
)
from crypto_quant_bot.market_analysis.v2_replay_audit_models import (  # noqa: E402
    ReplayValidationError,
    ValidatorEvidenceV1,
)

CONFIG_PATH = "config/replay/v2_deterministic_replay_audit_v1.json"
OUTPUT_PATH = "data/audit/v2_deterministic_replay_and_audit_lot29.json"
AUDIT_PATH = "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json"
CLOSURE_PATH = "data/audit/v2_replay_closure_manifest_lot29.json"
REPORT_PATH = "reports/lot_29_v2_deterministic_replay_and_audit_report.md"
HISTORICAL_CHAIN_COMMAND = ("bash", "scripts/run_required_chain_until_lot25.sh")
HISTORICAL_CHAIN_TIMEOUT_SECONDS = 360
HISTORICAL_LOTS = frozenset(range(21, 26))
CURRENT_LOTS = frozenset(range(26, 29))


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _artifact_specs(config: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_specs = config.get("artifacts")
    if not isinstance(raw_specs, list) or not all(isinstance(item, dict) for item in raw_specs):
        raise ReplayValidationError("artifacts must be an ordered list of objects")
    return tuple(raw_specs)


def _copy_historical_workspace(root: Path, destination: Path) -> None:
    ignored = shutil.ignore_patterns(
        ".git",
        ".coverage*",
        ".hypothesis",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "mutants",
        ".tmp-*",
    )
    shutil.copytree(root, destination, ignore=ignored)


def _run_historical_chain(workspace: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(workspace / "src")
    completed = subprocess.run(
        HISTORICAL_CHAIN_COMMAND,
        cwd=workspace,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=HISTORICAL_CHAIN_TIMEOUT_SECONDS,
    )
    combined = (completed.stdout + "\n" + completed.stderr).encode("utf-8")
    if len(combined) > MAX_VALIDATOR_STDOUT_BYTES:
        raise ReplayValidationError("historical validator chain output exceeds limit")
    if completed.returncode != 0:
        tail = combined.decode("utf-8", errors="replace")[-2_000:]
        raise ReplayValidationError(
            f"historical validator chain failed with rc={completed.returncode}: {tail}"
        )
    if "LOT 25 REQUIRED CHAIN: PASS" not in completed.stdout:
        raise ReplayValidationError("historical validator chain PASS marker missing")


def _historical_validator_evidence(
    root: Path,
    specs: tuple[dict[str, Any], ...],
) -> tuple[ValidatorEvidenceV1, ...]:
    with tempfile.TemporaryDirectory(prefix="lot29-historical-replay-") as temporary:
        workspace = Path(temporary) / "repository"
        _copy_historical_workspace(root, workspace)
        _run_historical_chain(workspace)
        return tuple(
            run_validator(workspace, int(spec["lot"]), str(spec["validator"]))
            for spec in specs
            if int(spec["lot"]) in HISTORICAL_LOTS
        )


def _current_validator_evidence(
    root: Path,
    specs: tuple[dict[str, Any], ...],
) -> tuple[ValidatorEvidenceV1, ...]:
    return tuple(
        run_validator(root, int(spec["lot"]), str(spec["validator"]))
        for spec in specs
        if int(spec["lot"]) in CURRENT_LOTS
    )


def _validator_evidence(
    root: Path,
    config: dict[str, Any],
) -> tuple[ValidatorEvidenceV1, ...]:
    specs = _artifact_specs(config)
    historical = _historical_validator_evidence(root, specs)
    current = _current_validator_evidence(root, specs)
    evidence_by_lot = {item.lot: item for item in (*historical, *current)}
    expected_lots = tuple(int(spec["lot"]) for spec in specs)
    if tuple(sorted(evidence_by_lot)) != expected_lots:
        raise ReplayValidationError("validator evidence does not cover ordered lots 21..28")
    return tuple(evidence_by_lot[lot] for lot in expected_lots)


def _audit_payload(state: dict[str, Any]) -> dict[str, Any]:
    closure = state["closure_manifest"]
    return {
        "schema_version": "v2-deterministic-replay-audit-audit-v1",
        "run_id": str(
            uuid5(
                NAMESPACE_URL,
                f"lot29:{state['code_commit']}:{state['output_checksum']}",
            )
        ),
        "code_commit": state["code_commit"],
        "output_checksum": state["output_checksum"],
        "chain_checksum": closure["chain_checksum"],
        "replay_status": state["replay_status"],
        "artifact_count": len(state["artifacts"]),
        "validator_count": len(state["validators"]),
        "reason_codes": state["reason_codes"],
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def _report(state: dict[str, Any]) -> str:
    closure = state["closure_manifest"]
    return "\n".join(
        [
            "# Lot 29 — V2 Deterministic Replay & Audit Report",
            "",
            "Verdict: **GO_LOT29_V2_REPLAY_VALIDATED_OFFLINE_ONLY**",
            "",
            f"- Code commit: `{state['code_commit']}`",
            f"- Lot sequence: `{closure['lot_sequence']}`",
            f"- Artifact count: `{len(state['artifacts'])}`",
            f"- Validator count: `{len(state['validators'])}`",
            f"- Chain checksum: `{closure['chain_checksum']}`",
            f"- Output checksum: `{state['output_checksum']}`",
            f"- Replay status: `{state['replay_status']}`",
            "",
            "Lots 21–25 are validated in an isolated regenerated historical workspace.",
            "Lots 26–28 are validated on the current exact head.",
            "The closure proves deterministic continuity of the committed V2 artifact chain.",
            "It does not create a forecast, signal, trade intent, order intent or execution permission.",
            "",
            "```text",
            "analysis_only=true",
            "used_for_decision=false",
            "trade_allowed=false",
            "execution_allowed=false",
            "approved_size=0",
            "```",
            "",
        ]
    )


def run(
    root: Path,
    code_commit: str,
    *,
    execute_validators: bool = True,
) -> dict[str, Any]:
    config = load_json(root / CONFIG_PATH)
    evidence = _validator_evidence(root, config) if execute_validators else None
    first = build_replay_state(
        root,
        config,
        code_commit,
        execute_validators=False,
        validator_evidence=evidence,
    )
    second = build_replay_state(
        root,
        config,
        code_commit,
        execute_validators=False,
        validator_evidence=first.validators,
    )
    if not replay_matches(first, second):
        raise RuntimeError("V2_REPLAY_NON_DETERMINISTIC_FAIL")
    state = first.to_dict()
    audit = _audit_payload(state)
    closure = state["closure_manifest"]
    write_json_atomic(root / OUTPUT_PATH, state)
    write_json_atomic(root / AUDIT_PATH, audit)
    write_json_atomic(root / CLOSURE_PATH, closure)
    report_path = root / REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_report(state), encoding="utf-8")
    return {
        "state": state,
        "audit": audit,
        "closure": closure,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Lot 29 deterministic V2 replay audit")
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--code-commit")
    parser.add_argument("--skip-validators", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    result = run(
        root,
        args.code_commit or _git_commit(root),
        execute_validators=not args.skip_validators,
    )
    print(result["closure"]["chain_checksum"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

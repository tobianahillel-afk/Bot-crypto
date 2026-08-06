from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.market_analysis.alignment_io import load_json, write_json_atomic  # noqa: E402
from crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit import (  # noqa: E402
    build_replay_state,
    replay_matches,
)

CONFIG_PATH = "config/replay/v2_deterministic_replay_audit_v1.json"
OUTPUT_PATH = "data/audit/v2_deterministic_replay_and_audit_lot29.json"
AUDIT_PATH = "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json"
CLOSURE_PATH = "data/audit/v2_replay_closure_manifest_lot29.json"
REPORT_PATH = "reports/lot_29_v2_deterministic_replay_and_audit_report.md"


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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
            "The closure proves deterministic continuity of the certified V2 artifact chain.",
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
    first = build_replay_state(
        root,
        config,
        code_commit,
        execute_validators=execute_validators,
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

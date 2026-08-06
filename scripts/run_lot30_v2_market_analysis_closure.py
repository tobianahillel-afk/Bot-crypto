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
from crypto_quant_bot.market_analysis.v2_market_analysis_closure import (  # noqa: E402
    build_closure_state,
    replay_matches,
)

CONFIG_PATH = "config/closure/v2_market_analysis_closure_v1.json"
OUTPUT_PATH = "data/audit/v2_market_analysis_closure_lot30.json"
AUDIT_PATH = "data/audit/v2_market_analysis_closure_audit_lot30.json"
MANIFEST_PATH = "data/audit/closure_manifest_lot30.json"
REPORT_PATH = "reports/lot_30_v2_market_analysis_closure_report.md"


def _git_commit(root: Path) -> str:
    completed = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _audit_payload(state: dict[str, Any]) -> dict[str, Any]:
    manifest = state["closure_manifest"]
    return {
        "schema_version": "v2-market-analysis-closure-audit-v1",
        "run_id": str(
            uuid5(
                NAMESPACE_URL,
                f"lot30:{state['code_commit']}:{state['output_checksum']}",
            )
        ),
        "code_commit": state["code_commit"],
        "output_checksum": state["output_checksum"],
        "final_chain_checksum": manifest["final_chain_checksum"],
        "closure_status": manifest["closure_status"],
        "covered_lot_count": len(manifest["covered_lot_sequence"]),
        "upstream_artifact_count": len(state["upstream_artifacts"]),
        "validator_replay_count": len(state["validator_replays"]),
        "negative_control_count": len(state["negative_controls"]),
        "reason_codes": state["reason_codes"],
        "analysis_only": True,
        "used_for_decision": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def _report(state: dict[str, Any]) -> str:
    manifest = state["closure_manifest"]
    controls = ", ".join(item["name"] for item in state["negative_controls"])
    return "\n".join(
        [
            "# Lot 30 — V2 Market Analysis Closure Report",
            "",
            "Verdict: **GO_LOT30_V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY**",
            "",
            f"- Code commit: `{state['code_commit']}`",
            f"- Covered lots: `{manifest['covered_lot_sequence']}`",
            f"- Upstream artifact count: `{len(state['upstream_artifacts'])}`",
            f"- Lot 29 validator replays: `{len(state['validator_replays'])}`",
            f"- Negative controls: `{controls}`",
            f"- Final chain checksum: `{manifest['final_chain_checksum']}`",
            f"- Output checksum: `{state['output_checksum']}`",
            f"- Closure status: `{manifest['closure_status']}`",
            "",
            "The Lot 29 replay state remains the canonical aggregate proof for Lots 21–28.",
            "Lot 30 independently rechecks every referenced artifact checksum, the Lot 29",
            "state/audit/manifest linkage, two identical validator runs, lifecycle locking",
            "and five fail-closed negative controls before closing V2.",
            "",
            "No V3 data-governance capability is activated by this closure.",
            "Lot 31 remains `PLANNED_LOCKED` pending the post-merge audit and a separate",
            "exact-commit entry gate.",
            "",
            "```text",
            "analysis_only=true",
            "used_for_decision=false",
            "signal_generation_allowed=false",
            "risk_approval_allowed=false",
            "order_routing_allowed=false",
            "trade_allowed=false",
            "execution_allowed=false",
            "approved_size=0",
            "```",
            "",
        ]
    )


def run(root: Path, code_commit: str) -> dict[str, Any]:
    config = load_json(root / CONFIG_PATH)
    first = build_closure_state(root, config, code_commit)
    second = build_closure_state(
        root,
        config,
        code_commit,
        execute_validator=False,
        validator_evidence=first.validator_replays,
    )
    if not replay_matches(first, second):
        raise RuntimeError("V2_MARKET_ANALYSIS_CLOSURE_NON_DETERMINISTIC")
    state = first.to_dict()
    audit = _audit_payload(state)
    manifest = state["closure_manifest"]
    write_json_atomic(root / OUTPUT_PATH, state)
    write_json_atomic(root / AUDIT_PATH, audit)
    write_json_atomic(root / MANIFEST_PATH, manifest)
    report_path = root / REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_report(state), encoding="utf-8")
    return {"state": state, "audit": audit, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Lot 30 V2 market-analysis closure")
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--code-commit")
    args = parser.parse_args()
    root = args.root.resolve()
    result = run(root, args.code_commit or _git_commit(root))
    print(result["manifest"]["final_chain_checksum"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

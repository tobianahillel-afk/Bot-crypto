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

from crypto_quant_bot.market_analysis.alignment_io import (  # noqa: E402
    load_json,
    write_json_atomic,
)
from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer import (  # noqa: E402
    build_explanation_state,
    checksum,
    replay_matches,
)

CONFIG_PATH = "config/explanations/explanation_core_why_not_trade_v1.json"
OUTPUT_PATH = "data/audit/explanation_core_and_why_not_trade_layer_lot28.json"
AUDIT_PATH = "data/audit/explanation_core_and_why_not_trade_layer_audit_lot28.json"
REPORT_PATH = "reports/lot_28_explanation_core_and_why_not_trade_layer_report.md"


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _load_inputs(root: Path, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    artifacts = config["input_artifacts"]
    return (
        load_json(root / str(artifacts["global_context"])),
        load_json(root / str(artifacts["multi_timeframe_alignment"])),
    )


def _report(state: dict[str, Any], code_commit: str) -> str:
    why = state["bundle"]["why_not_trade"]
    veto_codes = ", ".join(item["reason_code"] for item in why["reasons"])
    return "\n".join(
        [
            "# Lot 28 — Explanation Core & Why-Not-Trade Layer Report",
            "",
            "Verdict: **GO_LOT28_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY**",
            "",
            f"- Code commit: `{code_commit}`",
            f"- Explanation ID: `{state['explanation_id']}`",
            f"- Decision time: `{state['decision_time']}`",
            f"- Dominant veto: `{why['dominant_reason_code']}`",
            f"- Veto set: `{veto_codes}`",
            f"- Output checksum: `{state['output_checksum']}`",
            "",
            "Every statement is rendered from a versioned template and linked to source evidence.",
            "The output is descriptive only and does not recommend or authorize an executable action.",
            "",
            "```text",
            "analysis_only=true",
            "used_for_decision=false",
            "forecast_generation_allowed=false",
            "probability_claims_allowed=false",
            "signal_generation_allowed=false",
            "risk_approval_allowed=false",
            "order_routing_allowed=false",
            "execution_allowed=false",
            "trade_allowed=false",
            "approved_size=0",
            "no_order_intent_created=true",
            "```",
            "",
        ]
    )


def run(root: Path, code_commit: str) -> dict[str, Any]:
    config = load_json(root / CONFIG_PATH)
    global_context, alignment = _load_inputs(root, config)
    first = build_explanation_state(global_context, alignment, config, code_commit)
    second = build_explanation_state(global_context, alignment, config, code_commit)
    if not replay_matches(first, second):
        raise RuntimeError("EXPLANATION_REPLAY_DIVERGENCE")
    state = first.to_dict()
    run_id = str(uuid5(NAMESPACE_URL, f"lot28:run:{first.output_checksum}:{code_commit}"))
    audit = {
        "schema_version": "explanation-core-why-not-trade-layer-audit-v1",
        "run_id": run_id,
        "decision_time": first.decision_time,
        "code_commit": code_commit,
        "config_checksum": first.config_checksum,
        "input_checksums": first.input_checksums,
        "output_checksum": first.output_checksum,
        "replay_status": "MATCH",
        "reason_codes": list(first.reason_codes),
        "dominant_reason_code": first.bundle.why_not_trade.dominant_reason_code,
        "statement_count": sum(
            len(value)
            for key, value in first.bundle.to_dict().items()
            if key not in {"schema_version", "why_not_trade"}
        ),
        "why_not_reason_count": len(first.bundle.why_not_trade.reasons),
        "analysis_only": True,
        "used_for_decision": False,
        "execution_allowed": False,
        "trade_allowed": False,
        "no_order_intent_created": True,
    }
    write_json_atomic(root / OUTPUT_PATH, state)
    write_json_atomic(root / AUDIT_PATH, audit)
    (root / REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_PATH).write_text(_report(state, code_commit), encoding="utf-8")
    return {"state": state, "audit": audit, "artifact_checksum": checksum(state)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Lot 28 offline explanation layer")
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--code-commit")
    args = parser.parse_args()
    root = args.root.resolve()
    result = run(root, args.code_commit or _git_commit(root))
    print(result["state"]["bundle"]["why_not_trade"]["dominant_reason_code"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

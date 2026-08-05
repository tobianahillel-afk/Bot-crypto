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

from crypto_quant_bot.market_analysis.global_market_context_aggregator import (  # noqa: E402
    build_global_market_context,
    checksum,
    replay_matches,
)
from crypto_quant_bot.market_analysis.alignment_io import (  # noqa: E402
    load_json,
    write_json_atomic,
)

CONFIG_PATH = "config/math/global_market_context_aggregator_v1.json"
OUTPUT_PATH = "data/audit/global_market_context_aggregator_lot27.json"
AUDIT_PATH = "data/audit/global_market_context_aggregator_audit_lot27.json"
REPORT_PATH = "reports/lot_27_global_market_context_aggregator_report.md"


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _load_sources(root: Path, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    specs = config["source_specs"]
    result: dict[str, dict[str, Any]] = {}
    for source_id, spec in specs.items():
        path = root / str(spec["artifact"])
        if path.is_file():
            result[source_id] = load_json(path)
    return result


def _report(state: dict[str, Any], code_commit: str) -> str:
    return "\n".join(
        [
            "# Lot 27 — Global Market Context Aggregator Report",
            "",
            "Verdict: **GO_LOT27_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY**",
            "",
            f"- Code commit: `{code_commit}`",
            f"- Context ID: `{state['context_id']}`",
            f"- Decision time: `{state['decision_time']}`",
            f"- Dominant state: `{state['dominant_state']}`",
            f"- Aggregate evidence score: `{state['aggregate_evidence_score']}`",
            f"- Weighted coverage: `{state['weighted_coverage_ratio']}`",
            f"- Available sources: `{state['available_source_count']}/5`",
            f"- Conflicts: `{', '.join(state['conflict_states']) or 'none'}`",
            "",
            "The aggregate is descriptive and uncalibrated. It is not a probability, forecast, signal, trade intent or order.",
            "",
            "```text",
            "analysis_only=true",
            "used_for_decision=false",
            "forecast_generation_allowed=false",
            "probability_claims_allowed=false",
            "signal_generation_allowed=false",
            "order_routing_allowed=false",
            "execution_allowed=false",
            "trade_allowed=false",
            "approved_size=0",
            "```",
            "",
        ]
    )


def run(root: Path, code_commit: str) -> dict[str, Any]:
    config = load_json(root / CONFIG_PATH)
    sources = _load_sources(root, config)
    first = build_global_market_context(sources, config, code_commit)
    second = build_global_market_context(sources, config, code_commit)
    if not replay_matches(first, second):
        raise RuntimeError("GMC_REPLAY_DIVERGENCE")
    state = first.to_dict()
    run_id = str(uuid5(NAMESPACE_URL, f"lot27:run:{first.output_checksum}:{code_commit}"))
    audit = {
        "schema_version": "global-market-context-aggregator-audit-v1",
        "run_id": run_id,
        "decision_time": first.decision_time,
        "code_commit": code_commit,
        "config_checksum": first.config_checksum,
        "input_checksums": {
            item.source_id: item.source_checksum
            for item in first.contributions
            if item.source_checksum is not None
        },
        "output_checksum": first.output_checksum,
        "replay_status": "MATCH",
        "reason_codes": list(first.reason_codes),
        "analysis_only": True,
        "used_for_decision": False,
        "execution_allowed": False,
        "trade_allowed": False,
    }
    write_json_atomic(root / OUTPUT_PATH, state)
    write_json_atomic(root / AUDIT_PATH, audit)
    (root / REPORT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_PATH).write_text(_report(state, code_commit), encoding="utf-8")
    return {"state": state, "audit": audit, "artifact_checksum": checksum(state)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Lot 27 offline context aggregator")
    parser.add_argument("--root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--code-commit")
    args = parser.parse_args()
    root = args.root.resolve()
    result = run(root, args.code_commit or _git_commit(root))
    print(result["state"]["dominant_state"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

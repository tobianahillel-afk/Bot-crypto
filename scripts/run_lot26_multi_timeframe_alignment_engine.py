from __future__ import annotations

import argparse
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from crypto_quant_bot.market_analysis.alignment_adapter import adapt_lot25_rows
from crypto_quant_bot.market_analysis.alignment_audit import (
    build_alignment_evidence,
    replay_matches,
)
from crypto_quant_bot.market_analysis.alignment_common import checksum, parse_utc
from crypto_quant_bot.market_analysis.alignment_engine import build_alignment_state
from crypto_quant_bot.market_analysis.alignment_io import (
    load_json,
    load_jsonl,
    write_json_atomic,
    write_jsonl_atomic,
)

LOT25_INPUT = "data/audit/volatility_regime_confluence_timeframes_lot25.jsonl"
CONFIG_PATH = "config/math/multi_timeframe_alignment_v1.json"
SCALE_REGISTRY_PATH = "config/temporal/temporal_scale_registry_v1.json"
CLOCK_POLICY_PATH = "config/temporal/decision_clock_policy_v1.json"
CONTEXT_OUTPUT = "data/audit/timeframe_market_context_states_lot26.jsonl"
AVAILABILITY_OUTPUT = "data/audit/closed_bar_availability_lot26.jsonl"
ALIGNMENT_OUTPUT = "data/audit/multi_timeframe_alignment_engine_lot26.json"
EVIDENCE_OUTPUT = "data/audit/multi_timeframe_alignment_evidence_lot26.json"
REPLAY_OUTPUT = "data/audit/multi_timeframe_alignment_replay_lot26.json"
REPORT_OUTPUT = "reports/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_FINAL_REPORT.md"

_DURATION = {"5m": 300, "15m": 900}


def _git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _decision_time(rows: list[dict[str, Any]]) -> str:
    closes = []
    for row in rows:
        timeframe = str(row.get("timeframe", ""))
        opened = parse_utc(str(row.get("last_timestamp", "")), "last_timestamp")
        closes.append(opened + timedelta(seconds=_DURATION[timeframe]))
    return max(closes).isoformat().replace("+00:00", "Z")


def _run_id(code_commit: str, decision_time: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"lot26:run:{code_commit}:{decision_time}"))


def _report(alignment: dict[str, Any], evidence_checksum: str, code_commit: str) -> str:
    return "\n".join(
        [
            "# Lot 26 — Multi-Timeframe Alignment Final Report",
            "",
            "Verdict: **GO_LOT26_IMPLEMENTED_VALIDATED**",
            "",
            f"- Code commit: `{code_commit}`",
            f"- Alignment ID: `{alignment['alignment_id']}`",
            f"- Edge: `{alignment['local_scale_id']} → {alignment['higher_scale_id']}`",
            f"- Join: `{alignment['join_method']}`",
            f"- Agreement score: `{alignment['overall_agreement_score']}`",
            f"- Coverage: `{alignment['weighted_coverage_ratio']}`",
            f"- Alignment: `{alignment['alignment_state']}`",
            f"- Divergence: `{alignment['divergence_state']}`",
            f"- Evidence checksum: `{evidence_checksum}`",
            "",
            "The output is descriptive only. It is not a probability, forecast, signal, trade intent or order.",
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
    rows = load_jsonl(root / LOT25_INPUT)
    config = load_json(root / CONFIG_PATH)
    scale_registry = load_json(root / SCALE_REGISTRY_PATH)
    decision_clock = load_json(root / CLOCK_POLICY_PATH)
    decision_time = _decision_time(rows)
    states, availability = adapt_lot25_rows(
        rows,
        decision_time=decision_time,
        code_commit=code_commit,
    )
    local = next(state for state in states if state.timeframe == "5m")
    higher_states = [state for state in states if state.timeframe == "15m"]
    first = build_alignment_state(
        local,
        higher_states,
        availability,
        config,
        scale_registry,
        decision_clock,
        code_commit,
    )
    second = build_alignment_state(
        local,
        higher_states,
        availability,
        config,
        scale_registry,
        decision_clock,
        code_commit,
    )
    if not replay_matches(first, second):
        raise RuntimeError("MTF_REPLAY_DIVERGENCE")
    run_id = _run_id(code_commit, decision_time)
    higher = next(state for state in states if state.state_id == first.higher_state_id)
    evidence = build_alignment_evidence(first, local, higher, run_id=run_id)
    write_jsonl_atomic(root / CONTEXT_OUTPUT, [state.to_dict() for state in states])
    write_jsonl_atomic(root / AVAILABILITY_OUTPUT, [item.to_dict() for item in availability])
    write_json_atomic(root / ALIGNMENT_OUTPUT, first.to_dict())
    write_json_atomic(root / EVIDENCE_OUTPUT, evidence.to_dict())
    replay = {
        "schema_version": "lot26-replay-evidence-v1",
        "run_id": run_id,
        "status": "MATCH",
        "run_1_checksum": first.output_checksum,
        "run_2_checksum": second.output_checksum,
        "source_commit": code_commit,
        "used_for_decision": False,
        "execution_allowed": False,
    }
    write_json_atomic(root / REPLAY_OUTPUT, replay)
    evidence_checksum = evidence.envelope_checksum()
    (root / REPORT_OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_OUTPUT).write_text(
        _report(first.to_dict(), evidence_checksum, code_commit),
        encoding="utf-8",
    )
    return {
        "alignment": first.to_dict(),
        "evidence_checksum": evidence_checksum,
        "replay": replay,
        "artifact_checksum": checksum(first.to_dict()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Lot 26 offline alignment engine")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--code-commit")
    args = parser.parse_args()
    root = args.root.resolve()
    code_commit = args.code_commit or _git_commit(root)
    result = run(root, code_commit)
    print(result["alignment"]["alignment_state"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

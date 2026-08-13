#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine import (
    build_lot45_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data/audit/order_flow_delta_cvd_engine_lot45.json"
AUDIT_PATH = ROOT / "data/audit/order_flow_delta_cvd_engine_audit_lot45.json"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    state, audit = build_lot45_artifacts(ROOT, code_commit=args.code_commit)
    write_json(STATE_PATH, state.to_dict())
    write_json(AUDIT_PATH, audit.to_dict())
    print(json.dumps({"state_output_checksum": state.output_checksum, "audit_checksum": audit.audit_checksum}, sort_keys=True))


if __name__ == "__main__":
    main()

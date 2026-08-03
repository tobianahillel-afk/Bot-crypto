#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.audit.lookahead import audit_no_lookahead, default_audited_dataset_paths
from crypto_quant_bot.audit.writer import write_json, write_no_lookahead_report



def flush_streams() -> None:
    sys.stdout.flush()
    sys.stderr.flush()


def main() -> int:
    paths = default_audited_dataset_paths(ROOT)
    payload = audit_no_lookahead(paths)
    payload["source"] = "lot8_no_lookahead_audit_bounded_explicit_policy"
    payload["used_for_decision"] = False
    write_json(ROOT / "data" / "audit" / "no_lookahead_audit_lot8.json", payload)
    write_no_lookahead_report(ROOT / "reports" / "lot_08_no_lookahead_report.md", payload)
    flush_streams()
    if payload.get("validation_status") != "validated_lot8":
        print("LOT 8 NO-LOOKAHEAD AUDIT: FAIL", flush=True)
        return 1
    print("LOT 8 NO-LOOKAHEAD AUDIT: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.risk.risk_engine import RiskEngine



def fail(message: str) -> int:
    print("LOT 8 VALIDATION: FAIL")
    print(message)
    return 1


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def list_is_empty(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    return isinstance(value, list) and len(value) == 0


def main() -> int:
    os.write(1, b"LOT 8 VALIDATION: START\n")
    required_files = [
        ROOT / "src" / "crypto_quant_bot" / "contracts" / "audit.py",
        ROOT / "src" / "crypto_quant_bot" / "audit" / "__init__.py",
        ROOT / "src" / "crypto_quant_bot" / "audit" / "feature_registry_audit.py",
        ROOT / "src" / "crypto_quant_bot" / "audit" / "lookahead.py",
        ROOT / "src" / "crypto_quant_bot" / "audit" / "forbidden_names.py",
        ROOT / "src" / "crypto_quant_bot" / "audit" / "available_at.py",
        ROOT / "src" / "crypto_quant_bot" / "audit" / "writer.py",
        ROOT / "scripts" / "audit_lot8_feature_registry.py",
        ROOT / "scripts" / "audit_lot8_no_lookahead.py",
        ROOT / "scripts" / "validate_lot8.py",
        ROOT / "data" / "audit" / "feature_registry_audit_lot8.json",
        ROOT / "data" / "audit" / "no_lookahead_audit_lot8.json",
        ROOT / "reports" / "lot_08_feature_registry_audit_report.md",
        ROOT / "reports" / "lot_08_no_lookahead_report.md",
        ROOT / "docs" / "FEATURE_REGISTRY_AUDIT_POLICY.md",
        ROOT / "docs" / "ANTI_LOOKAHEAD_AUDIT_POLICY.md",
        ROOT / "docs" / "DATA_LEAKAGE_POLICY.md",
        ROOT / "docs" / "ACCEPTANCE_CRITERIA_LOT_08.md",
        ROOT / "docs" / "LOT_08_REPORT.md",
    ]
    for path in required_files:
        if not path.exists():
            return fail(f"missing Lot 8 artifact: {path}")
    feature_payload = load_json(ROOT / "data" / "audit" / "feature_registry_audit_lot8.json")
    lookahead_payload = load_json(ROOT / "data" / "audit" / "no_lookahead_audit_lot8.json")
    for payload_name, payload in [("feature registry", feature_payload), ("no-lookahead", lookahead_payload)]:
        if payload.get("validation_status") != "validated_lot8":
            return fail(f"{payload_name} audit status is not validated_lot8")
        if payload.get("quality_flag") != "valid":
            return fail(f"{payload_name} audit quality_flag is not valid")
        for key in ["forbidden_feature_names", "lookahead_violations", "available_at_violations", "used_for_decision_violations"]:
            if not list_is_empty(payload, key):
                return fail(f"{payload_name} has non-empty {key}")
    if not list_is_empty(feature_payload, "missing_from_registry"):
        return fail("feature registry audit has missing_from_registry entries")
    status_text = (ROOT / "config" / "module_status_matrix.yaml").read_text(encoding="utf-8")
    risk_text = (ROOT / "config" / "risk.yaml").read_text(encoding="utf-8")
    if "live_execution: DISABLED" not in status_text:
        return fail("live_execution invariant broken")
    if "leverage: FORBIDDEN" not in status_text:
        return fail("leverage invariant broken")
    if "trade_allowed_default: false" not in risk_text:
        return fail("trade_allowed default invariant broken")
    decision = DecisionEngine().decide_default()
    risk = RiskEngine().evaluate_default()
    if decision.trading_decision != "WAIT" or decision.system_decision != "BLOCK_TRADING" or decision.trade_allowed is not False:
        return fail("Decision Engine invariant broken")
    if risk.trade_allowed is not False:
        return fail("Risk Engine no longer blocks by default")
    os.write(1, b"LOT 8 VALIDATION: PASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

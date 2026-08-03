import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot8_audit_outputs_and_reports_exist():
    required = [
        "data/audit/feature_registry_audit_lot8.json",
        "data/audit/no_lookahead_audit_lot8.json",
        "reports/lot_08_feature_registry_audit_report.md",
        "reports/lot_08_no_lookahead_report.md",
        "docs/FEATURE_REGISTRY_AUDIT_POLICY.md",
        "docs/ANTI_LOOKAHEAD_AUDIT_POLICY.md",
        "docs/DATA_LEAKAGE_POLICY.md",
        "docs/ACCEPTANCE_CRITERIA_LOT_08.md",
        "docs/LOT_08_REPORT.md",
    ]
    for relative in required:
        assert (ROOT / relative).exists()


def test_lot8_audit_outputs_are_valid_json():
    for relative in [
        "data/audit/feature_registry_audit_lot8.json",
        "data/audit/no_lookahead_audit_lot8.json",
    ]:
        payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        assert payload["validation_status"] == "validated_lot8"
        assert payload["used_for_decision"] is False

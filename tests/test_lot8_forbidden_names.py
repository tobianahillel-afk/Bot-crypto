import json
from pathlib import Path

from crypto_quant_bot.audit.forbidden_names import audit_forbidden_names, find_forbidden_keys
from crypto_quant_bot.audit.lookahead import default_audited_dataset_paths, read_jsonl

ROOT = Path(__file__).resolve().parents[1]


def test_lot8_forbidden_name_detector_checks_keys_not_values():
    clean = {"description": "documentation text may mention signal safely"}
    dirty = {"nested": {"future_return": 1, "label": 0, "trade_signal": "WAIT"}}
    assert find_forbidden_keys(clean) == []
    violations = find_forbidden_keys(dirty)
    keys = {item["key"] for item in violations}
    assert {"future_return", "label", "trade_signal"}.issubset(keys)


def test_lot8_audited_datasets_have_no_forbidden_keys():
    for path in default_audited_dataset_paths(ROOT):
        assert audit_forbidden_names(read_jsonl(path), path) == []


def test_lot8_audit_json_has_no_forbidden_feature_names():
    payload = json.loads((ROOT / "data" / "audit" / "no_lookahead_audit_lot8.json").read_text(encoding="utf-8"))
    assert payload["forbidden_feature_names"] == []

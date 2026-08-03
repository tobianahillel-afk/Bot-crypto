import json
from pathlib import Path

from crypto_quant_bot.audit.lookahead import audit_dataset_no_lookahead, audit_no_lookahead, default_audited_dataset_paths

ROOT = Path(__file__).resolve().parents[1]


def test_lot8_no_lookahead_audit_json_is_clean():
    payload = json.loads((ROOT / "data" / "audit" / "no_lookahead_audit_lot8.json").read_text(encoding="utf-8"))
    assert payload["validation_status"] == "validated_lot8"
    assert payload["quality_flag"] == "valid"
    assert payload["forbidden_feature_names"] == []
    assert payload["lookahead_violations"] == []
    assert payload["available_at_violations"] == []
    assert payload["used_for_decision_violations"] == []


def test_lot8_no_lookahead_dataset_audit_is_clean_for_market_state():
    result = audit_dataset_no_lookahead(ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl")
    assert result.validation_status == "validated_lot8"
    assert result.violations == []
    assert result.component_available_at_checked is True


def test_lot8_no_lookahead_full_function_is_clean():
    payload = audit_no_lookahead(default_audited_dataset_paths(ROOT))
    assert payload["validation_status"] == "validated_lot8"
    assert payload["violations"] == []

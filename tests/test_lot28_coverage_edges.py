from __future__ import annotations

import copy

import pytest

from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer import (
    ExplanationValidationError,
    _assert_forbidden_tokens_absent,
    _mapping,
    _shared_values,
    build_explanation_state,
    validate_config,
    validate_inputs,
)
from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer_models import (
    WhyNotTradeReasonSetV1,
    require_text,
)
from crypto_quant_bot.market_analysis.explanation_core_validation import (
    ExplanationEvidenceError,
    iter_statements,
    validate_reason_set,
    validate_statements,
)
from tests.lot28_fixtures import cloned_inputs, load_config, load_inputs

COMMIT = "abcdef1234567890"


def built_bundle_sources() -> tuple[dict[str, object], dict[str, dict[str, object]], dict[str, object]]:
    global_context, alignment = load_inputs()
    config = load_config()
    state = build_explanation_state(global_context, alignment, config, COMMIT)
    sources = {
        config["input_artifacts"]["global_context"]: global_context,
        config["input_artifacts"]["multi_timeframe_alignment"]: alignment,
    }
    return state.bundle.to_dict(), sources, config


def test_config_contract_rejects_missing_template_and_registry_fields() -> None:
    config = load_config()
    config["templates"]["fact_global_context"]["text"] = ""
    with pytest.raises(ExplanationValidationError, match="template text missing"):
        validate_config(config)

    config = load_config()
    config["templates"]["fact_global_context"]["reason_code"] = ""
    with pytest.raises(ExplanationValidationError, match="reason code missing"):
        validate_config(config)

    config = load_config()
    config["why_not_trade_reasons"]["WNT_CONTEXT_MIXED"]["owner"] = ""
    with pytest.raises(ExplanationValidationError, match="must be non-empty"):
        validate_config(config)

    config = load_config()
    config["input_artifacts"].pop("global_context")
    with pytest.raises(ExplanationValidationError, match="input registry"):
        validate_config(config)


def test_input_contract_rejects_alignment_schema_safety_and_state() -> None:
    config = load_config()
    global_context, alignment = cloned_inputs()
    alignment["schema_version"] = "other"
    with pytest.raises(ExplanationValidationError, match="alignment schema"):
        validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    alignment["execution_allowed"] = True
    with pytest.raises(ExplanationValidationError, match="alignment safety"):
        validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    alignment["alignment_state"] = "MTF_ALIGNED"
    with pytest.raises(ExplanationValidationError, match="divergence"):
        validate_inputs(global_context, alignment, config)


def test_private_fail_closed_helpers_reject_invalid_shapes_and_tokens() -> None:
    with pytest.raises(ExplanationValidationError, match="must be an object"):
        _mapping([], "payload")

    global_context, alignment = cloned_inputs()
    global_context["conflict_states"] = ["A", "B"]
    with pytest.raises(ExplanationValidationError, match="exactly one"):
        _shared_values(global_context, alignment)

    with pytest.raises(ExplanationValidationError, match="forbidden"):
        _assert_forbidden_tokens_absent({"text": "BUY"}, load_config())


def test_model_contract_rejects_empty_text_and_unknown_dominant_reason() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        require_text("", "field")

    global_context, alignment = load_inputs()
    state = build_explanation_state(global_context, alignment, load_config(), COMMIT)
    reason_set = state.bundle.why_not_trade
    with pytest.raises(ValueError, match="dominant reason"):
        WhyNotTradeReasonSetV1(
            reason_set_id="invalid",
            reasons=reason_set.reasons,
            dominant_reason_code="UNKNOWN",
            final_consequence=reason_set.final_consequence,
        )


def test_statement_validator_rejects_invalid_section_count_identity_text_and_evidence() -> None:
    bundle, sources, config = built_bundle_sources()

    altered = copy.deepcopy(bundle)
    altered["facts_observed"] = "not-a-list"
    with pytest.raises(ExplanationEvidenceError, match="invalid statement section"):
        iter_statements(altered)

    altered = copy.deepcopy(bundle)
    altered["facts_observed"][1]["statement_id"] = altered["facts_observed"][0]["statement_id"]
    with pytest.raises(ExplanationEvidenceError, match="duplicate"):
        validate_statements(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["facts_observed"].pop()
    with pytest.raises(ExplanationEvidenceError, match="count"):
        validate_statements(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["facts_observed"][0]["text"] = "tampered"
    with pytest.raises(ExplanationEvidenceError, match="text diverges"):
        validate_statements(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["facts_observed"][0]["evidence_refs"] = []
    with pytest.raises(ExplanationEvidenceError, match="no source evidence"):
        validate_statements(altered, config, sources)


def test_reason_validator_rejects_count_code_order_and_summary_drift() -> None:
    bundle, sources, config = built_bundle_sources()

    altered = copy.deepcopy(bundle)
    altered["why_not_trade"]["reasons"].pop()
    with pytest.raises(ExplanationEvidenceError, match="count mismatch"):
        validate_reason_set(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["why_not_trade"]["reasons"][0]["reason_code"] = "UNKNOWN"
    with pytest.raises(ExplanationEvidenceError, match="unknown reason code"):
        validate_reason_set(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["why_not_trade"]["reasons"][0]["order_intent_created"] = True
    with pytest.raises(ExplanationEvidenceError, match="claims an order"):
        validate_reason_set(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["why_not_trade"]["no_order_intent_created"] = False
    with pytest.raises(ExplanationEvidenceError, match="prove no order"):
        validate_reason_set(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["final_consequence"] = []
    with pytest.raises(ExplanationEvidenceError, match="one statement"):
        validate_reason_set(altered, config, sources)

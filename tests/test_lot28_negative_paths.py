from __future__ import annotations

import copy

import pytest

from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer import (
    ExplanationValidationError,
    build_explanation_state,
    render_template,
    validate_config,
    validate_inputs,
)
from tests.lot28_fixtures import cloned_inputs, load_config, load_inputs

COMMIT = "abcdef1234567890"


def test_config_rejects_schema_template_order_and_duplicate_reason_codes() -> None:
    config = load_config()
    config["schema_version"] = "other"
    with pytest.raises(ExplanationValidationError, match="unsupported"):
        validate_config(config)

    config = load_config()
    config["statement_order"] = config["statement_order"][:-1]
    with pytest.raises(ExplanationValidationError, match="every template"):
        validate_config(config)

    config = load_config()
    config["statement_order"].append(config["statement_order"][0])
    with pytest.raises(ExplanationValidationError, match="unique"):
        validate_config(config)

    config = load_config()
    config["templates"]["fact_alignment"]["reason_code"] = config["templates"]["fact_global_context"][
        "reason_code"
    ]
    with pytest.raises(ExplanationValidationError, match="reason codes"):
        validate_config(config)


def test_config_rejects_unknown_sections_missing_reason_registry_and_permission_escalation() -> None:
    config = load_config()
    config["templates"]["fact_alignment"]["section"] = "narrative"
    with pytest.raises(ExplanationValidationError, match="invalid section"):
        validate_config(config)

    config = load_config()
    config["why_not_trade_reasons"].pop("WNT_CONTEXT_MIXED")
    with pytest.raises(ExplanationValidationError, match="incomplete"):
        validate_config(config)

    config = load_config()
    config["promotion_restrictions"]["execution_allowed"] = True
    with pytest.raises(ExplanationValidationError, match="permissions"):
        validate_config(config)

    config = load_config()
    config["forbidden_output_tokens"] = ["BUY"]
    with pytest.raises(ExplanationValidationError, match="token registry"):
        validate_config(config)


def test_input_schema_instrument_and_time_divergence_fail_closed() -> None:
    global_context, alignment = cloned_inputs()
    config = load_config()
    global_context["schema_version"] = "other"
    with pytest.raises(ExplanationValidationError, match="global context schema"):
        validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    alignment["instrument_id"] = "ETH/EUR"
    with pytest.raises(ExplanationValidationError, match="instruments"):
        validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    alignment["decision_time"] = "2026-05-25T03:05:00Z"
    with pytest.raises(ExplanationValidationError, match="decision times"):
        validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    alignment["decision_time"] = "2026-05-25T03:00:00"
    with pytest.raises(ValueError, match="UTC"):
        validate_inputs(global_context, alignment, config)


def test_input_safety_and_validation_escalations_fail_closed() -> None:
    config = load_config()
    for field in (
        "used_for_decision",
        "forecast_generation_allowed",
        "probability_claims_allowed",
        "signal_generation_allowed",
        "order_routing_allowed",
        "execution_allowed",
        "trade_allowed",
    ):
        global_context, alignment = cloned_inputs()
        global_context[field] = True
        with pytest.raises(ExplanationValidationError, match="safety"):
            validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    global_context["approved_size"] = 1
    with pytest.raises(ExplanationValidationError, match="approved_size"):
        validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    global_context["validation_state"] = "UNKNOWN"
    with pytest.raises(ExplanationValidationError, match="not validated"):
        validate_inputs(global_context, alignment, config)


def test_template_version_rejects_unexpected_context_alignment_and_coherence() -> None:
    config = load_config()
    global_context, alignment = cloned_inputs()
    global_context["dominant_state"] = "GLOBAL_CONTEXT_TRENDING"
    with pytest.raises(ExplanationValidationError, match="mixed global context"):
        validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    global_context["conflict_states"] = []
    with pytest.raises(ExplanationValidationError, match="divergence"):
        validate_inputs(global_context, alignment, config)

    global_context, alignment = cloned_inputs()
    alignment["coherence_state"] = "MTF_COHERENT"
    with pytest.raises(ExplanationValidationError, match="incoherent"):
        validate_inputs(global_context, alignment, config)


def test_render_template_rejects_unknown_template_and_missing_parameters() -> None:
    config = load_config()
    with pytest.raises(ExplanationValidationError, match="unknown template"):
        render_template(config, "unknown", {})
    with pytest.raises(ExplanationValidationError, match="weighted_coverage_ratio"):
        render_template(
            config,
            "fact_global_context",
            {"dominant_state": "GLOBAL_CONTEXT_MIXED"},
        )


def test_builder_rejects_non_numeric_or_out_of_range_scores() -> None:
    config = load_config()
    global_context, alignment = load_inputs()

    invalid = copy.deepcopy(global_context)
    invalid["category_support"]["TRENDING"] = True
    with pytest.raises(ExplanationValidationError, match="numeric"):
        build_explanation_state(invalid, alignment, config, COMMIT)

    invalid = copy.deepcopy(global_context)
    invalid["aggregate_evidence_score"] = 1.2
    with pytest.raises(ExplanationValidationError, match="within"):
        build_explanation_state(invalid, alignment, config, COMMIT)

    invalid = copy.deepcopy(global_context)
    invalid["conflict_states"] = ["A", "B"]
    with pytest.raises(ExplanationValidationError, match="exactly one"):
        build_explanation_state(invalid, alignment, config, COMMIT)

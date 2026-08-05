from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "src/crypto_quant_bot/market_analysis/explanation_core_and_why_not_trade_layer.py"
MODELS = ROOT / "src/crypto_quant_bot/market_analysis/explanation_core_and_why_not_trade_layer_models.py"
VALIDATION = ROOT / "src/crypto_quant_bot/market_analysis/explanation_core_validation.py"


def replace_between(path: Path, start_marker: str, end_marker: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    path.write_text(text[:start] + replacement.rstrip() + "\n\n" + text[end:], encoding="utf-8")


def refactor_engine() -> None:
    replace_between(
        ENGINE,
        "def _validate_templates(",
        "def _validate_reason_registry(",
        '''def _statement_order(
    config: Mapping[str, Any],
    templates: Mapping[str, Any],
) -> tuple[str, ...]:
    order = config.get("statement_order")
    if not isinstance(order, list) or not order or len(order) != len(set(order)):
        raise ExplanationValidationError("statement_order must be a unique non-empty list")
    if set(order) != set(templates):
        raise ExplanationValidationError("statement_order must reference every template exactly once")
    return tuple(str(template_id) for template_id in order)


def _validate_template(template_id: str, value: object) -> str:
    template = _mapping(value, f"templates.{template_id}")
    if template.get("section") not in SECTIONS:
        raise ExplanationValidationError(f"invalid section for template {template_id}")
    if not isinstance(template.get("text"), str) or not template["text"]:
        raise ExplanationValidationError(f"template text missing for {template_id}")
    reason_code = template.get("reason_code")
    if not isinstance(reason_code, str) or not reason_code:
        raise ExplanationValidationError(f"reason code missing for {template_id}")
    return reason_code


def _validate_templates(config: Mapping[str, Any]) -> None:
    templates = _mapping(config.get("templates"), "templates")
    order = _statement_order(config, templates)
    reason_codes = tuple(_validate_template(template_id, templates[template_id]) for template_id in order)
    if len(reason_codes) != len(set(reason_codes)):
        raise ExplanationValidationError("template reason codes must be unique")
''',
    )
    replace_between(
        ENGINE,
        "def validate_inputs(",
        "def _source_checksum(",
        '''def _validate_input_identity(
    global_context: Mapping[str, Any],
    alignment: Mapping[str, Any],
    schemas: Mapping[str, Any],
) -> None:
    if global_context.get("schema_version") != schemas["global_context"]:
        raise ExplanationValidationError("global context schema mismatch")
    if alignment.get("schema_version") != schemas["multi_timeframe_alignment"]:
        raise ExplanationValidationError("alignment schema mismatch")
    if global_context.get("instrument_id") != alignment.get("instrument_id"):
        raise ExplanationValidationError("input instruments diverge")


def _validate_input_times(
    global_context: Mapping[str, Any],
    alignment: Mapping[str, Any],
) -> None:
    global_time = str(global_context.get("decision_time", ""))
    alignment_time = str(alignment.get("decision_time", ""))
    parse_utc(global_time, "global_context.decision_time")
    parse_utc(alignment_time, "alignment.decision_time")
    if global_time != alignment_time:
        raise ExplanationValidationError("input decision times diverge")


def _validate_input_safety(
    global_context: Mapping[str, Any],
    alignment: Mapping[str, Any],
) -> None:
    false_fields = (
        "used_for_decision",
        "forecast_generation_allowed",
        "probability_claims_allowed",
        "signal_generation_allowed",
        "order_routing_allowed",
        "execution_allowed",
        "trade_allowed",
    )
    if global_context.get("analysis_only") is not True or not _safety_false(global_context, false_fields):
        raise ExplanationValidationError("global context safety invariants failed")
    if alignment.get("analysis_only") is not True or not _safety_false(alignment, false_fields):
        raise ExplanationValidationError("alignment safety invariants failed")
    if global_context.get("approved_size") != 0 or alignment.get("approved_size") != 0:
        raise ExplanationValidationError("approved_size must remain zero")


def _validate_expected_context(
    global_context: Mapping[str, Any],
    alignment: Mapping[str, Any],
) -> None:
    if global_context.get("validation_state") != "VALID":
        raise ExplanationValidationError("global context is not validated")
    if global_context.get("dominant_state") != "GLOBAL_CONTEXT_MIXED":
        raise ExplanationValidationError("template version expects a mixed global context")
    if global_context.get("conflict_states") != ["MTF_DIVERGENT"]:
        raise ExplanationValidationError("template version expects explicit multi-timeframe divergence")
    if alignment.get("alignment_state") != "MTF_DIVERGENT":
        raise ExplanationValidationError("template version expects explicit multi-timeframe divergence")
    if alignment.get("coherence_state") != "MTF_INCOHERENT":
        raise ExplanationValidationError("template version expects incoherent multi-timeframe state")


def validate_inputs(
    global_context: Mapping[str, Any],
    alignment: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    schemas = _mapping(config["required_input_schemas"], "required_input_schemas")
    _validate_input_identity(global_context, alignment, schemas)
    _validate_input_times(global_context, alignment)
    _validate_input_safety(global_context, alignment)
    _validate_expected_context(global_context, alignment)
''',
    )
    replace_between(
        ENGINE,
        "def _evidence_registry(",
        "def _plans(",
        '''def _global_context_evidence(
    global_context: Mapping[str, Any],
    path: str,
    digest: str,
) -> dict[str, EvidenceReferenceV1]:
    support = global_context["category_support"]
    return {
        "global_state": _evidence(path, digest, "/dominant_state", str(global_context["dominant_state"])),
        "global_coverage": _evidence(path, digest, "/weighted_coverage_ratio", float(global_context["weighted_coverage_ratio"])),
        "support_trending": _evidence(path, digest, "/category_support/TRENDING", float(support["TRENDING"])),
        "support_range": _evidence(path, digest, "/category_support/RANGE", float(support["RANGE"])),
        "support_mixed": _evidence(path, digest, "/category_support/MIXED", float(support["MIXED"])),
        "support_conflict": _evidence(path, digest, "/category_support/CONFLICT", float(support["CONFLICT"])),
        "aggregate_score": _evidence(path, digest, "/aggregate_evidence_score", float(global_context["aggregate_evidence_score"])),
        "available_sources": _evidence(path, digest, "/available_source_count", int(global_context["available_source_count"])),
        "confidence_interval": _evidence(path, digest, "/confidence_interval", None),
        "global_conflict": _evidence(path, digest, "/conflict_states/0", str(global_context["conflict_states"][0])),
    }


def _global_permission_evidence(
    global_context: Mapping[str, Any],
    path: str,
    digest: str,
) -> dict[str, EvidenceReferenceV1]:
    return {
        "global_analysis_only": _evidence(path, digest, "/analysis_only", True),
        "global_used_for_decision": _evidence(path, digest, "/used_for_decision", False),
        "global_signal_permission": _evidence(path, digest, "/signal_generation_allowed", False),
        "global_order_permission": _evidence(path, digest, "/order_routing_allowed", False),
        "global_execution_permission": _evidence(path, digest, "/execution_allowed", False),
    }


def _alignment_evidence(
    alignment: Mapping[str, Any],
    path: str,
    digest: str,
) -> dict[str, EvidenceReferenceV1]:
    return {
        "alignment_state": _evidence(path, digest, "/alignment_state", str(alignment["alignment_state"])),
        "alignment_coherence": _evidence(path, digest, "/coherence_state", str(alignment["coherence_state"])),
        "alignment_divergence": _evidence(path, digest, "/divergence_state", str(alignment["divergence_state"])),
    }


def _evidence_registry(
    global_context: Mapping[str, Any],
    alignment: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, EvidenceReferenceV1]:
    artifacts = _mapping(config["input_artifacts"], "input_artifacts")
    global_path = str(artifacts["global_context"])
    alignment_path = str(artifacts["multi_timeframe_alignment"])
    global_digest = _source_checksum(global_context)
    alignment_digest = _source_checksum(alignment)
    return {
        **_global_context_evidence(global_context, global_path, global_digest),
        **_global_permission_evidence(global_context, global_path, global_digest),
        **_alignment_evidence(alignment, alignment_path, alignment_digest),
    }
''',
    )
    replace_between(
        ENGINE,
        "def _plans(",
        "def _why_reason(",
        '''def _context_plans(
    values: Mapping[str, str],
    refs: Mapping[str, EvidenceReferenceV1],
) -> tuple[StatementPlan, ...]:
    return (
        StatementPlan(
            "fact_global_context",
            {"dominant_state": values["dominant_state"], "weighted_coverage_ratio": values["weighted_coverage_ratio"]},
            (refs["global_state"], refs["global_coverage"]),
        ),
        StatementPlan(
            "fact_category_support",
            {
                "trending_support": values["trending_support"],
                "range_support": values["range_support"],
                "mixed_support": values["mixed_support"],
                "conflict_support": values["conflict_support"],
            },
            (refs["support_trending"], refs["support_range"], refs["support_mixed"], refs["support_conflict"]),
        ),
        StatementPlan(
            "fact_alignment",
            {"alignment_state": values["alignment_state"], "coherence_state": values["coherence_state"]},
            (refs["alignment_state"], refs["alignment_coherence"]),
        ),
        StatementPlan(
            "feature_aggregate_score",
            {"aggregate_evidence_score": values["aggregate_evidence_score"]},
            (refs["aggregate_score"], refs["confidence_interval"]),
        ),
        StatementPlan(
            "inference_explicit_conflict",
            {"conflict_state": values["conflict_state"]},
            (refs["global_conflict"], refs["alignment_divergence"]),
        ),
    )


def _evidence_plans(
    values: Mapping[str, str],
    refs: Mapping[str, EvidenceReferenceV1],
) -> tuple[StatementPlan, ...]:
    return (
        StatementPlan(
            "support_validated_sources",
            {"available_source_count": values["available_source_count"]},
            (refs["available_sources"], refs["global_coverage"]),
        ),
        StatementPlan(
            "contradiction_trend_range",
            {
                "trending_support": values["trending_support"],
                "range_support": values["range_support"],
                "conflict_support": values["conflict_support"],
            },
            (refs["support_trending"], refs["support_range"], refs["support_conflict"]),
        ),
        StatementPlan("uncertainty_uncalibrated", {}, (refs["confidence_interval"],)),
    )


def _governance_plans(refs: Mapping[str, EvidenceReferenceV1]) -> tuple[StatementPlan, ...]:
    return (
        StatementPlan("rule_offline_only", {}, (refs["global_analysis_only"],)),
        StatementPlan("veto_context_mixed", {}, (refs["global_state"],)),
        StatementPlan(
            "veto_mtf_divergence",
            {},
            (refs["global_conflict"], refs["alignment_state"], refs["alignment_divergence"]),
        ),
        StatementPlan(
            "veto_permissions_disabled",
            {},
            (refs["global_used_for_decision"], refs["global_signal_permission"], refs["global_order_permission"], refs["global_execution_permission"]),
        ),
        StatementPlan(
            "non_applicable_future_capabilities",
            {},
            (refs["global_used_for_decision"], refs["global_signal_permission"], refs["global_order_permission"]),
        ),
        StatementPlan(
            "final_no_executable_action",
            {},
            (refs["global_used_for_decision"], refs["global_execution_permission"]),
        ),
    )


def _plans(values: Mapping[str, str], refs: Mapping[str, EvidenceReferenceV1]) -> tuple[StatementPlan, ...]:
    return _context_plans(values, refs) + _evidence_plans(values, refs) + _governance_plans(refs)
''',
    )


def refactor_validation() -> None:
    replace_between(
        VALIDATION,
        "def validate_statements(",
        "def validate_reason_set(",
        '''def _statement_definition(
    statement: Mapping[str, Any],
    templates: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any]]:
    template_id = str(statement["template_id"])
    if template_id not in templates:
        raise ExplanationEvidenceError(f"unknown statement template: {template_id}")
    return template_id, mapping(templates[template_id], f"templates.{template_id}")


def _validate_statement_contract(
    statement: Mapping[str, Any],
    template_id: str,
    template: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    if statement["section"] != template["section"]:
        raise ExplanationEvidenceError(f"statement section diverges: {template_id}")
    if statement["reason_code"] != template["reason_code"]:
        raise ExplanationEvidenceError(f"statement reason code diverges: {template_id}")
    parameters = mapping(statement["parameters"], "parameters")
    rendered = render_template(config, template_id, {str(key): str(value) for key, value in parameters.items()})
    if statement["text"] != rendered:
        raise ExplanationEvidenceError(f"statement text diverges from template: {template_id}")


def _validate_reference_list(
    refs: object,
    sources: Mapping[str, Mapping[str, Any]],
    missing_message: str,
) -> None:
    if not isinstance(refs, list) or not refs:
        raise ExplanationEvidenceError(missing_message)
    for reference in refs:
        validate_evidence_ref(mapping(reference, "evidence"), sources)


def validate_statements(
    bundle: Mapping[str, Any],
    config: Mapping[str, Any],
    sources: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    templates = mapping(config["templates"], "templates")
    statements = iter_statements(bundle)
    identifiers = [str(item["statement_id"]) for item in statements]
    if len(identifiers) != len(set(identifiers)):
        raise ExplanationEvidenceError("duplicate explanation statement ID")
    if len(statements) != len(templates):
        raise ExplanationEvidenceError("statement count does not match template registry")
    codes: list[str] = []
    for statement in statements:
        template_id, template = _statement_definition(statement, templates)
        _validate_statement_contract(statement, template_id, template, config)
        _validate_reference_list(
            statement["evidence_refs"],
            sources,
            f"reason code has no source evidence: {statement['reason_code']}",
        )
        codes.append(str(statement["reason_code"]))
    return tuple(codes)
''',
    )
    replace_between(
        VALIDATION,
        "def validate_reason_set(",
        "def validate_safety(",
        '''def _validate_reason_definition(
    reason: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> str:
    code = str(reason["reason_code"])
    if code not in registry:
        raise ExplanationEvidenceError(f"unknown reason code: {code}")
    definition = mapping(registry[code], f"why_not_trade_reasons.{code}")
    fields = ("owner", "condition_not_satisfied", "required_value", "reconsideration_condition")
    if any(reason[field] != definition[field] for field in fields):
        raise ExplanationEvidenceError(f"reason diverges from config: {code}")
    if reason["order_intent_created"] is not False:
        raise ExplanationEvidenceError("reason claims an order intent")
    return code


def _validate_reason_codes(codes: list[str], registry: Mapping[str, Any]) -> None:
    if len(codes) != len(set(codes)) or set(codes) != set(registry):
        raise ExplanationEvidenceError("reason codes are incomplete or duplicated")


def _validate_reason_set_summary(
    reason_set: Mapping[str, Any],
    bundle: Mapping[str, Any],
) -> None:
    if reason_set["dominant_reason_code"] != "WNT_PERMISSIONS_DISABLED":
        raise ExplanationEvidenceError("unexpected dominant reason")
    if reason_set["no_order_intent_created"] is not True:
        raise ExplanationEvidenceError("reason set must prove no order intent")
    final_items = bundle["final_consequence"]
    if not isinstance(final_items, list) or len(final_items) != 1:
        raise ExplanationEvidenceError("final consequence must contain one statement")
    if reason_set["final_consequence"] != final_items[0]["text"]:
        raise ExplanationEvidenceError("reason-set consequence diverges from bundle")


def validate_reason_set(
    bundle: Mapping[str, Any],
    config: Mapping[str, Any],
    sources: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    reason_set = mapping(bundle["why_not_trade"], "why_not_trade")
    registry = mapping(config["why_not_trade_reasons"], "why_not_trade_reasons")
    reasons = reason_set["reasons"]
    if not isinstance(reasons, list) or len(reasons) != len(registry):
        raise ExplanationEvidenceError("reason count mismatch")
    codes: list[str] = []
    for reason_value in reasons:
        reason = mapping(reason_value, "reason")
        code = _validate_reason_definition(reason, registry)
        _validate_reference_list(reason["evidence_refs"], sources, f"reason has no source evidence: {code}")
        codes.append(code)
    _validate_reason_codes(codes, registry)
    _validate_reason_set_summary(reason_set, bundle)
    return tuple(codes)
''',
    )


def refactor_models() -> None:
    text = MODELS.read_text(encoding="utf-8")
    text = text.replace("from datetime import UTC, datetime\n", "")
    import_marker = "from typing import Any\n"
    shared_import = (
        "from typing import Any\n\n"
        "from crypto_quant_bot.market_analysis.global_market_context_aggregator_models import (\n"
        "    parse_utc,\n"
        "    require_unique,\n"
        ")\n"
    )
    if shared_import not in text:
        text = text.replace(import_marker, shared_import, 1)
    start = text.index("def require_unique(")
    end = text.index("def _validate_scalar(", start)
    require_text_block = text[text.index("def require_text("):start]
    text = text[: text.index("def require_text(")] + require_text_block + text[end:]
    MODELS.write_text(text, encoding="utf-8")


def main() -> int:
    refactor_engine()
    refactor_validation()
    refactor_models()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

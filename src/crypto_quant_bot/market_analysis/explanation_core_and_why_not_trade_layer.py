from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer_models import (
    SECTIONS,
    EvidenceReferenceV1,
    ExplanationBundleV1,
    ExplanationCoreWhyNotTradeLayerStateV1,
    ExplanationStatementV1,
    WhyNotTradeReasonSetV1,
    WhyNotTradeReasonV1,
    parse_utc,
)


class ExplanationValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StatementPlan:
    template_id: str
    parameters: dict[str, str]
    evidence_refs: tuple[EvidenceReferenceV1, ...]


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def checksum(payload: object) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def stable_id(prefix: str, payload: object) -> str:
    return str(uuid5(NAMESPACE_URL, f"lot28:{prefix}:{checksum(payload)}"))


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExplanationValidationError(f"{field_name} must be an object")
    return value


def _statement_order(
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

def _validate_reason_registry(config: Mapping[str, Any]) -> None:
    registry = _mapping(config.get("why_not_trade_reasons"), "why_not_trade_reasons")
    required = {"WNT_CONTEXT_MIXED", "WNT_MTF_DIVERGENCE", "WNT_PERMISSIONS_DISABLED"}
    if set(registry) != required:
        raise ExplanationValidationError("why-not reason registry is incomplete")
    for reason_code, payload in registry.items():
        item = _mapping(payload, f"why_not_trade_reasons.{reason_code}")
        for field in ("owner", "condition_not_satisfied", "required_value", "reconsideration_condition"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise ExplanationValidationError(f"{reason_code}.{field} must be non-empty")


def _validate_restrictions(config: Mapping[str, Any]) -> None:
    restrictions = _mapping(config.get("promotion_restrictions"), "promotion_restrictions")
    if not restrictions or any(value is not False for value in restrictions.values()):
        raise ExplanationValidationError("all explanation-layer permissions must remain false")
    forbidden = config.get("forbidden_output_tokens")
    if not isinstance(forbidden, list) or set(forbidden) != {"BUY", "SELL", "position_size"}:
        raise ExplanationValidationError("forbidden output token registry is invalid")


def validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != "explanation-core-why-not-trade-config-v1":
        raise ExplanationValidationError("unsupported Lot 28 config schema")
    _validate_templates(config)
    _validate_reason_registry(config)
    _validate_restrictions(config)
    artifacts = _mapping(config.get("input_artifacts"), "input_artifacts")
    schemas = _mapping(config.get("required_input_schemas"), "required_input_schemas")
    if set(artifacts) != {"global_context", "multi_timeframe_alignment"} or set(schemas) != set(artifacts):
        raise ExplanationValidationError("Lot 28 input registry is invalid")


def _safety_false(payload: Mapping[str, Any], fields: tuple[str, ...]) -> bool:
    return all(payload.get(field) is False for field in fields)


def _validate_input_identity(
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

def _source_checksum(payload: Mapping[str, Any]) -> str:
    return checksum(payload)


def _evidence(
    artifact_path: str,
    artifact_checksum: str,
    json_pointer: str,
    observed_value: str | int | float | bool | None,
) -> EvidenceReferenceV1:
    return EvidenceReferenceV1(
        artifact_path=artifact_path,
        artifact_checksum=artifact_checksum,
        json_pointer=json_pointer,
        observed_value=observed_value,
    )


def _format_score(value: object, field_name: str) -> str:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ExplanationValidationError(f"{field_name} must be numeric")
    numeric = float(value)
    if not 0.0 <= numeric <= 1.0:
        raise ExplanationValidationError(f"{field_name} must be within [0, 1]")
    return f"{numeric:.6f}"


def _template(config: Mapping[str, Any], template_id: str) -> Mapping[str, Any]:
    templates = _mapping(config["templates"], "templates")
    if template_id not in templates:
        raise ExplanationValidationError(f"unknown template: {template_id}")
    return _mapping(templates[template_id], f"templates.{template_id}")


def render_template(config: Mapping[str, Any], template_id: str, parameters: Mapping[str, str]) -> str:
    template = _template(config, template_id)
    try:
        return str(template["text"]).format_map(dict(parameters))
    except KeyError as exc:
        raise ExplanationValidationError(f"missing template parameter: {exc.args[0]}") from exc


def _statement(config: Mapping[str, Any], plan: StatementPlan) -> ExplanationStatementV1:
    template = _template(config, plan.template_id)
    text = render_template(config, plan.template_id, plan.parameters)
    identity = {
        "template_id": plan.template_id,
        "parameters": plan.parameters,
        "evidence_refs": [item.to_dict() for item in plan.evidence_refs],
    }
    return ExplanationStatementV1(
        statement_id=stable_id("statement", identity),
        section=str(template["section"]),
        reason_code=str(template["reason_code"]),
        template_id=plan.template_id,
        text=text,
        parameters=plan.parameters,
        evidence_refs=plan.evidence_refs,
    )


def _shared_values(global_context: Mapping[str, Any], alignment: Mapping[str, Any]) -> dict[str, str]:
    support = _mapping(global_context.get("category_support"), "category_support")
    conflicts = global_context.get("conflict_states")
    if not isinstance(conflicts, list) or len(conflicts) != 1:
        raise ExplanationValidationError("exactly one global conflict is required")
    return {
        "dominant_state": str(global_context["dominant_state"]),
        "weighted_coverage_ratio": _format_score(global_context["weighted_coverage_ratio"], "weighted_coverage_ratio"),
        "trending_support": _format_score(support["TRENDING"], "TRENDING support"),
        "range_support": _format_score(support["RANGE"], "RANGE support"),
        "mixed_support": _format_score(support["MIXED"], "MIXED support"),
        "conflict_support": _format_score(support["CONFLICT"], "CONFLICT support"),
        "alignment_state": str(alignment["alignment_state"]),
        "coherence_state": str(alignment["coherence_state"]),
        "aggregate_evidence_score": _format_score(
            global_context["aggregate_evidence_score"],
            "aggregate_evidence_score",
        ),
        "conflict_state": str(conflicts[0]),
        "available_source_count": str(global_context["available_source_count"]),
    }


def _global_context_evidence(
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

def _context_plans(
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

def _why_reason(
    config: Mapping[str, Any],
    reason_code: str,
    observed_value: str,
    evidence_refs: tuple[EvidenceReferenceV1, ...],
) -> WhyNotTradeReasonV1:
    registry = _mapping(config["why_not_trade_reasons"], "why_not_trade_reasons")
    definition = _mapping(registry[reason_code], f"why_not_trade_reasons.{reason_code}")
    identity = {
        "reason_code": reason_code,
        "observed_value": observed_value,
        "evidence_refs": [item.to_dict() for item in evidence_refs],
    }
    return WhyNotTradeReasonV1(
        reason_id=stable_id("why-not", identity),
        reason_code=reason_code,
        owner=str(definition["owner"]),
        condition_not_satisfied=str(definition["condition_not_satisfied"]),
        observed_value=observed_value,
        required_value=str(definition["required_value"]),
        expiry=None,
        reconsideration_condition=str(definition["reconsideration_condition"]),
        evidence_refs=evidence_refs,
    )


def _why_not_reason_set(
    config: Mapping[str, Any],
    refs: Mapping[str, EvidenceReferenceV1],
    final_text: str,
) -> WhyNotTradeReasonSetV1:
    reasons = (
        _why_reason(config, "WNT_CONTEXT_MIXED", "GLOBAL_CONTEXT_MIXED", (refs["global_state"],)),
        _why_reason(
            config,
            "WNT_MTF_DIVERGENCE",
            "MTF_DIVERGENT",
            (refs["global_conflict"], refs["alignment_state"], refs["alignment_divergence"]),
        ),
        _why_reason(
            config,
            "WNT_PERMISSIONS_DISABLED",
            "decision=false;signal=false;routing=false;execution=false",
            (
                refs["global_used_for_decision"],
                refs["global_signal_permission"],
                refs["global_order_permission"],
                refs["global_execution_permission"],
            ),
        ),
    )
    identity = [item.to_dict() for item in reasons]
    return WhyNotTradeReasonSetV1(
        reason_set_id=stable_id("why-not-set", identity),
        reasons=reasons,
        dominant_reason_code="WNT_PERMISSIONS_DISABLED",
        final_consequence=final_text,
    )


def _bundle(statements: tuple[ExplanationStatementV1, ...], reason_set: WhyNotTradeReasonSetV1) -> ExplanationBundleV1:
    grouped = {section: tuple(item for item in statements if item.section == section) for section in SECTIONS}
    return ExplanationBundleV1(
        facts_observed=grouped["facts_observed"],
        features_computed=grouped["features_computed"],
        inferences=grouped["inferences"],
        assumptions=grouped["assumptions"],
        supporting_evidence=grouped["supporting_evidence"],
        contradicting_evidence=grouped["contradicting_evidence"],
        uncertainty=grouped["uncertainty"],
        rules_triggered=grouped["rules_triggered"],
        vetos_triggered=grouped["vetos_triggered"],
        non_applicable=grouped["non_applicable"],
        final_consequence=grouped["final_consequence"],
        why_not_trade=reason_set,
    )


def _assert_forbidden_tokens_absent(payload: object, config: Mapping[str, Any]) -> None:
    serialized = canonical_json(payload)
    forbidden = config["forbidden_output_tokens"]
    for token in forbidden:
        if str(token) in serialized:
            raise ExplanationValidationError(f"forbidden output token detected: {token}")


def build_explanation_state(
    global_context: Mapping[str, Any],
    alignment: Mapping[str, Any],
    config: Mapping[str, Any],
    code_commit: str,
) -> ExplanationCoreWhyNotTradeLayerStateV1:
    validate_config(config)
    validate_inputs(global_context, alignment, config)
    values = _shared_values(global_context, alignment)
    refs = _evidence_registry(global_context, alignment, config)
    statements = tuple(_statement(config, plan) for plan in _plans(values, refs))
    final_statement = next(item for item in statements if item.section == "final_consequence")
    reason_set = _why_not_reason_set(config, refs, final_statement.text)
    bundle = _bundle(statements, reason_set)
    input_checksums = {
        "global_context": _source_checksum(global_context),
        "multi_timeframe_alignment": _source_checksum(alignment),
    }
    identity = {
        "decision_time": global_context["decision_time"],
        "global_context_id": global_context["context_id"],
        "alignment_id": alignment["alignment_id"],
        "bundle": bundle.to_dict(),
        "config_checksum": checksum(config),
        "code_commit": code_commit,
    }
    reason_codes = tuple(item.reason_code for item in statements) + tuple(
        item.reason_code for item in reason_set.reasons
    )
    provisional = ExplanationCoreWhyNotTradeLayerStateV1(
        explanation_id=stable_id("explanation", identity),
        instrument_id=str(global_context["instrument_id"]),
        decision_time=str(global_context["decision_time"]),
        global_context_id=str(global_context["context_id"]),
        alignment_id=str(alignment["alignment_id"]),
        bundle=bundle,
        lineage_id=stable_id("lineage", identity),
        config_version=str(config["config_id"]),
        config_checksum=checksum(config),
        code_commit=code_commit,
        input_checksums=input_checksums,
        output_checksum="pending",
        reason_codes=reason_codes,
        validation_state="VALID",
    )
    payload = provisional.to_dict()
    payload.pop("output_checksum")
    state = replace(provisional, output_checksum=checksum(payload))
    _assert_forbidden_tokens_absent(state.to_dict(), config)
    return state


def replay_matches(
    first: ExplanationCoreWhyNotTradeLayerStateV1,
    second: ExplanationCoreWhyNotTradeLayerStateV1,
) -> bool:
    return first.to_dict() == second.to_dict() and first.output_checksum == second.output_checksum

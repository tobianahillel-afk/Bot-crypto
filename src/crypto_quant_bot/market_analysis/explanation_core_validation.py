from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer import (
    canonical_json,
    checksum,
    render_template,
)


class ExplanationEvidenceError(ValueError):
    pass


def mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExplanationEvidenceError(f"{field_name} must be an object")
    return value


def resolve_pointer(payload: object, pointer: str) -> object:
    if not pointer.startswith("/"):
        raise ExplanationEvidenceError("evidence JSON pointer must be absolute")
    current = payload
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if part not in current:
                raise ExplanationEvidenceError(f"evidence pointer field missing: {pointer}")
            current = current[part]
            continue
        if isinstance(current, list):
            if not part.isdigit() or int(part) >= len(current):
                raise ExplanationEvidenceError(f"evidence pointer index invalid: {pointer}")
            current = current[int(part)]
            continue
        raise ExplanationEvidenceError(f"evidence pointer traverses scalar: {pointer}")
    return current


def validate_evidence_ref(
    reference: Mapping[str, Any],
    sources: Mapping[str, Mapping[str, Any]],
) -> None:
    path = str(reference["artifact_path"])
    if path not in sources:
        raise ExplanationEvidenceError(f"evidence references an unregistered artifact: {path}")
    source = sources[path]
    if reference["artifact_checksum"] != checksum(source):
        raise ExplanationEvidenceError(f"evidence artifact checksum mismatch: {path}")
    observed = resolve_pointer(source, str(reference["json_pointer"]))
    if observed != reference["observed_value"]:
        raise ExplanationEvidenceError(f"evidence observed value mismatch: {reference['json_pointer']}")


def iter_statements(bundle: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    statements: list[Mapping[str, Any]] = []
    for section, value in bundle.items():
        if section in {"schema_version", "why_not_trade"}:
            continue
        if not isinstance(value, list):
            raise ExplanationEvidenceError(f"invalid statement section: {section}")
        statements.extend(mapping(item, "statement") for item in value)
    return statements


def _statement_definition(
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

def _validate_reason_definition(
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

def validate_safety(state: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    if state.get("analysis_only") is not True or state.get("approved_size") != 0:
        raise ExplanationEvidenceError("explanation safety state is invalid")
    restrictions = mapping(config["promotion_restrictions"], "promotion_restrictions")
    for field, expected in restrictions.items():
        if state.get(field) is not expected:
            raise ExplanationEvidenceError(f"permission mismatch: {field}")
    serialized = canonical_json(state)
    for token in config["forbidden_output_tokens"]:
        if str(token) in serialized:
            raise ExplanationEvidenceError(f"forbidden output token detected: {token}")

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from crypto_quant_bot.market_analysis.global_market_context_aggregator_models import (
    parse_utc,
    require_unique,
)

SECTIONS = {
    "facts_observed",
    "features_computed",
    "inferences",
    "assumptions",
    "supporting_evidence",
    "contradicting_evidence",
    "uncertainty",
    "rules_triggered",
    "vetos_triggered",
    "non_applicable",
    "final_consequence",
}
VALIDATION_STATES = {"VALID", "UNKNOWN", "BLOCKED"}


def require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _validate_scalar(value: object, field_name: str) -> None:
    if value is not None and not isinstance(value, str | int | float | bool):
        raise ValueError(f"{field_name} must be a JSON scalar")


@dataclass(frozen=True, slots=True)
class EvidenceReferenceV1:
    artifact_path: str
    artifact_checksum: str
    json_pointer: str
    observed_value: str | int | float | bool | None
    schema_version: str = "explanation-evidence-reference-v1"

    def __post_init__(self) -> None:
        require_text(self.artifact_path, "artifact_path")
        require_text(self.artifact_checksum, "artifact_checksum")
        require_text(self.json_pointer, "json_pointer")
        if len(self.artifact_checksum) != 64:
            raise ValueError("artifact_checksum must be a SHA-256 hex digest")
        _validate_scalar(self.observed_value, "observed_value")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExplanationStatementV1:
    statement_id: str
    section: str
    reason_code: str
    template_id: str
    text: str
    parameters: dict[str, str]
    evidence_refs: tuple[EvidenceReferenceV1, ...]
    schema_version: str = "explanation-statement-v1"

    def __post_init__(self) -> None:
        for field_name in ("statement_id", "reason_code", "template_id", "text"):
            require_text(getattr(self, field_name), field_name)
        if self.section not in SECTIONS:
            raise ValueError("unknown explanation section")
        if not self.evidence_refs:
            raise ValueError("every statement must contain source evidence")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in self.parameters.items()):
            raise ValueError("statement parameters must be string pairs")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = [item.to_dict() for item in self.evidence_refs]
        return payload


@dataclass(frozen=True, slots=True)
class WhyNotTradeReasonV1:
    reason_id: str
    reason_code: str
    owner: str
    condition_not_satisfied: str
    observed_value: str
    required_value: str
    expiry: str | None
    reconsideration_condition: str
    evidence_refs: tuple[EvidenceReferenceV1, ...]
    order_intent_created: bool = False
    schema_version: str = "why-not-trade-reason-v1"

    def __post_init__(self) -> None:
        for field_name in (
            "reason_id",
            "reason_code",
            "owner",
            "condition_not_satisfied",
            "observed_value",
            "required_value",
            "reconsideration_condition",
        ):
            require_text(getattr(self, field_name), field_name)
        if self.expiry is not None:
            parse_utc(self.expiry, "expiry")
        if not self.evidence_refs:
            raise ValueError("why-not reason must contain source evidence")
        if self.order_intent_created is not False:
            raise ValueError("order_intent_created must remain false")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = [item.to_dict() for item in self.evidence_refs]
        return payload


@dataclass(frozen=True, slots=True)
class WhyNotTradeReasonSetV1:
    reason_set_id: str
    reasons: tuple[WhyNotTradeReasonV1, ...]
    dominant_reason_code: str
    final_consequence: str
    no_order_intent_created: bool = True
    schema_version: str = "why-not-trade-reason-set-v1"

    def __post_init__(self) -> None:
        require_text(self.reason_set_id, "reason_set_id")
        require_text(self.dominant_reason_code, "dominant_reason_code")
        require_text(self.final_consequence, "final_consequence")
        if not self.reasons:
            raise ValueError("why-not reason set must not be empty")
        codes = tuple(item.reason_code for item in self.reasons)
        require_unique(codes, "why-not reason codes")
        if self.dominant_reason_code not in codes:
            raise ValueError("dominant reason must belong to the reason set")
        if self.no_order_intent_created is not True:
            raise ValueError("no_order_intent_created must remain true")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = [item.to_dict() for item in self.reasons]
        return payload


@dataclass(frozen=True, slots=True)
class ExplanationBundleV1:
    facts_observed: tuple[ExplanationStatementV1, ...]
    features_computed: tuple[ExplanationStatementV1, ...]
    inferences: tuple[ExplanationStatementV1, ...]
    assumptions: tuple[ExplanationStatementV1, ...]
    supporting_evidence: tuple[ExplanationStatementV1, ...]
    contradicting_evidence: tuple[ExplanationStatementV1, ...]
    uncertainty: tuple[ExplanationStatementV1, ...]
    rules_triggered: tuple[ExplanationStatementV1, ...]
    vetos_triggered: tuple[ExplanationStatementV1, ...]
    non_applicable: tuple[ExplanationStatementV1, ...]
    final_consequence: tuple[ExplanationStatementV1, ...]
    why_not_trade: WhyNotTradeReasonSetV1
    schema_version: str = "explanation-bundle-v1"

    def __post_init__(self) -> None:
        expected_sections = (
            "facts_observed",
            "features_computed",
            "inferences",
            "assumptions",
            "supporting_evidence",
            "contradicting_evidence",
            "uncertainty",
            "rules_triggered",
            "vetos_triggered",
            "non_applicable",
            "final_consequence",
        )
        statement_ids: list[str] = []
        for section in expected_sections:
            statements = getattr(self, section)
            if any(item.section != section for item in statements):
                raise ValueError(f"statement stored in the wrong section: {section}")
            statement_ids.extend(item.statement_id for item in statements)
        require_unique(tuple(statement_ids), "statement_ids")
        required_non_empty = (
            self.facts_observed,
            self.features_computed,
            self.inferences,
            self.supporting_evidence,
            self.contradicting_evidence,
            self.uncertainty,
            self.rules_triggered,
            self.vetos_triggered,
            self.non_applicable,
            self.final_consequence,
        )
        if any(not section for section in required_non_empty):
            raise ValueError("required explanation sections must not be empty")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"schema_version": self.schema_version}
        for section in (
            "facts_observed",
            "features_computed",
            "inferences",
            "assumptions",
            "supporting_evidence",
            "contradicting_evidence",
            "uncertainty",
            "rules_triggered",
            "vetos_triggered",
            "non_applicable",
            "final_consequence",
        ):
            payload[section] = [item.to_dict() for item in getattr(self, section)]
        payload["why_not_trade"] = self.why_not_trade.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class ExplanationCoreWhyNotTradeLayerStateV1:
    explanation_id: str
    instrument_id: str
    decision_time: str
    global_context_id: str
    alignment_id: str
    bundle: ExplanationBundleV1
    lineage_id: str
    config_version: str
    config_checksum: str
    code_commit: str
    input_checksums: dict[str, str]
    output_checksum: str
    reason_codes: tuple[str, ...]
    validation_state: str
    analysis_only: bool = True
    used_for_decision: bool = False
    forecast_generation_allowed: bool = False
    probability_claims_allowed: bool = False
    signal_generation_allowed: bool = False
    risk_approval_allowed: bool = False
    order_routing_allowed: bool = False
    execution_allowed: bool = False
    trade_allowed: bool = False
    approved_size: int = 0
    schema_version: str = "explanation-core-why-not-trade-layer-state-v1"

    def __post_init__(self) -> None:
        for field_name in (
            "explanation_id",
            "instrument_id",
            "global_context_id",
            "alignment_id",
            "lineage_id",
            "config_version",
            "config_checksum",
            "code_commit",
            "output_checksum",
        ):
            require_text(getattr(self, field_name), field_name)
        parse_utc(self.decision_time, "decision_time")
        object.__setattr__(self, "reason_codes", tuple(dict.fromkeys(self.reason_codes)))
        if self.validation_state not in VALIDATION_STATES:
            raise ValueError("unknown validation_state")
        require_unique(self.reason_codes, "reason_codes")
        if not self.input_checksums or any(len(value) != 64 for value in self.input_checksums.values()):
            raise ValueError("input_checksums must contain SHA-256 digests")
        permissions = (
            self.used_for_decision,
            self.forecast_generation_allowed,
            self.probability_claims_allowed,
            self.signal_generation_allowed,
            self.risk_approval_allowed,
            self.order_routing_allowed,
            self.execution_allowed,
            self.trade_allowed,
        )
        if self.analysis_only is not True or any(value is not False for value in permissions):
            raise ValueError("all executable permissions must remain disabled")
        if self.approved_size != 0:
            raise ValueError("approved_size must remain zero")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["bundle"] = self.bundle.to_dict()
        payload["reason_codes"] = list(self.reason_codes)
        return payload

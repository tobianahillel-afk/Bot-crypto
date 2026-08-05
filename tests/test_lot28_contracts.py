from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer_models import (
    EvidenceReferenceV1,
    ExplanationBundleV1,
    ExplanationCoreWhyNotTradeLayerStateV1,
    ExplanationStatementV1,
    WhyNotTradeReasonSetV1,
    WhyNotTradeReasonV1,
)


def evidence() -> EvidenceReferenceV1:
    return EvidenceReferenceV1(
        artifact_path="data/audit/source.json",
        artifact_checksum="a" * 64,
        json_pointer="/state",
        observed_value="MIXED",
    )


def statement(section: str = "facts_observed", reason_code: str = "FACT") -> ExplanationStatementV1:
    return ExplanationStatementV1(
        statement_id=f"statement-{section}-{reason_code}",
        section=section,
        reason_code=reason_code,
        template_id=f"template-{reason_code}",
        text="Deterministic text.",
        parameters={},
        evidence_refs=(evidence(),),
    )


def reason(code: str = "WNT_CONTEXT_MIXED") -> WhyNotTradeReasonV1:
    return WhyNotTradeReasonV1(
        reason_id=f"reason-{code}",
        reason_code=code,
        owner="MarketAnalysisDomain",
        condition_not_satisfied="condition",
        observed_value="observed",
        required_value="required",
        expiry=None,
        reconsideration_condition="A future validated gate is required.",
        evidence_refs=(evidence(),),
    )


def reason_set() -> WhyNotTradeReasonSetV1:
    reasons = (
        reason("WNT_CONTEXT_MIXED"),
        reason("WNT_MTF_DIVERGENCE"),
        reason("WNT_PERMISSIONS_DISABLED"),
    )
    return WhyNotTradeReasonSetV1(
        reason_set_id="reason-set",
        reasons=reasons,
        dominant_reason_code="WNT_PERMISSIONS_DISABLED",
        final_consequence="No executable action is produced.",
    )


def bundle() -> ExplanationBundleV1:
    return ExplanationBundleV1(
        facts_observed=(statement("facts_observed", "FACT"),),
        features_computed=(statement("features_computed", "FEATURE"),),
        inferences=(statement("inferences", "INFERENCE"),),
        assumptions=(),
        supporting_evidence=(statement("supporting_evidence", "SUPPORT"),),
        contradicting_evidence=(statement("contradicting_evidence", "CONTRADICTION"),),
        uncertainty=(statement("uncertainty", "UNCERTAINTY"),),
        rules_triggered=(statement("rules_triggered", "RULE"),),
        vetos_triggered=(statement("vetos_triggered", "VETO"),),
        non_applicable=(statement("non_applicable", "NA"),),
        final_consequence=(statement("final_consequence", "FINAL"),),
        why_not_trade=reason_set(),
    )


def test_evidence_reference_is_immutable_and_scalar_only() -> None:
    item = evidence()
    assert item.to_dict()["json_pointer"] == "/state"
    with pytest.raises(FrozenInstanceError):
        item.observed_value = "OTHER"  # type: ignore[misc]
    with pytest.raises(ValueError, match="SHA-256"):
        replace(item, artifact_checksum="short")
    with pytest.raises(ValueError, match="JSON scalar"):
        replace(item, observed_value={"nested": True})  # type: ignore[arg-type]


def test_statement_requires_known_section_and_evidence() -> None:
    with pytest.raises(ValueError, match="unknown"):
        replace(statement(), section="unknown")
    with pytest.raises(ValueError, match="source evidence"):
        replace(statement(), evidence_refs=())
    with pytest.raises(ValueError, match="string pairs"):
        replace(statement(), parameters={"value": 1})  # type: ignore[arg-type]


def test_reason_requires_evidence_and_proves_no_order_intent() -> None:
    with pytest.raises(ValueError, match="source evidence"):
        replace(reason(), evidence_refs=())
    with pytest.raises(ValueError, match="remain false"):
        replace(reason(), order_intent_created=True)
    with pytest.raises(ValueError, match="UTC"):
        replace(reason(), expiry="2026-05-25T03:00:00")


def test_reason_set_rejects_duplicates_and_unknown_dominant_reason() -> None:
    current = reason_set()
    duplicated = (current.reasons[0], current.reasons[0], current.reasons[2])
    with pytest.raises(ValueError, match="duplicates"):
        replace(current, reasons=duplicated)
    with pytest.raises(ValueError, match="belong"):
        replace(current, dominant_reason_code="UNKNOWN")
    with pytest.raises(ValueError, match="remain true"):
        replace(current, no_order_intent_created=False)


def test_bundle_rejects_wrong_section_and_missing_required_section() -> None:
    current = bundle()
    with pytest.raises(ValueError, match="wrong section"):
        replace(current, facts_observed=(statement("inferences", "WRONG"),))
    with pytest.raises(ValueError, match="must not be empty"):
        replace(current, uncertainty=())


def test_state_rejects_permission_escalation_and_bad_checksum_registry() -> None:
    current = ExplanationCoreWhyNotTradeLayerStateV1(
        explanation_id="explanation",
        instrument_id="BTC/EUR",
        decision_time="2026-05-25T03:00:00Z",
        global_context_id="context",
        alignment_id="alignment",
        bundle=bundle(),
        lineage_id="lineage",
        config_version="config",
        config_checksum="a" * 64,
        code_commit="abcdef1",
        input_checksums={"global": "b" * 64},
        output_checksum="c" * 64,
        reason_codes=("FACT",),
        validation_state="VALID",
    )
    with pytest.raises(ValueError, match="permissions"):
        replace(current, execution_allowed=True)
    with pytest.raises(ValueError, match="zero"):
        replace(current, approved_size=1)
    with pytest.raises(ValueError, match="SHA-256"):
        replace(current, input_checksums={"global": "short"})
    with pytest.raises(ValueError, match="unknown"):
        replace(current, validation_state="APPROVED")

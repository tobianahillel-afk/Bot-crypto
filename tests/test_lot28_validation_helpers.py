from __future__ import annotations

import copy

import pytest

from crypto_quant_bot.market_analysis.explanation_core_and_why_not_trade_layer import (
    build_explanation_state,
    checksum,
)
from crypto_quant_bot.market_analysis.explanation_core_validation import (
    ExplanationEvidenceError,
    iter_statements,
    mapping,
    resolve_pointer,
    validate_evidence_ref,
    validate_reason_set,
    validate_safety,
    validate_statements,
)
from tests.lot28_fixtures import load_config, load_inputs

COMMIT = "abcdef1234567890"


def test_mapping_and_pointer_resolution_exact_paths() -> None:
    payload = {"a": {"b/c": [{"~key": 7}]}}
    assert mapping(payload, "payload") is payload
    assert resolve_pointer(payload, "/a/b~1c/0/~0key") == 7
    with pytest.raises(ExplanationEvidenceError, match="must be an object"):
        mapping([], "payload")
    with pytest.raises(ExplanationEvidenceError, match="absolute"):
        resolve_pointer(payload, "a")
    with pytest.raises(ExplanationEvidenceError, match="field missing"):
        resolve_pointer(payload, "/missing")
    with pytest.raises(ExplanationEvidenceError, match="index invalid"):
        resolve_pointer(payload, "/a/b~1c/4")
    with pytest.raises(ExplanationEvidenceError, match="traverses scalar"):
        resolve_pointer(payload, "/a/b~1c/0/~0key/next")


def test_evidence_reference_validates_artifact_checksum_pointer_and_value() -> None:
    source = {"state": "MIXED", "score": 0.5}
    sources = {"artifact.json": source}
    reference = {
        "artifact_path": "artifact.json",
        "artifact_checksum": checksum(source),
        "json_pointer": "/state",
        "observed_value": "MIXED",
    }
    validate_evidence_ref(reference, sources)

    invalid = dict(reference)
    invalid["artifact_path"] = "unknown.json"
    with pytest.raises(ExplanationEvidenceError, match="unregistered"):
        validate_evidence_ref(invalid, sources)

    invalid = dict(reference)
    invalid["artifact_checksum"] = "0" * 64
    with pytest.raises(ExplanationEvidenceError, match="checksum mismatch"):
        validate_evidence_ref(invalid, sources)

    invalid = dict(reference)
    invalid["observed_value"] = "OTHER"
    with pytest.raises(ExplanationEvidenceError, match="observed value mismatch"):
        validate_evidence_ref(invalid, sources)


def built_bundle_sources() -> tuple[dict[str, object], dict[str, dict[str, object]], dict[str, object]]:
    global_context, alignment = load_inputs()
    config = load_config()
    state = build_explanation_state(global_context, alignment, config, COMMIT)
    bundle = state.bundle.to_dict()
    sources = {
        config["input_artifacts"]["global_context"]: global_context,
        config["input_artifacts"]["multi_timeframe_alignment"]: alignment,
    }
    return bundle, sources, config


def test_statement_validator_rerenders_and_preserves_template_count() -> None:
    bundle, sources, config = built_bundle_sources()
    codes = validate_statements(bundle, config, sources)
    assert len(codes) == 14
    assert len(set(codes)) == 14
    assert len(iter_statements(bundle)) == 14

    altered = copy.deepcopy(bundle)
    altered["facts_observed"][0]["section"] = "inferences"
    with pytest.raises(ExplanationEvidenceError, match="section diverges"):
        validate_statements(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["facts_observed"][0]["reason_code"] = "OTHER"
    with pytest.raises(ExplanationEvidenceError, match="reason code diverges"):
        validate_statements(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["facts_observed"][0]["template_id"] = "unknown"
    with pytest.raises(ExplanationEvidenceError, match="unknown statement template"):
        validate_statements(altered, config, sources)


def test_reason_set_validator_enforces_registry_and_final_consequence() -> None:
    bundle, sources, config = built_bundle_sources()
    assert validate_reason_set(bundle, config, sources) == (
        "WNT_CONTEXT_MIXED",
        "WNT_MTF_DIVERGENCE",
        "WNT_PERMISSIONS_DISABLED",
    )

    altered = copy.deepcopy(bundle)
    altered["why_not_trade"]["dominant_reason_code"] = "WNT_CONTEXT_MIXED"
    with pytest.raises(ExplanationEvidenceError, match="dominant"):
        validate_reason_set(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["why_not_trade"]["final_consequence"] = "Other consequence."
    with pytest.raises(ExplanationEvidenceError, match="diverges"):
        validate_reason_set(altered, config, sources)

    altered = copy.deepcopy(bundle)
    altered["why_not_trade"]["reasons"][0]["owner"] = "UnknownDomain"
    with pytest.raises(ExplanationEvidenceError, match="diverges from config"):
        validate_reason_set(altered, config, sources)


def test_safety_validator_rejects_every_permission_and_forbidden_token() -> None:
    global_context, alignment = load_inputs()
    config = load_config()
    state = build_explanation_state(global_context, alignment, config, COMMIT).to_dict()
    validate_safety(state, config)

    for field in config["promotion_restrictions"]:
        altered = copy.deepcopy(state)
        altered[field] = True
        with pytest.raises(ExplanationEvidenceError, match="permission mismatch"):
            validate_safety(altered, config)

    altered = copy.deepcopy(state)
    altered["bundle"]["final_consequence"][0]["text"] += " SELL"
    with pytest.raises(ExplanationEvidenceError, match="forbidden"):
        validate_safety(altered, config)

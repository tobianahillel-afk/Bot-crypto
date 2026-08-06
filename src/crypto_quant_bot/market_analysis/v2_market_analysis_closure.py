from __future__ import annotations

import hashlib
import json
import subprocess  # nosec B404 -- fixed local validator command only
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from crypto_quant_bot.market_analysis.alignment_io import load_json
from crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit import file_checksum
from crypto_quant_bot.market_analysis.v2_market_analysis_closure_models import (
    ClosureValidationError,
    NegativeControlEvidenceV1,
    UpstreamArtifactEvidenceV1,
    V2FinalClosureManifestV1,
    V2MarketAnalysisClosureStateV1,
    ValidatorReplayEvidenceV1,
)

EXPECTED_UPSTREAM_LOTS = tuple(range(21, 29))
EXPECTED_COVERED_LOTS = tuple(range(21, 31))
EXPECTED_NEGATIVE_CONTROLS = (
    "SCHEMA_MISMATCH_REJECTED",
    "UPSTREAM_CHECKSUM_TAMPER_REJECTED",
    "FORBIDDEN_CAPABILITY_REJECTED",
    "VALIDATOR_DIVERGENCE_REJECTED",
    "LIFECYCLE_UNLOCK_REJECTED",
)
EXPECTED_FUTURE_LOCKS = (
    "ContinuousMarketStateV1",
    "MultiHorizonForecastV1",
    "ParticipantBehaviorScenarioV1",
    "TradeIntent",
    "RiskDecisionV1",
    "RiskReservationV1",
    "OrderIntent",
)
EXPECTED_REASON_CODES = (
    "V2_LOTS_21_30_COVERED",
    "V2_REPLAY_CHAIN_MATCH",
    "V2_NEGATIVE_CONTROLS_PASS",
    "V3_CAPABILITIES_LOCKED",
    "V2_OFFLINE_ONLY",
)
MAX_VALIDATOR_OUTPUT_BYTES = 1_000_000
VALIDATOR_COMMAND = ("python", "scripts/validate_lot29.py")


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ClosureValidationError(f"{field} must be an object")
    return value


def _require_list_of_objects(value: object, field: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ClosureValidationError(f"{field} must be a list of objects")
    return tuple(item for item in value if isinstance(item, dict))


def _validate_safety(safety: object) -> None:
    expected = {
        "analysis_only": True,
        "approved_size": 0,
        "execution_allowed": False,
        "order_routing_allowed": False,
        "risk_approval_allowed": False,
        "signal_generation_allowed": False,
        "trade_allowed": False,
        "used_for_decision": False,
    }
    if safety != expected:
        raise ClosureValidationError("closure safety policy is not fail-closed")


def _validate_config(config: dict[str, Any]) -> dict[str, str]:
    if config.get("schema_version") != "v2-market-analysis-closure-config-v1":
        raise ClosureValidationError("unsupported Lot 30 config schema")
    if config.get("version_id") != "V2_MARKET_ANALYSIS":
        raise ClosureValidationError("Lot 30 must close V2_MARKET_ANALYSIS")
    if config.get("runtime_mode") != "LOCAL_OFFLINE_ANALYSIS_ONLY":
        raise ClosureValidationError("Lot 30 must remain offline only")
    if tuple(config.get("future_capabilities_locked", ())) != EXPECTED_FUTURE_LOCKS:
        raise ClosureValidationError("future capability lock set differs")
    if tuple(config.get("negative_controls", ())) != EXPECTED_NEGATIVE_CONTROLS:
        raise ClosureValidationError("negative control registry differs")
    _validate_safety(config.get("safety"))
    return _validate_lot29_paths(config.get("lot29"))


def _validate_lot29_paths(raw_paths: object) -> dict[str, str]:
    paths = _require_object(raw_paths, "lot29")
    expected = {
        "state_path": "data/audit/v2_deterministic_replay_and_audit_lot29.json",
        "audit_path": "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json",
        "closure_path": "data/audit/v2_replay_closure_manifest_lot29.json",
        "lifecycle_path": "data/audit/roadmap_lifecycle_overlay_lot29.json",
        "validator": "scripts/validate_lot29.py",
    }
    if paths != expected:
        raise ClosureValidationError("Lot 29 source registry differs from the canonical paths")
    return {key: str(value) for key, value in paths.items()}


def _validate_strict_fail_closed_document(document: dict[str, Any], name: str) -> None:
    expected = {
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    for field, value in expected.items():
        if document.get(field) != value:
            raise ClosureValidationError(f"{name} safety mismatch: {field}")
    forbidden = ("signal_generation_allowed", "risk_approval_allowed", "order_routing_allowed")
    for field in forbidden:
        if document.get(field) is True:
            raise ClosureValidationError(f"{name} enables forbidden field: {field}")


def _validate_historical_artifact_safety(document: dict[str, Any], lot: int) -> None:
    forbidden = (
        "used_for_decision",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    )
    for field in forbidden:
        if document.get(field) is True:
            raise ClosureValidationError(f"Lot {lot} artifact enables forbidden field: {field}")
    if "approved_size" in document and document.get("approved_size") != 0:
        raise ClosureValidationError(f"Lot {lot} artifact approved_size must remain zero")
    if "analysis_only" in document and document.get("analysis_only") is not True:
        raise ClosureValidationError(f"Lot {lot} artifact analysis_only must remain true")


def _validate_lifecycle(lifecycle: dict[str, Any]) -> None:
    if lifecycle.get("latest_implemented_lot") != 29:
        raise ClosureValidationError("lifecycle latest implemented lot must be 29")
    lots = _require_object(lifecycle.get("lots"), "lifecycle lots")
    lot29 = _require_object(lots.get("29"), "lifecycle Lot 29")
    lot30 = _require_object(lots.get("30"), "lifecycle Lot 30")
    if lot29.get("status") != "IMPLEMENTED_VALIDATED_OFFLINE_REPLAY_ONLY":
        raise ClosureValidationError("Lot 29 lifecycle status is not validated")
    if lot29.get("trade_allowed") is not False or lot29.get("execution_allowed") is not False:
        raise ClosureValidationError("Lot 29 lifecycle enables trading or execution")
    if lot30 != {"implementation_started": False, "status": "PLANNED_LOCKED"}:
        raise ClosureValidationError("Lot 30 entry lifecycle must remain locked")


def _validate_lot29_state_checksum(state: dict[str, Any]) -> str:
    payload = dict(state)
    output_checksum = payload.pop("output_checksum", None)
    if output_checksum != canonical_checksum(payload):
        raise ClosureValidationError("Lot 29 persisted state checksum mismatch")
    return str(output_checksum)


def _artifact_evidence(root: Path, item: dict[str, Any]) -> UpstreamArtifactEvidenceV1:
    lot = int(item.get("lot", -1))
    relative = str(item.get("artifact_path", ""))
    path = root / relative
    if not path.is_file():
        raise ClosureValidationError(f"Lot {lot} artifact is missing")
    observed_checksum = file_checksum(path)
    if item.get("artifact_checksum") != observed_checksum:
        raise ClosureValidationError(f"Lot {lot} artifact checksum changed")
    observed_size = path.stat().st_size
    if item.get("byte_size") != observed_size:
        raise ClosureValidationError(f"Lot {lot} artifact byte size changed")
    artifact = _require_object(load_json(path), f"Lot {lot} artifact")
    embedded = item.get("embedded_output_checksum")
    if embedded is not None and artifact.get("output_checksum") != embedded:
        raise ClosureValidationError(f"Lot {lot} embedded output checksum changed")
    _validate_historical_artifact_safety(artifact, lot)
    return UpstreamArtifactEvidenceV1(
        lot=lot,
        artifact_path=relative,
        artifact_checksum=observed_checksum,
        embedded_output_checksum=embedded if isinstance(embedded, str) else None,
        byte_size=observed_size,
    )


def _validate_upstream_artifacts(
    root: Path,
    state: dict[str, Any],
) -> tuple[UpstreamArtifactEvidenceV1, ...]:
    items = _require_list_of_objects(state.get("artifacts"), "Lot 29 artifacts")
    if tuple(item.get("lot") for item in items) != EXPECTED_UPSTREAM_LOTS:
        raise ClosureValidationError("Lot 29 upstream artifacts must be ordered 21..28")
    return tuple(_artifact_evidence(root, item) for item in items)


def _validate_lot29_links(
    state: dict[str, Any],
    audit: dict[str, Any],
    closure: dict[str, Any],
    output_checksum: str,
) -> None:
    if state.get("replay_status") != "MATCH" or audit.get("replay_status") != "MATCH":
        raise ClosureValidationError("Lot 29 replay is not MATCH")
    if state.get("closure_manifest") != closure:
        raise ClosureValidationError("Lot 29 state and closure manifest differ")
    if audit.get("output_checksum") != output_checksum:
        raise ClosureValidationError("Lot 29 audit output checksum differs")
    if audit.get("chain_checksum") != closure.get("chain_checksum"):
        raise ClosureValidationError("Lot 29 audit chain checksum differs")
    if closure.get("lot_sequence") != list(EXPECTED_UPSTREAM_LOTS):
        raise ClosureValidationError("Lot 29 closure sequence must be 21..28")
    if closure.get("artifact_count") != 8 or closure.get("validator_count") != 8:
        raise ClosureValidationError("Lot 29 closure must contain eight artifacts and validators")


def _load_and_validate_lot29(
    root: Path,
    paths: dict[str, str],
) -> tuple[dict[str, Any], tuple[UpstreamArtifactEvidenceV1, ...]]:
    state = _require_object(load_json(root / paths["state_path"]), "Lot 29 state")
    audit = _require_object(load_json(root / paths["audit_path"]), "Lot 29 audit")
    closure = _require_object(load_json(root / paths["closure_path"]), "Lot 29 closure")
    lifecycle = _require_object(load_json(root / paths["lifecycle_path"]), "Lot 29 lifecycle")
    output_checksum = _validate_lot29_state_checksum(state)
    _validate_strict_fail_closed_document(state, "Lot 29 state")
    _validate_strict_fail_closed_document(audit, "Lot 29 audit")
    upstream = _validate_upstream_artifacts(root, state)
    _validate_lot29_links(state, audit, closure, output_checksum)
    _validate_lifecycle(lifecycle)
    return lifecycle, upstream


def run_lot29_validator(root: Path, run_index: int) -> ValidatorReplayEvidenceV1:
    completed = subprocess.run(  # nosec B603
        VALIDATOR_COMMAND,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=240,
    )
    combined = (completed.stdout + "\n" + completed.stderr).encode("utf-8")
    if len(combined) > MAX_VALIDATOR_OUTPUT_BYTES:
        raise ClosureValidationError("Lot 29 validator output exceeds limit")
    if completed.returncode != 0:
        raise ClosureValidationError(f"Lot 29 validator failed with rc={completed.returncode}")
    return ValidatorReplayEvidenceV1(
        run_index=run_index,
        command=VALIDATOR_COMMAND,
        return_code=0,
        status="PASS",
        stdout_checksum=hashlib.sha256(combined).hexdigest(),
    )


def _require_validator_match(replays: tuple[ValidatorReplayEvidenceV1, ...]) -> None:
    if tuple(item.run_index for item in replays) != (1, 2):
        raise ClosureValidationError("two ordered validator runs are required")
    if replays[0].stdout_checksum != replays[1].stdout_checksum:
        raise ClosureValidationError("Lot 29 validator replay diverged")


def _resolve_validator_evidence(
    root: Path,
    execute_validator: bool,
    evidence: tuple[ValidatorReplayEvidenceV1, ...] | None,
) -> tuple[ValidatorReplayEvidenceV1, ...]:
    if evidence is None and not execute_validator:
        raise ClosureValidationError("validator evidence is required when execution is disabled")
    resolved = evidence or (run_lot29_validator(root, 1), run_lot29_validator(root, 2))
    _require_validator_match(resolved)
    return resolved


def _expect_rejected(
    name: str,
    reason_code: str,
    operation: Callable[[], object],
) -> NegativeControlEvidenceV1:
    try:
        operation()
    except ClosureValidationError:
        return NegativeControlEvidenceV1(name=name, status="PASS", reason_code=reason_code)
    raise ClosureValidationError(f"negative control did not reject: {name}")


def _invalid_control_inputs(
    config: dict[str, Any],
    lifecycle: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    wrong_schema = {**config, "schema_version": "unsupported"}
    forbidden = {**config, "safety": {**_require_object(config.get("safety"), "safety")}}
    _require_object(forbidden["safety"], "forbidden safety")["trade_allowed"] = True
    unlocked = json.loads(json.dumps(lifecycle))
    lots = _require_object(unlocked.get("lots"), "unlocked lifecycle lots")
    lots["30"] = {"implementation_started": True, "status": "IMPLEMENTATION_STARTED"}
    return wrong_schema, forbidden, unlocked


def _reject_tampered_checksum(observed_checksum: str) -> None:
    if observed_checksum != "0" * 64:
        raise ClosureValidationError("tampered checksum rejected")


def _divergent_replays() -> tuple[ValidatorReplayEvidenceV1, ...]:
    return (
        ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", "1" * 64),
        ValidatorReplayEvidenceV1(2, VALIDATOR_COMMAND, 0, "PASS", "2" * 64),
    )


def run_negative_controls(
    config: dict[str, Any],
    lifecycle: dict[str, Any],
    observed_checksum: str,
) -> tuple[NegativeControlEvidenceV1, ...]:
    wrong_schema, forbidden, unlocked = _invalid_control_inputs(config, lifecycle)
    specifications: tuple[tuple[str, str, Callable[[], object]], ...] = (
        ("SCHEMA_MISMATCH_REJECTED", "UNSUPPORTED_SCHEMA_BLOCKED", lambda: _validate_config(wrong_schema)),
        ("UPSTREAM_CHECKSUM_TAMPER_REJECTED", "UPSTREAM_CHECKSUM_MISMATCH_BLOCKED", lambda: _reject_tampered_checksum(observed_checksum)),
        ("FORBIDDEN_CAPABILITY_REJECTED", "FORBIDDEN_CAPABILITY_BLOCKED", lambda: _validate_config(forbidden)),
        ("VALIDATOR_DIVERGENCE_REJECTED", "NON_DETERMINISTIC_VALIDATOR_BLOCKED", lambda: _require_validator_match(_divergent_replays())),
        ("LIFECYCLE_UNLOCK_REJECTED", "UNAUTHORIZED_LIFECYCLE_ADVANCE_BLOCKED", lambda: _validate_lifecycle(unlocked)),
    )
    return tuple(_expect_rejected(name, reason, operation) for name, reason, operation in specifications)


def _final_chain_checksum(
    upstream: tuple[UpstreamArtifactEvidenceV1, ...],
    evidence_checksums: tuple[str, str, str],
    validator_checksum: str,
) -> str:
    state_checksum, audit_checksum, closure_checksum = evidence_checksums
    return canonical_checksum(
        {
            "upstream": [item.artifact_checksum for item in upstream],
            "lot29_state": state_checksum,
            "lot29_audit": audit_checksum,
            "lot29_closure": closure_checksum,
            "validator_stdout": validator_checksum,
            "covered_lots": list(EXPECTED_COVERED_LOTS),
        }
    )


def _lot29_evidence_checksums(root: Path, paths: dict[str, str]) -> tuple[str, str, str]:
    return (
        file_checksum(root / paths["state_path"]),
        file_checksum(root / paths["audit_path"]),
        file_checksum(root / paths["closure_path"]),
    )


def _build_manifest(
    upstream: tuple[UpstreamArtifactEvidenceV1, ...],
    checksums: tuple[str, str, str],
    validator_checksum: str,
    negative_control_count: int,
) -> V2FinalClosureManifestV1:
    state_checksum, audit_checksum, closure_checksum = checksums
    return V2FinalClosureManifestV1(
        covered_lot_sequence=EXPECTED_COVERED_LOTS,
        upstream_lot_sequence=EXPECTED_UPSTREAM_LOTS,
        direct_validated_lot=29,
        closure_lot=30,
        upstream_artifact_checksums=tuple(item.artifact_checksum for item in upstream),
        lot29_state_checksum=state_checksum,
        lot29_audit_checksum=audit_checksum,
        lot29_closure_checksum=closure_checksum,
        validator_stdout_checksum=validator_checksum,
        negative_control_count=negative_control_count,
        final_chain_checksum=_final_chain_checksum(upstream, checksums, validator_checksum),
        closure_status="V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
    )


def _build_state(
    code_commit: str,
    upstream: tuple[UpstreamArtifactEvidenceV1, ...],
    validators: tuple[ValidatorReplayEvidenceV1, ...],
    controls: tuple[NegativeControlEvidenceV1, ...],
    manifest: V2FinalClosureManifestV1,
) -> V2MarketAnalysisClosureStateV1:
    draft = V2MarketAnalysisClosureStateV1(
        code_commit=code_commit,
        version_id="V2_MARKET_ANALYSIS",
        runtime_mode="LOCAL_OFFLINE_ANALYSIS_ONLY",
        upstream_artifacts=upstream,
        validator_replays=validators,
        negative_controls=controls,
        closure_manifest=manifest,
        reason_codes=EXPECTED_REASON_CODES,
        future_capabilities_locked=EXPECTED_FUTURE_LOCKS,
        analysis_only=True,
        used_for_decision=False,
        signal_generation_allowed=False,
        risk_approval_allowed=False,
        order_routing_allowed=False,
        trade_allowed=False,
        execution_allowed=False,
        approved_size=0,
        output_checksum="0" * 64,
    )
    return replace(draft, output_checksum=canonical_checksum(draft.payload_without_checksum()))


def build_closure_state(
    root: Path,
    config: dict[str, Any],
    code_commit: str,
    *,
    execute_validator: bool = True,
    validator_evidence: tuple[ValidatorReplayEvidenceV1, ...] | None = None,
) -> V2MarketAnalysisClosureStateV1:
    paths = _validate_config(config)
    lifecycle, upstream = _load_and_validate_lot29(root, paths)
    validators = _resolve_validator_evidence(root, execute_validator, validator_evidence)
    controls = run_negative_controls(config, lifecycle, upstream[0].artifact_checksum)
    checksums = _lot29_evidence_checksums(root, paths)
    manifest = _build_manifest(upstream, checksums, validators[0].stdout_checksum, len(controls))
    return _build_state(code_commit, upstream, validators, controls, manifest)


def replay_matches(
    first: V2MarketAnalysisClosureStateV1,
    second: V2MarketAnalysisClosureStateV1,
) -> bool:
    return first.to_dict() == second.to_dict()


def _parse_validator_evidence(raw: object) -> tuple[ValidatorReplayEvidenceV1, ...]:
    items = _require_list_of_objects(raw, "persisted validator replays")
    return tuple(
        ValidatorReplayEvidenceV1(
            run_index=int(item.get("run_index", -1)),
            command=tuple(str(value) for value in item.get("command", ())),
            return_code=int(item.get("return_code", -1)),
            status=str(item.get("status", "")),
            stdout_checksum=str(item.get("stdout_checksum", "")),
        )
        for item in items
    )


def _persisted_output_checksum(state: dict[str, Any]) -> str:
    payload = dict(state)
    output_checksum = payload.pop("output_checksum", None)
    if output_checksum != canonical_checksum(payload):
        raise ClosureValidationError("persisted Lot 30 state checksum mismatch")
    return str(output_checksum)


def _validate_regenerated_state(
    root: Path,
    config: dict[str, Any],
    state: dict[str, Any],
) -> None:
    validators = _parse_validator_evidence(state.get("validator_replays"))
    expected = build_closure_state(
        root,
        config,
        str(state.get("code_commit", "")),
        execute_validator=False,
        validator_evidence=validators,
    )
    if expected.to_dict() != state:
        raise ClosureValidationError("persisted Lot 30 state differs from regenerated closure")


def _validate_persisted_manifest(state: dict[str, Any], manifest: dict[str, Any]) -> None:
    if state.get("closure_manifest") != manifest:
        raise ClosureValidationError("persisted Lot 30 manifest differs from state")


def _validate_persisted_audit(
    audit: dict[str, Any],
    manifest: dict[str, Any],
    output_checksum: str,
) -> None:
    expected = {
        "output_checksum": output_checksum,
        "final_chain_checksum": manifest.get("final_chain_checksum"),
        "closure_status": manifest.get("closure_status"),
        "covered_lot_count": 10,
        "negative_control_count": 5,
        "analysis_only": True,
        "used_for_decision": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    for field, value in expected.items():
        if audit.get(field) != value:
            raise ClosureValidationError(f"Lot 30 audit mismatch: {field}")


def _validation_summary(manifest: dict[str, Any], output_checksum: str) -> dict[str, Any]:
    return {
        "schema_version": "lot30-validation-v1",
        "status": "PASS",
        "closure_status": manifest["closure_status"],
        "covered_lot_count": 10,
        "upstream_artifact_count": 8,
        "validator_replay_count": 2,
        "negative_control_count": 5,
        "final_chain_checksum": manifest["final_chain_checksum"],
        "output_checksum": output_checksum,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def validate_persisted_state(
    root: Path,
    config: dict[str, Any],
    state: dict[str, Any],
    audit: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    output_checksum = _persisted_output_checksum(state)
    _validate_regenerated_state(root, config, state)
    _validate_persisted_manifest(state, manifest)
    _validate_persisted_audit(audit, manifest, output_checksum)
    return _validation_summary(manifest, output_checksum)

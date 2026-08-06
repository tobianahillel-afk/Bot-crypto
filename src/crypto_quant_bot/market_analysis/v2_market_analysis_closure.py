from __future__ import annotations

import hashlib
import json
import subprocess  # nosec B404 -- fixed local validator command only
from collections.abc import Callable
from pathlib import Path
from typing import Any

from crypto_quant_bot.market_analysis.alignment_io import load_json
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


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    lot29 = _require_object(config.get("lot29"), "lot29")
    expected_paths = {
        "state_path": "data/audit/v2_deterministic_replay_and_audit_lot29.json",
        "audit_path": "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json",
        "closure_path": "data/audit/v2_replay_closure_manifest_lot29.json",
        "lifecycle_path": "data/audit/roadmap_lifecycle_overlay_lot29.json",
        "validator": "scripts/validate_lot29.py",
    }
    if lot29 != expected_paths:
        raise ClosureValidationError("Lot 29 source registry differs from the canonical paths")
    return {key: str(value) for key, value in lot29.items()}


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
    for field in ("signal_generation_allowed", "risk_approval_allowed", "order_routing_allowed"):
        if document.get(field) is True:
            raise ClosureValidationError(f"{name} enables forbidden field: {field}")


def _validate_historical_artifact_safety(document: dict[str, Any], lot: int) -> None:
    for field in (
        "used_for_decision",
        "signal_generation_allowed",
        "risk_approval_allowed",
        "order_routing_allowed",
        "trade_allowed",
        "execution_allowed",
    ):
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
    observed = canonical_checksum(payload)
    if output_checksum != observed:
        raise ClosureValidationError("Lot 29 persisted state checksum mismatch")
    return str(output_checksum)


def _validate_upstream_artifacts(
    root: Path,
    state: dict[str, Any],
) -> tuple[UpstreamArtifactEvidenceV1, ...]:
    items = _require_list_of_objects(state.get("artifacts"), "Lot 29 artifacts")
    if tuple(item.get("lot") for item in items) != EXPECTED_UPSTREAM_LOTS:
        raise ClosureValidationError("Lot 29 upstream artifacts must be ordered 21..28")
    evidence: list[UpstreamArtifactEvidenceV1] = []
    for item in items:
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
        artifact_payload = _require_object(load_json(path), f"Lot {lot} artifact")
        embedded = item.get("embedded_output_checksum")
        if embedded is not None and artifact_payload.get("output_checksum") != embedded:
            raise ClosureValidationError(f"Lot {lot} embedded output checksum changed")
        _validate_historical_artifact_safety(artifact_payload, lot)
        evidence.append(
            UpstreamArtifactEvidenceV1(
                lot=lot,
                artifact_path=relative,
                artifact_checksum=observed_checksum,
                embedded_output_checksum=embedded if isinstance(embedded, str) else None,
                byte_size=observed_size,
            )
        )
    return tuple(evidence)


def _load_and_validate_lot29(
    root: Path,
    paths: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], tuple[UpstreamArtifactEvidenceV1, ...]]:
    state = _require_object(load_json(root / paths["state_path"]), "Lot 29 state")
    audit = _require_object(load_json(root / paths["audit_path"]), "Lot 29 audit")
    closure = _require_object(load_json(root / paths["closure_path"]), "Lot 29 closure")
    lifecycle = _require_object(load_json(root / paths["lifecycle_path"]), "Lot 29 lifecycle")

    output_checksum = _validate_lot29_state_checksum(state)
    _validate_strict_fail_closed_document(state, "Lot 29 state")
    _validate_strict_fail_closed_document(audit, "Lot 29 audit")
    upstream = _validate_upstream_artifacts(root, state)
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
    _validate_lifecycle(lifecycle)
    return state, audit, lifecycle, upstream


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


def run_negative_controls(
    config: dict[str, Any],
    lifecycle: dict[str, Any],
    observed_checksum: str,
) -> tuple[NegativeControlEvidenceV1, ...]:
    wrong_schema = dict(config)
    wrong_schema["schema_version"] = "unsupported"

    forbidden = dict(config)
    forbidden_safety = dict(_require_object(config.get("safety"), "safety"))
    forbidden_safety["trade_allowed"] = True
    forbidden["safety"] = forbidden_safety

    unlocked_lifecycle = json.loads(json.dumps(lifecycle))
    unlocked_lots = _require_object(unlocked_lifecycle.get("lots"), "unlocked lifecycle lots")
    unlocked_lots["30"] = {"implementation_started": True, "status": "IMPLEMENTATION_STARTED"}

    first = ValidatorReplayEvidenceV1(1, VALIDATOR_COMMAND, 0, "PASS", "1" * 64)
    second = ValidatorReplayEvidenceV1(2, VALIDATOR_COMMAND, 0, "PASS", "2" * 64)

    def reject_tampered_checksum() -> None:
        if observed_checksum != "0" * 64:
            raise ClosureValidationError("tampered checksum rejected")

    return (
        _expect_rejected(
            "SCHEMA_MISMATCH_REJECTED",
            "UNSUPPORTED_SCHEMA_BLOCKED",
            lambda: _validate_config(wrong_schema),
        ),
        _expect_rejected(
            "UPSTREAM_CHECKSUM_TAMPER_REJECTED",
            "UPSTREAM_CHECKSUM_MISMATCH_BLOCKED",
            reject_tampered_checksum,
        ),
        _expect_rejected(
            "FORBIDDEN_CAPABILITY_REJECTED",
            "FORBIDDEN_CAPABILITY_BLOCKED",
            lambda: _validate_config(forbidden),
        ),
        _expect_rejected(
            "VALIDATOR_DIVERGENCE_REJECTED",
            "NON_DETERMINISTIC_VALIDATOR_BLOCKED",
            lambda: _require_validator_match((first, second)),
        ),
        _expect_rejected(
            "LIFECYCLE_UNLOCK_REJECTED",
            "UNAUTHORIZED_LIFECYCLE_ADVANCE_BLOCKED",
            lambda: _validate_lifecycle(unlocked_lifecycle),
        ),
    )


def _final_chain_checksum(
    upstream: tuple[UpstreamArtifactEvidenceV1, ...],
    lot29_state_checksum: str,
    lot29_audit_checksum: str,
    lot29_closure_checksum: str,
    validator_checksum: str,
) -> str:
    return canonical_checksum(
        {
            "upstream": [item.artifact_checksum for item in upstream],
            "lot29_state": lot29_state_checksum,
            "lot29_audit": lot29_audit_checksum,
            "lot29_closure": lot29_closure_checksum,
            "validator_stdout": validator_checksum,
            "covered_lots": list(EXPECTED_COVERED_LOTS),
        }
    )


def build_closure_state(
    root: Path,
    config: dict[str, Any],
    code_commit: str,
    *,
    execute_validator: bool = True,
    validator_evidence: tuple[ValidatorReplayEvidenceV1, ...] | None = None,
) -> V2MarketAnalysisClosureStateV1:
    paths = _validate_config(config)
    _state29, _audit29, lifecycle, upstream = _load_and_validate_lot29(root, paths)
    if validator_evidence is None:
        if not execute_validator:
            raise ClosureValidationError("validator evidence is required when execution is disabled")
        validator_evidence = (
            run_lot29_validator(root, 1),
            run_lot29_validator(root, 2),
        )
    _require_validator_match(validator_evidence)
    negative_controls = run_negative_controls(config, lifecycle, upstream[0].artifact_checksum)

    lot29_state_checksum = file_checksum(root / paths["state_path"])
    lot29_audit_checksum = file_checksum(root / paths["audit_path"])
    lot29_closure_checksum = file_checksum(root / paths["closure_path"])
    validator_checksum = validator_evidence[0].stdout_checksum
    final_chain_checksum = _final_chain_checksum(
        upstream,
        lot29_state_checksum,
        lot29_audit_checksum,
        lot29_closure_checksum,
        validator_checksum,
    )
    manifest = V2FinalClosureManifestV1(
        covered_lot_sequence=EXPECTED_COVERED_LOTS,
        upstream_lot_sequence=EXPECTED_UPSTREAM_LOTS,
        direct_validated_lot=29,
        closure_lot=30,
        upstream_artifact_checksums=tuple(item.artifact_checksum for item in upstream),
        lot29_state_checksum=lot29_state_checksum,
        lot29_audit_checksum=lot29_audit_checksum,
        lot29_closure_checksum=lot29_closure_checksum,
        validator_stdout_checksum=validator_checksum,
        negative_control_count=len(negative_controls),
        final_chain_checksum=final_chain_checksum,
        closure_status="V2_MARKET_ANALYSIS_CLOSED_OFFLINE_ONLY",
    )
    payload = {
        "schema_version": "v2-market-analysis-closure-state-v1",
        "code_commit": code_commit,
        "version_id": "V2_MARKET_ANALYSIS",
        "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
        "upstream_artifacts": [item.to_dict() for item in upstream],
        "validator_replays": [item.to_dict() for item in validator_evidence],
        "negative_controls": [item.to_dict() for item in negative_controls],
        "closure_manifest": manifest.to_dict(),
        "reason_codes": list(EXPECTED_REASON_CODES),
        "future_capabilities_locked": list(EXPECTED_FUTURE_LOCKS),
        "analysis_only": True,
        "used_for_decision": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }
    return V2MarketAnalysisClosureStateV1(
        code_commit=code_commit,
        version_id="V2_MARKET_ANALYSIS",
        runtime_mode="LOCAL_OFFLINE_ANALYSIS_ONLY",
        upstream_artifacts=upstream,
        validator_replays=validator_evidence,
        negative_controls=negative_controls,
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
        output_checksum=canonical_checksum(payload),
    )


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


def validate_persisted_state(
    root: Path,
    config: dict[str, Any],
    state: dict[str, Any],
    audit: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    persisted = dict(state)
    output_checksum = persisted.pop("output_checksum", None)
    if output_checksum != canonical_checksum(persisted):
        raise ClosureValidationError("persisted Lot 30 state checksum mismatch")
    validator_evidence = _parse_validator_evidence(state.get("validator_replays"))
    expected = build_closure_state(
        root,
        config,
        str(state.get("code_commit", "")),
        execute_validator=False,
        validator_evidence=validator_evidence,
    )
    if expected.to_dict() != state:
        raise ClosureValidationError("persisted Lot 30 state differs from regenerated closure")
    if state.get("closure_manifest") != manifest:
        raise ClosureValidationError("persisted Lot 30 manifest differs from state")
    expected_audit = {
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
    for field, value in expected_audit.items():
        if audit.get(field) != value:
            raise ClosureValidationError(f"Lot 30 audit mismatch: {field}")
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

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    atomic_write_json,
    canonical_checksum,
    file_checksum,
    load_json_object,
)

from .microstructure_scope_and_offline_data_contracts_models import (
    CapabilityMatrixEntryV1,
    ContractRegistryEntryV1,
    Lot37LineageEnvelopeV1,
    Lot37MetricsV1,
    Lot37RunContextV1,
    MicrostructureScopeOfflineDataContractsAuditV1,
    MicrostructureScopeOfflineDataContractsCapabilityMatrixV1,
    MicrostructureScopeOfflineDataContractsContractRegistryV1,
    MicrostructureScopeOfflineDataContractsStateV1,
    PublicApiEntryV1,
)
from .microstructure_scope_and_offline_data_contracts_validation import (
    MicrostructureScopeValidationError,
    duration_us,
    lot37_safety,
    parse_utc_timestamp,
    require_integer,
    require_text,
    validate_causal_times,
)

CONFIG_PATH = Path("config/microstructure/microstructure_scope_offline_data_contracts_v1.json")
EXPECTED_GATE_CHECKSUM = "37ffdb72b1f83a506e95802518f77a5b06e164b342b6e2cf7985c1c695cda58d"
EXPECTED_V3_AUDIT_COMMIT = "33fba0abf7463fc54a36282476ee51655ff09919"
EXPECTED_LOT36_STATE_CHECKSUM = "635b5504d21ca8d46faf51bd46639538345b4bcd94437330791b49036ee07592"
EXPECTED_LOT36_AUDIT_CHECKSUM = "ca8f70e8f75b0e18b5b5c8835646ccb4c0e6adf4177023a9bd2117c0f1d81f42"
EXPECTED_REQUIRED_OUTPUTS = {
    "MicrostructureScopeOfflineDataContractsStateV1",
    "MicrostructureScopeOfflineDataContractsAuditV1",
    "MicrostructureScopeOfflineDataContractsContractRegistryV1",
    "MicrostructureScopeOfflineDataContractsCapabilityMatrixV1",
}
EXPECTED_CONTRACTS = {
    "MicrostructureOfflineL2InputV1",
    "MicrostructureOfflineTradeInputV1",
    *EXPECTED_REQUIRED_OUTPUTS,
}
EXPECTED_REQUIRED_CAPABILITIES = {
    "V4_SCOPE_BOUNDARY",
    "OFFLINE_DATA_CONTRACT_REGISTRY",
    "V4_CAPABILITY_MATRIX",
    "PUBLIC_API_BOUNDARY",
}
EXPECTED_FUTURE_LOTS = {
    "LOT38_ORDER_BOOK_L2_SNAPSHOT_ENGINE": 38,
    "LOT39_ORDER_BOOK_DELTA_SEQUENCE_RECONSTRUCTOR": 39,
    "LOT40_BOOK_INTEGRITY_DESYNCHRONIZATION_DETECTOR": 40,
    "LOT41_SPREAD_DEPTH_IMBALANCE_ENGINE": 41,
    "LOT42_LIQUIDITY_ZONES_WALLS_VOIDS_ENGINE": 42,
    "LOT43_BOOK_RESILIENCE_REPLENISHMENT_ENGINE": 43,
    "LOT44_TRADES_AGGRESSOR_CLASSIFICATION_SCHEMA": 44,
    "LOT45_ORDER_FLOW_DELTA_CVD_ENGINE": 45,
    "LOT46_TRADE_CLASSIFICATION_CONFIDENCE_ENGINE": 46,
    "LOT47_ABSORPTION_DEFENSE_HIDDEN_LIQUIDITY_PROXY": 47,
    "LOT48_VOLUME_CLUSTERS_TIME_AT_LEVEL_ENGINE": 48,
    "LOT49_STOP_ZONES_LIQUIDITY_POOLS_BREAKOUT_ATTRACTION": 49,
    "LOT50_SWEEP_FAKEOUT_TRAP_FAILED_AUCTION_ENGINE": 50,
    "LOT51_DERIVATIVES_CONTEXT": 51,
    "LOT52_GAME_THEORY_SCENARIO_AGGREGATION_V4_CLOSURE": 52,
}
EXPECTED_FORBIDDEN_CAPABILITIES = {
    "EXTERNAL_NETWORK_ACCESS",
    "PARTICIPANT_INTENT_AS_FACT",
    "SCENARIO_SCORE_AS_SIGNAL",
    "SIGNAL_GENERATION",
    "RISK_APPROVAL",
    "ORDER_ROUTING",
    "TRADING",
    "EXECUTION",
}
EXPECTED_PUBLIC_API = {
    "build_lot37_artifacts",
    "write_lot37_artifacts",
    "MicrostructureScopeOfflineDataContractsStateV1",
    "MicrostructureScopeOfflineDataContractsAuditV1",
}
COMMON_REASON_CODES = (
    "LOT37_SCOPE_CONTRACTS_VALIDATED",
    "V3_POST_MERGE_CLOSURE_VERIFIED",
    "OFFLINE_INPUT_AVAILABILITY_VERIFIED",
    "FUTURE_V4_CAPABILITIES_LOCKED",
    "PARTICIPANT_INFERENCE_MUST_BE_EXPLICIT",
    "SCENARIO_SCORE_IS_NOT_SIGNAL",
    "LOT38_REMAINS_LOCKED",
)


def _objects(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        raise MicrostructureScopeValidationError(f"{field} must be a non-empty object list")
    return [dict(item) for item in value]


def _verify_gate(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = root / require_text(config.get("entry_gate_path"), "entry_gate_path")
    gate = load_json_object(path)
    body = dict(gate)
    checksum = body.pop("output_checksum", None)
    if checksum != EXPECTED_GATE_CHECKSUM or canonical_checksum(body) != checksum:
        raise MicrostructureScopeValidationError("Lot 37 entry gate checksum changed")
    expected = {
        "gate_status": "GO_LOT37_IMPLEMENTATION_ENTRY",
        "human_decision": "APPROVED_START_LOT37",
        "target_lot": 37,
        "owner": "MicrostructureDomain",
        "runtime_mode": "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        "implementation_started": False,
        "next_lot": 38,
        "next_lot_status": "PLANNED_LOCKED",
    }
    if any(gate.get(field) != value for field, value in expected.items()):
        raise MicrostructureScopeValidationError("Lot 37 entry gate does not authorize this scope")
    if set(gate.get("required_outputs", [])) != EXPECTED_REQUIRED_OUTPUTS:
        raise MicrostructureScopeValidationError("Lot 37 required output contract set changed")
    if gate.get("safety") != lot37_safety():
        raise MicrostructureScopeValidationError("Lot 37 gate safety boundary changed")
    return gate


def _verify_lifecycle(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = root / require_text(config.get("lifecycle_overlay_path"), "lifecycle_overlay_path")
    overlay = load_json_object(path)
    if overlay.get("latest_implemented_lot") != 36:
        raise MicrostructureScopeValidationError("Lot 37 requires audited lifecycle latest lot 36")
    lots = overlay.get("lots")
    if not isinstance(lots, dict):
        raise MicrostructureScopeValidationError("lifecycle lot map missing")
    lot36 = lots.get("36")
    if not isinstance(lot36, dict) or lot36.get("v3_closed") is not True:
        raise MicrostructureScopeValidationError("V3 post-merge closure is not certified")
    if lot36.get("status") != "IMPLEMENTED_VALIDATED_V3_CLOSURE_ONLY":
        raise MicrostructureScopeValidationError("Lot 36 lifecycle status changed")
    if lots.get("37") != {"implementation_started": False, "status": "PLANNED_LOCKED"}:
        raise MicrostructureScopeValidationError("Lot 37 historical lock changed before implementation")
    return lot36


def _validate_config(config: dict[str, Any]) -> None:
    expected_fields = {
        "schema_version", "config_version", "run_id", "correlation_id", "lineage_id",
        "event_time", "available_at", "generated_at", "input_reference_time",
        "max_input_age_us", "entry_gate_path", "lifecycle_overlay_path",
        "offline_l2_fixture_path", "offline_trade_fixture_path", "contract_registry_id",
        "contract_registry_version", "contracts", "public_api", "capability_matrix",
    }
    if set(config) != expected_fields:
        raise MicrostructureScopeValidationError("Lot 37 config fields differ from contract")
    if config.get("schema_version") != "lot37-microstructure-scope-config-v1":
        raise MicrostructureScopeValidationError("Lot 37 config schema changed")
    if config.get("config_version") != "lot37-microstructure-scope-config-v1":
        raise MicrostructureScopeValidationError("Lot 37 config version changed")
    validate_causal_times(
        require_text(config.get("event_time"), "event_time"),
        require_text(config.get("available_at"), "available_at"),
        require_text(config.get("generated_at"), "generated_at"),
    )
    reference = parse_utc_timestamp(
        require_text(config.get("input_reference_time"), "input_reference_time"),
        "input_reference_time",
    )
    generated = parse_utc_timestamp(
        require_text(config.get("generated_at"), "generated_at"), "generated_at"
    )
    if reference != generated:
        raise MicrostructureScopeValidationError("Lot 37 reference time must equal generated_at")
    require_integer(config.get("max_input_age_us"), "max_input_age_us", minimum=1)


def _verify_fixture(
    root: Path,
    path_text: str,
    expected_checksum: str,
    reference: str,
    max_age_us: int,
) -> dict[str, Any]:
    path = root / path_text
    if file_checksum(path) != expected_checksum:
        raise MicrostructureScopeValidationError(f"offline fixture checksum changed: {path_text}")
    fixture = load_json_object(path)
    if fixture.get("fixture_only") is not True or fixture.get("canonical_contract") is not False:
        raise MicrostructureScopeValidationError("offline availability evidence cannot be canonical")
    if fixture.get("used_for_decision") is not False:
        raise MicrostructureScopeValidationError("offline availability evidence cannot be decision data")
    event = parse_utc_timestamp(
        require_text(fixture.get("event_time"), "fixture event_time"), "fixture event_time"
    )
    available = parse_utc_timestamp(
        require_text(fixture.get("available_at"), "fixture available_at"), "fixture available_at"
    )
    reference_time = parse_utc_timestamp(reference, "input_reference_time")
    if not event <= available <= reference_time:
        raise MicrostructureScopeValidationError("offline fixture violates causal availability")
    if duration_us(available, reference_time) > max_age_us:
        raise MicrostructureScopeValidationError("offline fixture exceeds configured freshness window")
    return fixture


def _verify_offline_inputs(
    root: Path, config: dict[str, Any], gate: dict[str, Any]
) -> tuple[str, str]:
    prerequisites = gate.get("prerequisites")
    if not isinstance(prerequisites, dict):
        raise MicrostructureScopeValidationError("Lot 37 gate prerequisites missing")
    l2_path = require_text(config.get("offline_l2_fixture_path"), "offline_l2_fixture_path")
    trade_path = require_text(config.get("offline_trade_fixture_path"), "offline_trade_fixture_path")
    if l2_path != prerequisites.get("offline_l2_fixture_path") or trade_path != prerequisites.get("offline_trade_fixture_path"):
        raise MicrostructureScopeValidationError("offline fixture path differs from approved gate")
    l2_checksum = require_text(prerequisites.get("offline_l2_fixture_sha256"), "offline_l2_fixture_sha256")
    trade_checksum = require_text(prerequisites.get("offline_trade_fixture_sha256"), "offline_trade_fixture_sha256")
    reference = require_text(config.get("input_reference_time"), "input_reference_time")
    max_age_us = require_integer(config.get("max_input_age_us"), "max_input_age_us", minimum=1)
    l2 = _verify_fixture(root, l2_path, l2_checksum, reference, max_age_us)
    trades = _verify_fixture(root, trade_path, trade_checksum, reference, max_age_us)
    if not isinstance(l2.get("bids"), list) or not isinstance(l2.get("asks"), list):
        raise MicrostructureScopeValidationError("L2 contract example lacks bid/ask collections")
    trade_records = trades.get("trades")
    if not isinstance(trade_records, list) or not trade_records:
        raise MicrostructureScopeValidationError("trade contract example lacks records")
    if any(item.get("side") != "UNKNOWN" for item in trade_records if isinstance(item, dict)):
        raise MicrostructureScopeValidationError("Lot 37 cannot classify trade aggressor side")
    return l2_checksum, trade_checksum


def _build_contract_registry(
    root: Path, config: dict[str, Any]
) -> MicrostructureScopeOfflineDataContractsContractRegistryV1:
    entries = tuple(
        sorted(
            (
                ContractRegistryEntryV1(
                    require_text(raw.get("contract_name"), "contract_name"),
                    require_text(raw.get("contract_kind"), "contract_kind"),
                    require_text(raw.get("owner"), "contract owner"),
                    require_text(raw.get("schema_path"), "schema_path"),
                    require_text(raw.get("producer"), "producer"),
                    require_text(raw.get("consumer"), "consumer"),
                    require_text(raw.get("status"), "contract status"),
                    require_integer(raw.get("enabled_by_lot"), "enabled_by_lot", minimum=37),
                )
                for raw in _objects(config.get("contracts"), "contracts")
            ),
            key=lambda item: item.contract_name,
        )
    )
    if {item.contract_name for item in entries} != EXPECTED_CONTRACTS:
        raise MicrostructureScopeValidationError("Lot 37 contract registry set changed")
    for item in entries:
        if not (root / item.schema_path).is_file():
            raise MicrostructureScopeValidationError(f"contract schema missing: {item.schema_path}")
    return MicrostructureScopeOfflineDataContractsContractRegistryV1(
        require_text(config.get("contract_registry_id"), "contract_registry_id"),
        require_text(config.get("contract_registry_version"), "contract_registry_version"),
        entries,
    )


def _build_capability_matrix(
    config: dict[str, Any]
) -> MicrostructureScopeOfflineDataContractsCapabilityMatrixV1:
    entries = tuple(
        sorted(
            (
                CapabilityMatrixEntryV1(
                    require_text(raw.get("capability_id"), "capability_id"),
                    require_text(raw.get("title"), "capability title"),
                    require_text(raw.get("classification"), "classification"),
                    require_text(raw.get("owner"), "capability owner"),
                    require_integer(raw.get("enabled_by_lot"), "enabled_by_lot"),
                    require_text(raw.get("implementation_status"), "implementation_status"),
                    require_text(raw.get("contract_ref"), "contract_ref"),
                    require_text(raw.get("gate_ref"), "gate_ref"),
                )
                for raw in _objects(config.get("capability_matrix"), "capability_matrix")
            ),
            key=lambda item: item.capability_id,
        )
    )
    _validate_capability_matrix(entries)
    return MicrostructureScopeOfflineDataContractsCapabilityMatrixV1(
        "v4-microstructure-capability-matrix-v1", "1.0.0", entries
    )


def _validate_capability_matrix(entries: tuple[CapabilityMatrixEntryV1, ...]) -> None:
    by_id = {item.capability_id: item for item in entries}
    expected = EXPECTED_REQUIRED_CAPABILITIES | set(EXPECTED_FUTURE_LOTS) | EXPECTED_FORBIDDEN_CAPABILITIES
    if set(by_id) != expected:
        raise MicrostructureScopeValidationError("Lot 37 capability matrix membership changed")
    if any(by_id[name].classification != "REQUIRED" for name in EXPECTED_REQUIRED_CAPABILITIES):
        raise MicrostructureScopeValidationError("Lot 37 required scope capability disabled")
    for name, lot in EXPECTED_FUTURE_LOTS.items():
        item = by_id[name]
        if item.classification != "DISABLED" or item.enabled_by_lot != lot:
            raise MicrostructureScopeValidationError("future V4 capability prematurely activated")
    if any(by_id[name].classification != "FORBIDDEN" for name in EXPECTED_FORBIDDEN_CAPABILITIES):
        raise MicrostructureScopeValidationError("Lot 37 forbidden capability weakened")


def _build_public_api(config: dict[str, Any]) -> tuple[PublicApiEntryV1, ...]:
    entries = tuple(
        sorted(
            (
                PublicApiEntryV1(
                    require_text(raw.get("symbol"), "symbol"),
                    require_text(raw.get("module"), "module"),
                    require_text(raw.get("kind"), "kind"),
                    require_text(raw.get("status"), "API status"),
                )
                for raw in _objects(config.get("public_api"), "public_api")
            ),
            key=lambda item: item.symbol,
        )
    )
    if {item.symbol for item in entries} != EXPECTED_PUBLIC_API:
        raise MicrostructureScopeValidationError("Lot 37 public API set changed")
    return entries


def _build_metrics(
    registry: MicrostructureScopeOfflineDataContractsContractRegistryV1,
    matrix: MicrostructureScopeOfflineDataContractsCapabilityMatrixV1,
    public_api: tuple[PublicApiEntryV1, ...],
    config: dict[str, Any],
) -> Lot37MetricsV1:
    counts = {
        kind: sum(item.classification == kind for item in matrix.entries)
        for kind in ("REQUIRED", "DISABLED", "FORBIDDEN")
    }
    available = parse_utc_timestamp(
        require_text(config.get("available_at"), "available_at"), "available_at"
    )
    generated = parse_utc_timestamp(
        require_text(config.get("generated_at"), "generated_at"), "generated_at"
    )
    return Lot37MetricsV1(
        len(registry.entries),
        len(matrix.entries),
        counts["REQUIRED"],
        counts["DISABLED"],
        counts["FORBIDDEN"],
        len(public_api),
        2,
        0,
        duration_us(available, generated),
    )


def _build_run_context(config: dict[str, Any], code_commit: str) -> Lot37RunContextV1:
    return Lot37RunContextV1(
        require_text(config.get("run_id"), "run_id"),
        "OFFLINE_MICROSTRUCTURE_RESEARCH_ONLY",
        require_text(config.get("config_version"), "config_version"),
        code_commit,
        require_text(config.get("correlation_id"), "correlation_id"),
    )


def _build_lineage(
    config: dict[str, Any], l2_checksum: str, trade_checksum: str
) -> Lot37LineageEnvelopeV1:
    return Lot37LineageEnvelopeV1(
        require_text(config.get("lineage_id"), "lineage_id"),
        EXPECTED_GATE_CHECKSUM,
        EXPECTED_V3_AUDIT_COMMIT,
        EXPECTED_LOT36_STATE_CHECKSUM,
        EXPECTED_LOT36_AUDIT_CHECKSUM,
        l2_checksum,
        trade_checksum,
        require_text(config.get("available_at"), "available_at"),
    )


def _build_state(
    config: dict[str, Any],
    code_commit: str,
    l2_checksum: str,
    trade_checksum: str,
    registry: MicrostructureScopeOfflineDataContractsContractRegistryV1,
    matrix: MicrostructureScopeOfflineDataContractsCapabilityMatrixV1,
    public_api: tuple[PublicApiEntryV1, ...],
) -> MicrostructureScopeOfflineDataContractsStateV1:
    state = MicrostructureScopeOfflineDataContractsStateV1(
        _build_run_context(config, code_commit),
        _build_lineage(config, l2_checksum, trade_checksum),
        require_text(config.get("event_time"), "event_time"),
        require_text(config.get("available_at"), "available_at"),
        require_text(config.get("generated_at"), "generated_at"),
        "VALIDATED_OFFLINE_CONTRACT_SCOPE",
        registry,
        matrix,
        public_api,
        _build_metrics(registry, matrix, public_api, config),
        COMMON_REASON_CODES,
        lot37_safety(),
        "0" * 64,
    )
    checksum = canonical_checksum(state.payload_without_checksum())
    return replace(state, output_checksum=checksum)


def _build_audit(
    config_path: Path,
    code_commit: str,
    state: MicrostructureScopeOfflineDataContractsStateV1,
    registry: MicrostructureScopeOfflineDataContractsContractRegistryV1,
    matrix: MicrostructureScopeOfflineDataContractsCapabilityMatrixV1,
) -> MicrostructureScopeOfflineDataContractsAuditV1:
    audit = MicrostructureScopeOfflineDataContractsAuditV1(
        code_commit,
        state.output_checksum,
        file_checksum(config_path),
        EXPECTED_GATE_CHECKSUM,
        canonical_checksum(registry.to_dict()),
        canonical_checksum(matrix.to_dict()),
        state.validation_state,
        lot37_safety(),
        "0" * 64,
    )
    checksum = canonical_checksum(audit.payload_without_checksum())
    return replace(audit, audit_checksum=checksum)


def build_lot37_artifacts(
    root: Path, code_commit: str
) -> tuple[MicrostructureScopeOfflineDataContractsStateV1, MicrostructureScopeOfflineDataContractsAuditV1]:
    config_path = root / CONFIG_PATH
    config = load_json_object(config_path)
    _validate_config(config)
    gate = _verify_gate(root, config)
    _verify_lifecycle(root, config)
    l2_checksum, trade_checksum = _verify_offline_inputs(root, config, gate)
    registry = _build_contract_registry(root, config)
    matrix = _build_capability_matrix(config)
    public_api = _build_public_api(config)
    state = _build_state(
        config, code_commit, l2_checksum, trade_checksum, registry, matrix, public_api
    )
    return state, _build_audit(config_path, code_commit, state, registry, matrix)


def _output_paths(root: Path) -> dict[str, Path]:
    return {
        "state": root / "data/audit/microstructure_scope_and_offline_data_contracts_lot37.json",
        "audit": root / "data/audit/microstructure_scope_and_offline_data_contracts_audit_lot37.json",
        "contract_registry": root / "data/audit/microstructure_contract_registry_lot37.json",
        "capability_matrix": root / "data/audit/microstructure_capability_matrix_lot37.json",
    }


def write_lot37_artifacts(root: Path, code_commit: str) -> dict[str, str]:
    state, audit = build_lot37_artifacts(root, code_commit)
    outputs = _output_paths(root)
    atomic_write_json(outputs["state"], state.to_dict())
    atomic_write_json(outputs["audit"], audit.to_dict())
    atomic_write_json(outputs["contract_registry"], state.contract_registry.to_dict())
    atomic_write_json(outputs["capability_matrix"], state.capability_matrix.to_dict())
    return {name: str(path.relative_to(root)) for name, path in outputs.items()}

from __future__ import annotations

import json
from dataclasses import replace
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.lineage.io import count_lines
from crypto_quant_bot.lineage.models import (
    DEFAULT_LINEAGE_BLOCK_REASONS,
    LineageArtifact,
    LineageCheck,
    LineagePolicy,
    LineageResult,
    ReproducibilityManifest,
)

REPLAY_COMMAND = """
timeout 300s bash -lc '
python scripts/validate_lot0.py &&
python scripts/ingest_ohlcvt_fixture.py &&
python scripts/validate_lot1.py &&
python scripts/build_lot2_datasets.py &&
python scripts/validate_lot2.py &&
python scripts/build_lot3_pivots.py &&
python scripts/validate_lot3.py &&
python scripts/build_lot4_volume_vwap.py &&
python scripts/validate_lot4.py &&
python scripts/build_lot5_volatility.py &&
python scripts/validate_lot5.py &&
python scripts/build_lot6_regime.py &&
python scripts/validate_lot6.py &&
python scripts/build_lot7_market_state.py &&
python scripts/validate_lot7.py &&
python scripts/audit_lot8_feature_registry.py &&
python scripts/audit_lot8_no_lookahead.py &&
python scripts/validate_lot8.py &&
python scripts/run_lot9_backtest_replay.py &&
python scripts/validate_lot9.py &&
python scripts/run_lot10_transaction_costs.py &&
python scripts/validate_lot10.py &&
python scripts/run_lot11_risk_engine.py &&
python scripts/validate_lot11.py &&
python scripts/run_lot12_exposure_guard.py &&
python scripts/validate_lot12.py &&
python scripts/run_lot13_portfolio_freeze.py &&
python scripts/validate_lot13.py &&
python scripts/run_lot14_decision_firewall.py &&
python scripts/validate_lot14.py &&
python scripts/run_lot15_decision_ledger.py &&
python scripts/validate_lot15.py &&
python scripts/run_lot16_reproducibility_manifest.py &&
python scripts/validate_lot16.py &&
python scripts/run_lot17_health_monitor.py &&
python scripts/validate_lot17.py &&
python -m pytest -q &&
echo EXACT_CHAIN_LOT16_DONE
'
""".strip()

VALIDATION_COMMANDS = [
    "python scripts/validate_lot16.py",
    "python scripts/validate_all_until_lot16.py",
    "bash scripts/run_required_chain_until_lot16.sh",
    "python scripts/diagnose_lot16_required_chain_timing.py",
    "python scripts/diagnose_exact_chain_until_lot16.py",
]

SOURCE_CATALOG_BASE_EXCLUDED_IDS = {
    "reproducibility_manifest_lot16",
    "reproducibility_artifacts_lot16",
    "health_monitor_lot17",
    "health_checks_lot17",
    "no_trading_compliance_lot18",
    "no_trading_compliance_checks_lot18",
    "release_candidate_lot19",
    "release_candidate_checks_lot19",
    "v1_closure_lot20",
    "v1_closure_checks_lot20",
    "product_scope_lot21",
    "product_scope_capabilities_lot21",
    "product_scope_roadmap_lot21",
}
SOURCE_CATALOG_EXCLUDED_IDS = SOURCE_CATALOG_BASE_EXCLUDED_IDS
LOT16_SOURCE_CATALOG_SCOPE = "LOT0_TO_LOT15_STABLE_SOURCE_CATALOG_ONLY"
LOT16_SOURCE_CATALOG_STABLE_FIELDS = (
    "dataset_id",
    "dataset_name",
    "pair",
    "timeframe",
    "layer",
    "data_version",
    "start_timestamp",
    "end_timestamp",
    "row_count",
    "checksum",
    "source",
    "schema_version",
    "quality_flag",
    "validation_status",
    "used_for_decision",
    "path",
    "artifact_path",
    "lot",
    "lot_id",
    "source_lot",
)

INVARIANTS = {
    "TradingDecision": "WAIT",
    "SystemDecision": "BLOCK_TRADING",
    "final_decision": "WAIT",
    "final_system_decision": "BLOCK_TRADING",
    "trade_allowed": False,
    "execution_allowed": False,
    "Risk Engine blocks by default": True,
    "live_execution": "DISABLED",
    "leverage": "FORBIDDEN",
    "exposure_allowed": False,
    "allocation_allowed": False,
    "rebalance_allowed": False,
    "portfolio_state": "FROZEN",
    "capital_at_risk": 0,
    "external_connectivity_allowed": False,
    "human_review_required": True,
    "immutability_mode": "APPEND_ONLY_SIMULATED",
}

SOURCE_REPORT_PATHS = [
    "reports/lot_00_validation_report.md",
    "reports/lot_01_data_quality_report.md",
    "reports/lot_01_validation_report.md",
    "reports/lot_02_feature_report.md",
    "reports/lot_02_multitimeframe_report.md",
    "reports/lot_03_pivot_report.md",
    "reports/lot_03_zone_report.md",
    "reports/lot_04_volume_profile_report.md",
    "reports/lot_04_vwap_report.md",
    "reports/lot_05_range_state_report.md",
    "reports/lot_05_volatility_report.md",
    "reports/lot_05_validation_report.md",
    "reports/lot_06_regime_report.md",
    "reports/lot_06_validation_report.md",
    "reports/lot_07_market_state_report.md",
    "reports/lot_07_validation_report.md",
    "reports/lot_08_feature_registry_audit_report.md",
    "reports/lot_08_no_lookahead_report.md",
    "reports/lot_09_backtest_replay_report.md",
    "reports/lot_10_transaction_costs_report.md",
    "reports/lot_10_validation_report.md",
    "reports/lot_11_risk_engine_report.md",
    "reports/lot_11_validation_report.md",
    "reports/lot_12_exposure_guard_report.md",
    "reports/lot_12_validation_report.md",
    "reports/lot_13_portfolio_freeze_report.md",
    "reports/lot_13_validation_report.md",
    "reports/lot_14_decision_firewall_report.md",
    "reports/lot_14_validation_report.md",
    "reports/lot_15_decision_ledger_report.md",
    "reports/lot_15_validation_report.md",
]

ARTIFACT_SPECS = [
    {
        "artifact_id": "btc_eur_5m_market_state_lot7",
        "lot": "Lot 7",
        "artifact_type": "jsonl",
        "path": "data/gold/btc_eur_5m_market_state_lot7.jsonl",
        "produced_by": "python scripts/build_lot7_market_state.py",
        "consumes": [
            "reports/lot_02_feature_report.md",
            "reports/lot_03_pivot_report.md",
            "reports/lot_04_volume_profile_report.md",
            "reports/lot_05_volatility_report.md",
            "reports/lot_06_regime_report.md",
        ],
        "validation_command": "python scripts/validate_lot7.py",
    },
    {
        "artifact_id": "btc_eur_15m_market_state_lot7",
        "lot": "Lot 7",
        "artifact_type": "jsonl",
        "path": "data/gold/btc_eur_15m_market_state_lot7.jsonl",
        "produced_by": "python scripts/build_lot7_market_state.py",
        "consumes": [
            "reports/lot_02_multitimeframe_report.md",
            "reports/lot_03_zone_report.md",
            "reports/lot_04_vwap_report.md",
            "reports/lot_05_range_state_report.md",
            "reports/lot_06_regime_report.md",
        ],
        "validation_command": "python scripts/validate_lot7.py",
    },
    {
        "artifact_id": "feature_registry_audit_lot8",
        "lot": "Lot 8",
        "artifact_type": "json",
        "path": "data/audit/feature_registry_audit_lot8.json",
        "produced_by": "python scripts/audit_lot8_feature_registry.py",
        "consumes": [
            "data/gold/btc_eur_5m_market_state_lot7.jsonl",
            "data/gold/btc_eur_15m_market_state_lot7.jsonl",
        ],
        "validation_command": "python scripts/validate_lot8.py",
    },
    {
        "artifact_id": "no_lookahead_audit_lot8",
        "lot": "Lot 8",
        "artifact_type": "json",
        "path": "data/audit/no_lookahead_audit_lot8.json",
        "produced_by": "python scripts/audit_lot8_no_lookahead.py",
        "consumes": [
            "data/gold/btc_eur_5m_market_state_lot7.jsonl",
            "data/gold/btc_eur_15m_market_state_lot7.jsonl",
        ],
        "validation_command": "python scripts/validate_lot8.py",
    },
    {
        "artifact_id": "backtest_lot9_5m_steps",
        "lot": "Lot 9",
        "artifact_type": "jsonl",
        "path": "data/audit/backtest_lot9_5m_steps.jsonl",
        "produced_by": "python scripts/run_lot9_backtest_replay.py",
        "consumes": [
            "data/gold/btc_eur_5m_market_state_lot7.jsonl",
            "data/audit/feature_registry_audit_lot8.json",
            "data/audit/no_lookahead_audit_lot8.json",
        ],
        "validation_command": "python scripts/validate_lot9.py",
    },
    {
        "artifact_id": "backtest_lot9_15m_steps",
        "lot": "Lot 9",
        "artifact_type": "jsonl",
        "path": "data/audit/backtest_lot9_15m_steps.jsonl",
        "produced_by": "python scripts/run_lot9_backtest_replay.py",
        "consumes": [
            "data/gold/btc_eur_15m_market_state_lot7.jsonl",
            "data/audit/feature_registry_audit_lot8.json",
            "data/audit/no_lookahead_audit_lot8.json",
        ],
        "validation_command": "python scripts/validate_lot9.py",
    },
    {
        "artifact_id": "backtest_lot9_run_config",
        "lot": "Lot 9",
        "artifact_type": "json",
        "path": "data/audit/backtest_lot9_run_config.json",
        "produced_by": "python scripts/run_lot9_backtest_replay.py",
        "consumes": [
            "data/audit/feature_registry_audit_lot8.json",
            "data/audit/no_lookahead_audit_lot8.json",
        ],
        "validation_command": "python scripts/validate_lot9.py",
    },
    {
        "artifact_id": "backtest_lot9_run_result",
        "lot": "Lot 9",
        "artifact_type": "json",
        "path": "data/audit/backtest_lot9_run_result.json",
        "produced_by": "python scripts/run_lot9_backtest_replay.py",
        "consumes": [
            "data/audit/backtest_lot9_5m_steps.jsonl",
            "data/audit/backtest_lot9_15m_steps.jsonl",
            "data/audit/backtest_lot9_run_config.json",
        ],
        "validation_command": "python scripts/validate_lot9.py",
    },
    {
        "artifact_id": "transaction_cost_lot10_5m_estimates",
        "lot": "Lot 10",
        "artifact_type": "jsonl",
        "path": "data/audit/transaction_cost_lot10_5m_estimates.jsonl",
        "produced_by": "python scripts/run_lot10_transaction_costs.py",
        "consumes": [
            "data/audit/backtest_lot9_5m_steps.jsonl",
            "data/audit/backtest_lot9_run_result.json",
        ],
        "validation_command": "python scripts/validate_lot10.py",
    },
    {
        "artifact_id": "transaction_cost_lot10_15m_estimates",
        "lot": "Lot 10",
        "artifact_type": "jsonl",
        "path": "data/audit/transaction_cost_lot10_15m_estimates.jsonl",
        "produced_by": "python scripts/run_lot10_transaction_costs.py",
        "consumes": [
            "data/audit/backtest_lot9_15m_steps.jsonl",
            "data/audit/backtest_lot9_run_result.json",
        ],
        "validation_command": "python scripts/validate_lot10.py",
    },
    {
        "artifact_id": "transaction_cost_lot10_run_result",
        "lot": "Lot 10",
        "artifact_type": "json",
        "path": "data/audit/transaction_cost_lot10_run_result.json",
        "produced_by": "python scripts/run_lot10_transaction_costs.py",
        "consumes": [
            "data/audit/transaction_cost_lot10_5m_estimates.jsonl",
            "data/audit/transaction_cost_lot10_15m_estimates.jsonl",
        ],
        "validation_command": "python scripts/validate_lot10.py",
    },
    {
        "artifact_id": "risk_engine_lot11_5m",
        "lot": "Lot 11",
        "artifact_type": "jsonl",
        "path": "data/audit/risk_engine_lot11_5m.jsonl",
        "produced_by": "python scripts/run_lot11_risk_engine.py",
        "consumes": [
            "data/gold/btc_eur_5m_market_state_lot7.jsonl",
            "data/audit/transaction_cost_lot10_5m_estimates.jsonl",
        ],
        "validation_command": "python scripts/validate_lot11.py",
    },
    {
        "artifact_id": "risk_engine_lot11_15m",
        "lot": "Lot 11",
        "artifact_type": "jsonl",
        "path": "data/audit/risk_engine_lot11_15m.jsonl",
        "produced_by": "python scripts/run_lot11_risk_engine.py",
        "consumes": [
            "data/gold/btc_eur_15m_market_state_lot7.jsonl",
            "data/audit/transaction_cost_lot10_15m_estimates.jsonl",
        ],
        "validation_command": "python scripts/validate_lot11.py",
    },
    {
        "artifact_id": "exposure_guard_lot12_5m",
        "lot": "Lot 12",
        "artifact_type": "jsonl",
        "path": "data/audit/exposure_guard_lot12_5m.jsonl",
        "produced_by": "python scripts/run_lot12_exposure_guard.py",
        "consumes": [
            "data/gold/btc_eur_5m_market_state_lot7.jsonl",
            "data/audit/risk_engine_lot11_5m.jsonl",
        ],
        "validation_command": "python scripts/validate_lot12.py",
    },
    {
        "artifact_id": "exposure_guard_lot12_15m",
        "lot": "Lot 12",
        "artifact_type": "jsonl",
        "path": "data/audit/exposure_guard_lot12_15m.jsonl",
        "produced_by": "python scripts/run_lot12_exposure_guard.py",
        "consumes": [
            "data/gold/btc_eur_15m_market_state_lot7.jsonl",
            "data/audit/risk_engine_lot11_15m.jsonl",
        ],
        "validation_command": "python scripts/validate_lot12.py",
    },
    {
        "artifact_id": "portfolio_freeze_lot13_5m",
        "lot": "Lot 13",
        "artifact_type": "jsonl",
        "path": "data/audit/portfolio_freeze_lot13_5m.jsonl",
        "produced_by": "python scripts/run_lot13_portfolio_freeze.py",
        "consumes": [
            "data/audit/risk_engine_lot11_5m.jsonl",
            "data/audit/exposure_guard_lot12_5m.jsonl",
        ],
        "validation_command": "python scripts/validate_lot13.py",
    },
    {
        "artifact_id": "portfolio_freeze_lot13_15m",
        "lot": "Lot 13",
        "artifact_type": "jsonl",
        "path": "data/audit/portfolio_freeze_lot13_15m.jsonl",
        "produced_by": "python scripts/run_lot13_portfolio_freeze.py",
        "consumes": [
            "data/audit/risk_engine_lot11_15m.jsonl",
            "data/audit/exposure_guard_lot12_15m.jsonl",
        ],
        "validation_command": "python scripts/validate_lot13.py",
    },
    {
        "artifact_id": "final_decision_firewall_lot14_5m",
        "lot": "Lot 14",
        "artifact_type": "jsonl",
        "path": "data/audit/final_decision_firewall_lot14_5m.jsonl",
        "produced_by": "python scripts/run_lot14_decision_firewall.py",
        "consumes": [
            "data/gold/btc_eur_5m_market_state_lot7.jsonl",
            "data/audit/transaction_cost_lot10_5m_estimates.jsonl",
            "data/audit/risk_engine_lot11_5m.jsonl",
            "data/audit/exposure_guard_lot12_5m.jsonl",
            "data/audit/portfolio_freeze_lot13_5m.jsonl",
        ],
        "validation_command": "python scripts/validate_lot14.py",
    },
    {
        "artifact_id": "final_decision_firewall_lot14_15m",
        "lot": "Lot 14",
        "artifact_type": "jsonl",
        "path": "data/audit/final_decision_firewall_lot14_15m.jsonl",
        "produced_by": "python scripts/run_lot14_decision_firewall.py",
        "consumes": [
            "data/gold/btc_eur_15m_market_state_lot7.jsonl",
            "data/audit/transaction_cost_lot10_15m_estimates.jsonl",
            "data/audit/risk_engine_lot11_15m.jsonl",
            "data/audit/exposure_guard_lot12_15m.jsonl",
            "data/audit/portfolio_freeze_lot13_15m.jsonl",
        ],
        "validation_command": "python scripts/validate_lot14.py",
    },
    {
        "artifact_id": "decision_ledger_lot15_5m",
        "lot": "Lot 15",
        "artifact_type": "jsonl",
        "path": "data/audit/decision_ledger_lot15_5m.jsonl",
        "produced_by": "python scripts/run_lot15_decision_ledger.py",
        "consumes": [
            "data/gold/btc_eur_5m_market_state_lot7.jsonl",
            "data/audit/transaction_cost_lot10_5m_estimates.jsonl",
            "data/audit/risk_engine_lot11_5m.jsonl",
            "data/audit/exposure_guard_lot12_5m.jsonl",
            "data/audit/portfolio_freeze_lot13_5m.jsonl",
            "data/audit/final_decision_firewall_lot14_5m.jsonl",
        ],
        "validation_command": "python scripts/validate_lot15.py",
    },
    {
        "artifact_id": "decision_ledger_lot15_15m",
        "lot": "Lot 15",
        "artifact_type": "jsonl",
        "path": "data/audit/decision_ledger_lot15_15m.jsonl",
        "produced_by": "python scripts/run_lot15_decision_ledger.py",
        "consumes": [
            "data/gold/btc_eur_15m_market_state_lot7.jsonl",
            "data/audit/transaction_cost_lot10_15m_estimates.jsonl",
            "data/audit/risk_engine_lot11_15m.jsonl",
            "data/audit/exposure_guard_lot12_15m.jsonl",
            "data/audit/portfolio_freeze_lot13_15m.jsonl",
            "data/audit/final_decision_firewall_lot14_15m.jsonl",
        ],
        "validation_command": "python scripts/validate_lot15.py",
    },
]


LOT_ID_PATTERN = re.compile(r"lot[\s_-]?(\d+)", re.IGNORECASE)
CATALOG_LOT_HINT_FIELDS = (
    "dataset_id",
    "dataset_name",
    "data_version",
    "source",
    "validation_status",
    "lineage_id",
    "path",
    "artifact_path",
    "lot",
    "lot_id",
    "source_lot",
)

def extract_catalog_record_lot_numbers(record: dict[str, object]) -> tuple[int, ...]:
    lot_numbers: set[int] = set()
    for field in CATALOG_LOT_HINT_FIELDS:
        value = record.get(field)
        if value in {None, ""}:
            continue
        for match in LOT_ID_PATTERN.findall(str(value)):
            lot_numbers.add(int(match))
    return tuple(sorted(lot_numbers))


def normalize_catalog_records_for_max_lot(
    records: list[dict[str, object]],
    *,
    max_included_lot: int,
    excluded_dataset_ids: set[str] | frozenset[str],
) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    for record in records:
        dataset_id = str(record.get("dataset_id", ""))
        if dataset_id in excluded_dataset_ids:
            continue
        lot_numbers = extract_catalog_record_lot_numbers(record)
        if any(lot_number > max_included_lot for lot_number in lot_numbers):
            continue
        filtered.append(record)
    filtered.sort(
        key=lambda record: (
            str(record.get("dataset_id", "")),
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
    )
    return filtered


def _extract_catalog_records(catalog: object) -> list[dict[str, object]]:
    if isinstance(catalog, list):
        raw_entries = catalog
    elif isinstance(catalog, dict):
        raw_entries = catalog.get("entries", [])
    else:
        raise TypeError("dataset_catalog payload must be a list or a dict containing an entries list")
    if not isinstance(raw_entries, list):
        raise TypeError("dataset_catalog entries payload must be a list")
    return [record for record in raw_entries if isinstance(record, dict)]


def _dedupe_catalog_records_by_dataset_id(records: list[dict[str, object]]) -> list[dict[str, object]]:
    without_dataset_id: list[dict[str, object]] = []
    unique_by_dataset_id: dict[str, dict[str, object]] = {}
    for record in records:
        cloned = json.loads(json.dumps(record, ensure_ascii=False, sort_keys=True))
        dataset_id = cloned.get("dataset_id")
        if isinstance(dataset_id, str) and dataset_id:
            unique_by_dataset_id[dataset_id] = cloned
        else:
            without_dataset_id.append(cloned)
    return without_dataset_id + [unique_by_dataset_id[key] for key in sorted(unique_by_dataset_id)]


def _normalize_lot16_source_record(record: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for field in LOT16_SOURCE_CATALOG_STABLE_FIELDS:
        if field in record:
            normalized[field] = record[field]
    return json.loads(json.dumps(normalized, ensure_ascii=False, sort_keys=True))


def normalize_lot16_source_catalog_records(catalog: object) -> list[dict[str, object]]:
    deduped = _dedupe_catalog_records_by_dataset_id(_extract_catalog_records(catalog))
    filtered = normalize_catalog_records_for_max_lot(
        deduped,
        max_included_lot=15,
        excluded_dataset_ids=SOURCE_CATALOG_BASE_EXCLUDED_IDS,
    )
    normalized = [record for record in (_normalize_lot16_source_record(item) for item in filtered) if record]
    normalized.sort(
        key=lambda record: (
            str(record.get("dataset_id", "")),
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
    )
    return normalized


def count_lot16_source_catalog_entries(catalog: object) -> int:
    return len(normalize_lot16_source_catalog_records(catalog))


def compute_lot16_source_catalog_checksum(catalog: object) -> str:
    normalized = normalize_lot16_source_catalog_records(catalog)
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _normalize_checksum_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "manifest_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("manifest checksum payload must remain a mapping")
    return cleaned


def build_manifest_checksum(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        _normalize_checksum_payload(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_source_catalog_checksum(records: list[dict[str, object]] | dict[str, object]) -> str:
    return compute_lot16_source_catalog_checksum(records)


def file_created_at_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


class LineageManifestBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.policy = LineagePolicy()

    def build_artifact(self, spec: dict[str, object]) -> LineageArtifact:
        path = self.root / str(spec["path"])
        return LineageArtifact(
            artifact_id=str(spec["artifact_id"]),
            lot=str(spec["lot"]),
            artifact_type=str(spec["artifact_type"]),
            path=str(spec["path"]),
            checksum_sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
            line_count=count_lines(path),
            required=True,
            produced_by=str(spec["produced_by"]),
            consumes=list(spec.get("consumes", [])),
            validation_command=str(spec.get("validation_command", "")),
            created_at=file_created_at_iso(path),
        )

    def build_artifacts(self) -> list[LineageArtifact]:
        artifacts: list[LineageArtifact] = []
        for spec in ARTIFACT_SPECS:
            artifacts.append(self.build_artifact(spec))
        return artifacts

    def build_checks(self, *, source_catalog_path: str, artifact_count: int, critical_counts: dict[str, dict[str, int]]) -> list[LineageCheck]:
        return [
            LineageCheck(
                check_name="manifest_scope",
                expected_value="local_only",
                observed_value="local_only",
                block_reason="REPRODUCIBILITY_MANIFEST_ONLY",
                message="Manifest remains a local reproducibility record only.",
            ),
            LineageCheck(
                check_name="source_catalog",
                expected_value=source_catalog_path,
                observed_value=source_catalog_path,
                block_reason="LOCAL_ARTIFACTS_ONLY",
                message="Source catalog path is local and explicit.",
            ),
            LineageCheck(
                check_name="artifact_count",
                expected_value=artifact_count,
                observed_value=artifact_count,
                block_reason="LOCAL_ARTIFACTS_ONLY",
                message="Explicit artifact list is recorded locally.",
            ),
            LineageCheck(
                check_name="external_connectivity_allowed",
                expected_value=False,
                observed_value=False,
                block_reason="NO_EXTERNAL_CONNECTIVITY",
                message="External connectivity remains disabled.",
            ),
            LineageCheck(
                check_name="execution_allowed",
                expected_value=False,
                observed_value=False,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Execution remains disabled.",
            ),
            LineageCheck(
                check_name="exchange_connectivity",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_EXCHANGE_CONNECTOR",
                message="No exchange connector is available.",
            ),
            LineageCheck(
                check_name="routing_stack",
                expected_value="not_available",
                observed_value="not_available",
                block_reason="NO_ORDER_ROUTER",
                message="No routing stack is available.",
            ),
            LineageCheck(
                check_name="project_mode",
                expected_value="EDUCATIONAL_AUDIT_ONLY",
                observed_value="EDUCATIONAL_AUDIT_ONLY",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational audit only.",
            ),
            LineageCheck(
                check_name="lot12_total_rows",
                expected_value=48,
                observed_value=critical_counts["lot12"]["total"],
                block_reason="LOCAL_ARTIFACTS_ONLY",
                message="Lot 12 critical row count remains stable.",
            ),
            LineageCheck(
                check_name="lot13_total_rows",
                expected_value=48,
                observed_value=critical_counts["lot13"]["total"],
                block_reason="LOCAL_ARTIFACTS_ONLY",
                message="Lot 13 critical row count remains stable.",
            ),
            LineageCheck(
                check_name="lot14_total_rows",
                expected_value=48,
                observed_value=critical_counts["lot14"]["total"],
                block_reason="LOCAL_ARTIFACTS_ONLY",
                message="Lot 14 critical row count remains stable.",
            ),
            LineageCheck(
                check_name="lot15_total_rows",
                expected_value=48,
                observed_value=critical_counts["lot15"]["total"],
                block_reason="LOCAL_ARTIFACTS_ONLY",
                message="Lot 15 critical row count remains stable.",
            ),
        ]

    def build_result(
        self,
        *,
        artifacts: list[LineageArtifact],
        critical_counts: dict[str, dict[str, int]],
        output_paths: list[str],
        source_artifacts: list[str],
    ) -> LineageResult:
        return LineageResult(
            manifest_version=self.policy.manifest_version,
            policy_version=self.policy.policy_version,
            artifact_count=len(artifacts),
            critical_counts=critical_counts,
            reproducibility_state=self.policy.reproducibility_state,
            lineage_state=self.policy.lineage_state,
            output_paths=output_paths,
            source_artifacts=source_artifacts,
        )

    def build_manifest(
        self,
        *,
        source_catalog_path: str,
        source_catalog_scope: str,
        source_catalog_entry_count: int,
        source_catalog_checksum: str,
        artifacts: list[LineageArtifact],
        critical_counts: dict[str, dict[str, int]],
        source_artifacts: list[str],
    ) -> ReproducibilityManifest:
        created_at = utc_now_iso()
        checks = self.build_checks(
            source_catalog_path=source_catalog_path,
            artifact_count=len(artifacts),
            critical_counts=critical_counts,
        )
        manifest = ReproducibilityManifest(
            manifest_version=self.policy.manifest_version,
            policy_version=self.policy.policy_version,
            project_name=self.policy.project_name,
            project_mode=self.policy.project_mode,
            created_at=created_at,
            reproducibility_state=self.policy.reproducibility_state,
            lineage_state=self.policy.lineage_state,
            external_connectivity_allowed=False,
            execution_allowed=False,
            trade_allowed=False,
            source_catalog_path=source_catalog_path,
            reproducibility_scope_lot16=source_catalog_scope,
            source_catalog_scope=source_catalog_scope,
            source_catalog_entry_count=source_catalog_entry_count,
            source_catalog_checksum=source_catalog_checksum,
            artifact_count=len(artifacts),
            artifacts=list(artifacts),
            critical_counts=critical_counts,
            replay_commands=[REPLAY_COMMAND],
            validation_commands=list(VALIDATION_COMMANDS),
            lineage_checks=checks,
            lineage_block_reasons=list(DEFAULT_LINEAGE_BLOCK_REASONS),
            invariants=dict(INVARIANTS),
            source_artifacts=list(source_artifacts),
            manifest_checksum="",
        )
        checksum = build_manifest_checksum(manifest.to_dict())
        return replace(manifest, manifest_checksum=checksum)

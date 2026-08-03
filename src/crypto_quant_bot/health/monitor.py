from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.health.io import count_lines, load_json, load_jsonl
from crypto_quant_bot.health.models import (
    DEFAULT_HEALTH_BLOCK_REASONS,
    HealthCheck,
    HealthMonitorResult,
    HealthPolicy,
    HealthSnapshot,
)
from crypto_quant_bot.lineage import (
    build_manifest_checksum,
    build_source_catalog_checksum,
    normalize_catalog_records_for_max_lot,
)

DATASET_CATALOG_PATH = "data/audit/dataset_catalog.json"
LOT16_MANIFEST_PATH = "data/audit/reproducibility_manifest_lot16.json"
LOT16_ARTIFACTS_PATH = "data/audit/reproducibility_artifacts_lot16.jsonl"
HEALTH_MONITOR_OUTPUT_PATH = "data/audit/health_monitor_lot17.json"
HEALTH_CHECKS_OUTPUT_PATH = "data/audit/health_checks_lot17.jsonl"
HEALTH_REPORT_OUTPUT_PATH = "reports/lot_17_health_monitor_report.md"
HEALTH_VALIDATION_REPORT_PATH = "reports/lot_17_validation_report.md"

EXPECTED_CRITICAL_COUNTS = {
    "lot12": {"5m": 36, "15m": 12, "total": 48},
    "lot13": {"5m": 36, "15m": 12, "total": 48},
    "lot14": {"5m": 36, "15m": 12, "total": 48},
    "lot15": {"5m": 36, "15m": 12, "total": 48},
}

CRITICAL_COUNT_PATHS = {
    "lot12": {
        "5m": "data/audit/exposure_guard_lot12_5m.jsonl",
        "15m": "data/audit/exposure_guard_lot12_15m.jsonl",
    },
    "lot13": {
        "5m": "data/audit/portfolio_freeze_lot13_5m.jsonl",
        "15m": "data/audit/portfolio_freeze_lot13_15m.jsonl",
    },
    "lot14": {
        "5m": "data/audit/final_decision_firewall_lot14_5m.jsonl",
        "15m": "data/audit/final_decision_firewall_lot14_15m.jsonl",
    },
    "lot15": {
        "5m": "data/audit/decision_ledger_lot15_5m.jsonl",
        "15m": "data/audit/decision_ledger_lot15_15m.jsonl",
    },
}

REQUIRED_ARTIFACT_PATHS = [
    "data/audit/exposure_guard_lot12_5m.jsonl",
    "data/audit/exposure_guard_lot12_15m.jsonl",
    "data/audit/portfolio_freeze_lot13_5m.jsonl",
    "data/audit/portfolio_freeze_lot13_15m.jsonl",
    "data/audit/final_decision_firewall_lot14_5m.jsonl",
    "data/audit/final_decision_firewall_lot14_15m.jsonl",
    "data/audit/decision_ledger_lot15_5m.jsonl",
    "data/audit/decision_ledger_lot15_15m.jsonl",
    LOT16_MANIFEST_PATH,
    LOT16_ARTIFACTS_PATH,
]

REQUIRED_REPORT_PATHS = [
    "reports/lot_12_exposure_guard_report.md",
    "reports/lot_12_validation_report.md",
    "reports/lot_13_portfolio_freeze_report.md",
    "reports/lot_13_validation_report.md",
    "reports/lot_14_decision_firewall_report.md",
    "reports/lot_14_validation_report.md",
    "reports/lot_15_decision_ledger_report.md",
    "reports/lot_15_validation_report.md",
    "reports/lot_16_reproducibility_report.md",
    "reports/lot_16_validation_report.md",
]

REQUIRED_SCRIPT_PATHS = [
    "scripts/run_lot12_exposure_guard.py",
    "scripts/validate_lot12.py",
    "scripts/validate_all_until_lot12.py",
    "scripts/run_required_chain_until_lot12.sh",
    "scripts/run_lot13_portfolio_freeze.py",
    "scripts/validate_lot13.py",
    "scripts/validate_all_until_lot13.py",
    "scripts/run_required_chain_until_lot13.sh",
    "scripts/run_lot14_decision_firewall.py",
    "scripts/validate_lot14.py",
    "scripts/validate_all_until_lot14.py",
    "scripts/run_required_chain_until_lot14.sh",
    "scripts/run_lot15_decision_ledger.py",
    "scripts/validate_lot15.py",
    "scripts/validate_all_until_lot15.py",
    "scripts/run_required_chain_until_lot15.sh",
    "scripts/run_lot16_reproducibility_manifest.py",
    "scripts/validate_lot16.py",
    "scripts/validate_all_until_lot16.py",
    "scripts/run_required_chain_until_lot16.sh",
]

REQUIRED_DIAGNOSTIC_PATHS = [
    "scripts/diagnose_pytest_resolution.py",
    "scripts/diagnose_exact_chain_return_shell.py",
    "scripts/diagnose_lot12_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot12.py",
    "scripts/diagnose_lot13_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot13.py",
    "scripts/diagnose_lot14_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot14.py",
    "scripts/diagnose_lot15_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot15.py",
    "scripts/diagnose_lot16_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot16.py",
]

EXPECTED_LOT16_CATALOG_IDS = {
    "reproducibility_manifest_lot16",
    "reproducibility_artifacts_lot16",
}
HEALTH_CATALOG_BASE_EXCLUDED_IDS = {
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
HEALTH_CATALOG_EXCLUDED_IDS = HEALTH_CATALOG_BASE_EXCLUDED_IDS
HEALTH_PYTEST_EXPECTED = "python -m pytest -q"
HEALTH_EXACT_CHAIN_EXPECTED = "EXACT_CHAIN_LOT17_DONE"
HEALTH_INVARIANTS = {
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

def build_dataset_catalog_checksum(records: list[dict[str, Any]]) -> str:
    filtered = normalize_catalog_records_for_max_lot(
        list(records),
        max_included_lot=16,
        excluded_dataset_ids=HEALTH_CATALOG_BASE_EXCLUDED_IDS,
    )
    encoded = json.dumps(
        filtered,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _normalize_health_checksum_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "health_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("health checksum payload must remain a mapping")
    return cleaned


def build_health_checksum(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        _normalize_health_checksum_payload(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _all_exist(root: Path, relative_paths: list[str]) -> bool:
    return all((root / relative_path).exists() for relative_path in relative_paths)


def default_source_artifacts() -> list[str]:
    return sorted(
        {
            DATASET_CATALOG_PATH,
            LOT16_MANIFEST_PATH,
            LOT16_ARTIFACTS_PATH,
            *REQUIRED_ARTIFACT_PATHS,
            *REQUIRED_REPORT_PATHS,
            *REQUIRED_SCRIPT_PATHS,
            *REQUIRED_DIAGNOSTIC_PATHS,
        }
    )


class LocalHealthMonitor:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.policy = HealthPolicy()

    def default_policy(self) -> HealthPolicy:
        return self.policy

    def _compute_critical_counts(self) -> tuple[bool, dict[str, dict[str, int]]]:
        observed: dict[str, dict[str, int]] = {}
        for lot_name, mapping in CRITICAL_COUNT_PATHS.items():
            counts: dict[str, int] = {}
            for timeframe, relative_path in mapping.items():
                path = self.root / relative_path
                counts[timeframe] = count_lines(path)
            counts["total"] = counts["5m"] + counts["15m"]
            observed[lot_name] = counts
        return observed == EXPECTED_CRITICAL_COUNTS, observed

    def _validate_checksum_references(
        self,
        *,
        catalog_rows: list[dict[str, Any]],
        manifest: dict[str, Any],
        artifact_rows: list[dict[str, Any]],
    ) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if manifest.get("artifact_count") != len(artifact_rows):
            errors.append("artifact_count mismatch")
        if build_manifest_checksum(manifest) != manifest.get("manifest_checksum"):
            errors.append("manifest_checksum mismatch")
        if build_source_catalog_checksum(catalog_rows) != manifest.get("source_catalog_checksum"):
            errors.append("source_catalog_checksum mismatch")
        catalog_ids = [str(record.get("dataset_id", "")) for record in catalog_rows if isinstance(record, dict)]
        if len(catalog_ids) != len(set(catalog_ids)):
            errors.append("dataset_catalog duplicate dataset_id")
        if EXPECTED_LOT16_CATALOG_IDS - set(catalog_ids):
            errors.append("dataset_catalog missing Lot 16 ids")
        manifest_artifacts = manifest.get("artifacts")
        if not isinstance(manifest_artifacts, list) or len(manifest_artifacts) != len(artifact_rows):
            errors.append("manifest artifacts mismatch")
            manifest_by_id: dict[str, dict[str, Any]] = {}
        else:
            manifest_by_id = {
                str(row.get("artifact_id", "")): row
                for row in manifest_artifacts
                if isinstance(row, dict)
            }
        for row in artifact_rows:
            artifact_id = str(row.get("artifact_id", ""))
            path = self.root / str(row.get("path", ""))
            if not path.exists():
                errors.append(f"missing artifact path: {path}")
                continue
            if sha256_file(path) != row.get("checksum_sha256"):
                errors.append(f"artifact checksum mismatch: {artifact_id}")
            if count_lines(path) != int(row.get("line_count", -1)):
                errors.append(f"artifact line_count mismatch: {artifact_id}")
            manifest_row = manifest_by_id.get(artifact_id)
            if manifest_row is None:
                errors.append(f"manifest missing artifact: {artifact_id}")
                continue
            if manifest_row.get("path") != row.get("path"):
                errors.append(f"manifest path mismatch: {artifact_id}")
            if manifest_row.get("checksum_sha256") != row.get("checksum_sha256"):
                errors.append(f"manifest checksum reference mismatch: {artifact_id}")
        return not errors, errors

    def build_checks(
        self,
        *,
        dataset_catalog_readable: bool,
        lot16_manifest_readable: bool,
        lot16_artifacts_readable: bool,
        required_artifacts_present: bool,
        required_reports_present: bool,
        required_scripts_present: bool,
        required_diagnostics_present: bool,
        critical_counts_valid: bool,
        critical_counts_observed: dict[str, dict[str, int]],
        checksum_references_valid: bool,
        checksum_errors: list[str],
    ) -> list[HealthCheck]:
        checks = [
            HealthCheck(
                check_name="dataset_catalog_readable",
                status="PASS" if dataset_catalog_readable else "BLOCK",
                expected_value=True,
                observed_value=dataset_catalog_readable,
                block_reason="LOCAL_HEALTH_MONITOR_ONLY",
                message="dataset_catalog.json remains readable locally.",
            ),
            HealthCheck(
                check_name="lot16_manifest_readable",
                status="PASS" if lot16_manifest_readable else "BLOCK",
                expected_value=True,
                observed_value=lot16_manifest_readable,
                block_reason="REPRODUCIBILITY_MANIFEST_REQUIRED",
                message="Lot 16 manifest is readable locally.",
            ),
            HealthCheck(
                check_name="lot16_artifacts_readable",
                status="PASS" if lot16_artifacts_readable else "BLOCK",
                expected_value=True,
                observed_value=lot16_artifacts_readable,
                block_reason="REPRODUCIBILITY_MANIFEST_REQUIRED",
                message="Lot 16 artifact JSONL is readable locally.",
            ),
            HealthCheck(
                check_name="required_artifacts_present",
                status="PASS" if required_artifacts_present else "BLOCK",
                expected_value=True,
                observed_value=required_artifacts_present,
                block_reason="REPRODUCIBILITY_MANIFEST_REQUIRED",
                message="Critical Lot 12 to Lot 16 artifacts exist.",
            ),
            HealthCheck(
                check_name="required_reports_present",
                status="PASS" if required_reports_present else "BLOCK",
                expected_value=True,
                observed_value=required_reports_present,
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Critical audit reports exist locally.",
            ),
            HealthCheck(
                check_name="required_scripts_present",
                status="PASS" if required_scripts_present else "BLOCK",
                expected_value=True,
                observed_value=required_scripts_present,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Required run and validation scripts exist locally.",
            ),
            HealthCheck(
                check_name="required_diagnostics_present",
                status="PASS" if required_diagnostics_present else "BLOCK",
                expected_value=True,
                observed_value=required_diagnostics_present,
                block_reason="NO_EXTERNAL_CONNECTIVITY",
                message="Required timing and exact-chain diagnostics exist locally.",
            ),
            HealthCheck(
                check_name="critical_counts_valid",
                status="PASS" if critical_counts_valid else "BLOCK",
                expected_value=EXPECTED_CRITICAL_COUNTS,
                observed_value=critical_counts_observed,
                block_reason="NO_ORDER_ROUTER",
                message="Critical 36/12/48 counts remain consistent.",
            ),
            HealthCheck(
                check_name="checksum_references_valid",
                status="PASS" if checksum_references_valid else "BLOCK",
                expected_value=True,
                observed_value=checksum_references_valid,
                block_reason="REPRODUCIBILITY_MANIFEST_REQUIRED",
                message="Lot 16 checksum references remain locally verifiable."
                if checksum_references_valid
                else "; ".join(checksum_errors),
            ),
        ]
        return checks

    def build_snapshot(self) -> HealthSnapshot:
        dataset_catalog_path = self.root / DATASET_CATALOG_PATH
        lot16_manifest_path = self.root / LOT16_MANIFEST_PATH
        lot16_artifacts_path = self.root / LOT16_ARTIFACTS_PATH

        catalog_rows: list[dict[str, Any]] = []
        dataset_catalog_readable = False
        dataset_catalog_checksum = ""
        if dataset_catalog_path.exists():
            catalog_payload = load_json(dataset_catalog_path)
            if isinstance(catalog_payload, list):
                catalog_rows = [row for row in catalog_payload if isinstance(row, dict)]
                dataset_catalog_readable = True
                dataset_catalog_checksum = build_dataset_catalog_checksum(catalog_rows)

        manifest: dict[str, Any] = {}
        lot16_manifest_readable = False
        lot16_manifest_checksum = ""
        if lot16_manifest_path.exists():
            manifest_payload = load_json(lot16_manifest_path)
            if isinstance(manifest_payload, dict):
                manifest = manifest_payload
                lot16_manifest_readable = True
                lot16_manifest_checksum = sha256_file(lot16_manifest_path)

        artifact_rows: list[dict[str, Any]] = []
        lot16_artifacts_readable = False
        if lot16_artifacts_path.exists():
            artifact_rows = load_jsonl(lot16_artifacts_path, max_lines=256)
            lot16_artifacts_readable = True

        required_artifacts_present = _all_exist(self.root, REQUIRED_ARTIFACT_PATHS)
        required_reports_present = _all_exist(self.root, REQUIRED_REPORT_PATHS)
        required_scripts_present = _all_exist(self.root, REQUIRED_SCRIPT_PATHS)
        required_diagnostics_present = _all_exist(self.root, REQUIRED_DIAGNOSTIC_PATHS)
        critical_counts_valid, critical_counts_observed = self._compute_critical_counts()
        checksum_references_valid, checksum_errors = self._validate_checksum_references(
            catalog_rows=catalog_rows,
            manifest=manifest,
            artifact_rows=artifact_rows,
        )
        checks = self.build_checks(
            dataset_catalog_readable=dataset_catalog_readable,
            lot16_manifest_readable=lot16_manifest_readable,
            lot16_artifacts_readable=lot16_artifacts_readable,
            required_artifacts_present=required_artifacts_present,
            required_reports_present=required_reports_present,
            required_scripts_present=required_scripts_present,
            required_diagnostics_present=required_diagnostics_present,
            critical_counts_valid=critical_counts_valid,
            critical_counts_observed=critical_counts_observed,
            checksum_references_valid=checksum_references_valid,
            checksum_errors=checksum_errors,
        )
        core_state_ok = all(
            [
                dataset_catalog_readable,
                lot16_manifest_readable,
                lot16_artifacts_readable,
                required_artifacts_present,
                required_reports_present,
                required_scripts_present,
                required_diagnostics_present,
                critical_counts_valid,
                checksum_references_valid,
            ]
        )
        snapshot = HealthSnapshot(
            health_version=self.policy.health_version,
            policy_version=self.policy.policy_version,
            project_name=self.policy.project_name,
            project_mode=self.policy.project_mode,
            created_at=utc_now_iso(),
            health_state=self.policy.health_state if core_state_ok else "UNHEALTHY_FOR_LOCAL_AUDIT",
            integrity_state=self.policy.integrity_state if checksum_references_valid else "INTEGRITY_CHECK_FAILED",
            reproducibility_state=self.policy.reproducibility_state if core_state_ok else "REPRODUCIBILITY_CHECK_FAILED",
            monitoring_mode=self.policy.monitoring_mode,
            external_connectivity_allowed=self.policy.external_connectivity_allowed,
            execution_allowed=self.policy.execution_allowed,
            trade_allowed=self.policy.trade_allowed,
            dataset_catalog_path=DATASET_CATALOG_PATH,
            dataset_catalog_readable=dataset_catalog_readable,
            dataset_catalog_checksum=dataset_catalog_checksum,
            lot16_manifest_path=LOT16_MANIFEST_PATH,
            lot16_manifest_readable=lot16_manifest_readable,
            lot16_manifest_checksum=lot16_manifest_checksum,
            lot16_artifacts_path=LOT16_ARTIFACTS_PATH,
            lot16_artifacts_readable=lot16_artifacts_readable,
            artifact_count=len(artifact_rows),
            required_artifacts_present=required_artifacts_present,
            required_reports_present=required_reports_present,
            required_scripts_present=required_scripts_present,
            required_diagnostics_present=required_diagnostics_present,
            critical_counts_valid=critical_counts_valid,
            checksum_references_valid=checksum_references_valid,
            pytest_expected=HEALTH_PYTEST_EXPECTED,
            exact_chain_expected=HEALTH_EXACT_CHAIN_EXPECTED,
            health_checks=checks,
            health_block_reasons=list(DEFAULT_HEALTH_BLOCK_REASONS),
            invariants=dict(HEALTH_INVARIANTS),
            source_artifacts=default_source_artifacts(),
            health_checksum="",
        )
        return replace(snapshot, health_checksum=build_health_checksum(snapshot.to_dict()))

    def build_result(self, *, snapshot: HealthSnapshot, output_paths: list[str]) -> HealthMonitorResult:
        return HealthMonitorResult(
            artifact_count=snapshot.artifact_count,
            health_check_count=len(snapshot.health_checks),
            health_state=snapshot.health_state,
            integrity_state=snapshot.integrity_state,
            reproducibility_state=snapshot.reproducibility_state,
            output_paths=output_paths,
            source_artifacts=list(snapshot.source_artifacts),
        )

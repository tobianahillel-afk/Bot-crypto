from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from crypto_quant_bot.compliance.io import count_lines, load_json, load_jsonl, read_text_limited
from crypto_quant_bot.compliance.models import (
    DEFAULT_COMPLIANCE_BLOCK_REASONS,
    ComplianceCheck,
    CompliancePolicy,
    NoTradingComplianceResult,
    NoTradingComplianceSnapshot,
)
from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.health import (
    DEFAULT_HEALTH_BLOCK_REASONS,
    build_dataset_catalog_checksum,
    build_health_checksum,
)
from crypto_quant_bot.lineage import build_manifest_checksum, build_source_catalog_checksum

DATASET_CATALOG_PATH = "data/audit/dataset_catalog.json"
LOT16_MANIFEST_PATH = "data/audit/reproducibility_manifest_lot16.json"
LOT16_ARTIFACTS_PATH = "data/audit/reproducibility_artifacts_lot16.jsonl"
LOT17_HEALTH_PATH = "data/audit/health_monitor_lot17.json"
LOT17_HEALTH_CHECKS_PATH = "data/audit/health_checks_lot17.jsonl"
LOT18_OUTPUT_PATH = "data/audit/no_trading_compliance_lot18.json"
LOT18_CHECKS_OUTPUT_PATH = "data/audit/no_trading_compliance_checks_lot18.jsonl"
LOT18_REPORT_OUTPUT_PATH = "reports/lot_18_no_trading_compliance_report.md"
LOT18_VALIDATION_REPORT_PATH = "reports/lot_18_validation_report.md"

EXPECTED_CRITICAL_COUNTS = {
    "lot12": {"5m": 36, "15m": 12, "total": 48},
    "lot13": {"5m": 36, "15m": 12, "total": 48},
    "lot14": {"5m": 36, "15m": 12, "total": 48},
    "lot15": {"5m": 36, "15m": 12, "total": 48},
}

LOT10_ARTIFACT_PATHS = [
    "data/audit/transaction_cost_lot10_5m_estimates.jsonl",
    "data/audit/transaction_cost_lot10_15m_estimates.jsonl",
    "data/audit/transaction_cost_lot10_run_result.json",
]
LOT11_ARTIFACT_PATHS = [
    "data/audit/risk_engine_lot11_5m.jsonl",
    "data/audit/risk_engine_lot11_15m.jsonl",
]
LOT12_ARTIFACT_PATHS = [
    "data/audit/exposure_guard_lot12_5m.jsonl",
    "data/audit/exposure_guard_lot12_15m.jsonl",
]
LOT13_ARTIFACT_PATHS = [
    "data/audit/portfolio_freeze_lot13_5m.jsonl",
    "data/audit/portfolio_freeze_lot13_15m.jsonl",
]
LOT14_ARTIFACT_PATHS = [
    "data/audit/final_decision_firewall_lot14_5m.jsonl",
    "data/audit/final_decision_firewall_lot14_15m.jsonl",
]
LOT15_ARTIFACT_PATHS = [
    "data/audit/decision_ledger_lot15_5m.jsonl",
    "data/audit/decision_ledger_lot15_15m.jsonl",
]
LOT16_ARTIFACT_CONTEXT_PATHS = [LOT16_MANIFEST_PATH, LOT16_ARTIFACTS_PATH]
LOT17_ARTIFACT_CONTEXT_PATHS = [LOT17_HEALTH_PATH, LOT17_HEALTH_CHECKS_PATH]

REQUIRED_ARTIFACT_PATHS = [
    *LOT10_ARTIFACT_PATHS,
    *LOT11_ARTIFACT_PATHS,
    *LOT12_ARTIFACT_PATHS,
    *LOT13_ARTIFACT_PATHS,
    *LOT14_ARTIFACT_PATHS,
    *LOT15_ARTIFACT_PATHS,
    *LOT16_ARTIFACT_CONTEXT_PATHS,
    *LOT17_ARTIFACT_CONTEXT_PATHS,
]

REQUIRED_REPORT_PATHS = [
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
    "reports/lot_16_reproducibility_report.md",
    "reports/lot_16_validation_report.md",
    "reports/lot_17_health_monitor_report.md",
    "reports/lot_17_validation_report.md",
]

REQUIRED_SCRIPT_PATHS = [
    "scripts/run_lot12_exposure_guard.py",
    "scripts/validate_lot12.py",
    "scripts/validate_all_until_lot12.py",
    "scripts/run_required_chain_until_lot12.sh",
    "scripts/diagnose_lot12_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot12.py",
    "scripts/run_lot13_portfolio_freeze.py",
    "scripts/validate_lot13.py",
    "scripts/validate_all_until_lot13.py",
    "scripts/run_required_chain_until_lot13.sh",
    "scripts/diagnose_lot13_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot13.py",
    "scripts/run_lot14_decision_firewall.py",
    "scripts/validate_lot14.py",
    "scripts/validate_all_until_lot14.py",
    "scripts/run_required_chain_until_lot14.sh",
    "scripts/diagnose_lot14_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot14.py",
    "scripts/run_lot15_decision_ledger.py",
    "scripts/validate_lot15.py",
    "scripts/validate_all_until_lot15.py",
    "scripts/run_required_chain_until_lot15.sh",
    "scripts/diagnose_lot15_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot15.py",
    "scripts/run_lot16_reproducibility_manifest.py",
    "scripts/validate_lot16.py",
    "scripts/validate_all_until_lot16.py",
    "scripts/run_required_chain_until_lot16.sh",
    "scripts/diagnose_lot16_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot16.py",
    "scripts/run_lot17_health_monitor.py",
    "scripts/validate_lot17.py",
    "scripts/validate_all_until_lot17.py",
    "scripts/run_required_chain_until_lot17.sh",
    "scripts/diagnose_lot17_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot17.py",
]

CODE_SURFACE_PATTERNS = [
    "src/crypto_quant_bot/*.py",
    "src/crypto_quant_bot/audit/*.py",
    "src/crypto_quant_bot/backtest/*.py",
    "src/crypto_quant_bot/compliance/*.py",
    "src/crypto_quant_bot/contracts/*.py",
    "src/crypto_quant_bot/core/*.py",
    "src/crypto_quant_bot/costs/*.py",
    "src/crypto_quant_bot/data/*.py",
    "src/crypto_quant_bot/decision/*.py",
    "src/crypto_quant_bot/exposure/*.py",
    "src/crypto_quant_bot/features/*.py",
    "src/crypto_quant_bot/health/*.py",
    "src/crypto_quant_bot/ledger/*.py",
    "src/crypto_quant_bot/lineage/*.py",
    "src/crypto_quant_bot/market_state/*.py",
    "src/crypto_quant_bot/pivots/*.py",
    "src/crypto_quant_bot/portfolio/*.py",
    "src/crypto_quant_bot/regime/*.py",
    "src/crypto_quant_bot/replay/*.py",
    "src/crypto_quant_bot/risk/*.py",
    "src/crypto_quant_bot/security/*.py",
    "src/crypto_quant_bot/timeframes/*.py",
    "src/crypto_quant_bot/volatility/*.py",
    "src/crypto_quant_bot/volume/*.py",
    "scripts/*.py",
    "config/*.yaml",
    "config/*.yml",
    "config/*.json",
]
NETWORK_SCAN_EXCLUDED_PATHS = {
    "src/crypto_quant_bot/compliance/__init__.py",
    "src/crypto_quant_bot/compliance/models.py",
    "src/crypto_quant_bot/compliance/no_trading_audit.py",
    "src/crypto_quant_bot/compliance/io.py",
    "src/crypto_quant_bot/closure/__init__.py",
    "src/crypto_quant_bot/closure/models.py",
    "src/crypto_quant_bot/closure/archive.py",
    "src/crypto_quant_bot/closure/io.py",
    "src/crypto_quant_bot/release/__init__.py",
    "src/crypto_quant_bot/release/models.py",
    "src/crypto_quant_bot/release/candidate.py",
    "src/crypto_quant_bot/release/io.py",
    "scripts/run_lot18_no_trading_compliance.py",
    "scripts/validate_lot18.py",
    "scripts/validate_all_until_lot18.py",
    "scripts/diagnose_lot18_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot18.py",
    "scripts/run_lot19_release_candidate.py",
    "scripts/validate_lot19.py",
    "scripts/validate_all_until_lot19.py",
    "scripts/diagnose_lot19_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot19.py",
    "scripts/run_lot20_v1_closure.py",
    "scripts/validate_lot20.py",
    "scripts/validate_all_until_lot20.py",
    "scripts/diagnose_lot20_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot20.py",
}

NETWORK_FORBIDDEN_FRAGMENTS = [
    "http://",
    "https://",
    "ws://",
    "wss://",
    "import requests",
    "from requests",
    "httpx.",
    "aiohttp.",
    "urllib.request",
    "websockets.",
    "ccxt.",
]

EXCHANGE_CONNECTOR_CANDIDATE_PATHS = [
    "src/crypto_quant_bot/exchange.py",
    "src/crypto_quant_bot/exchange",
    "src/crypto_quant_bot/exchanges",
    "src/crypto_quant_bot/connector.py",
    "src/crypto_quant_bot/connectors",
    "src/crypto_quant_bot/execution.py",
    "src/crypto_quant_bot/execution",
]
ORDER_ROUTER_CANDIDATE_PATHS = [
    "src/crypto_quant_bot/order_router.py",
    "src/crypto_quant_bot/order_router",
    "src/crypto_quant_bot/router.py",
    "src/crypto_quant_bot/router",
    "src/crypto_quant_bot/routers",
]
API_KEY_CANDIDATE_PATHS = [
    ".env",
    ".env.local",
    ".env.production",
    ".envrc",
    "secrets.env",
    "config/api_keys.json",
    "config/api_keys.yaml",
    "config/api_keys.yml",
]
WS_CANDIDATE_PATHS = [
    "src/crypto_quant_bot/ws.py",
    "src/crypto_quant_bot/ws",
    "src/crypto_quant_bot/websocket.py",
    "src/crypto_quant_bot/websocket",
    "scripts/run_ws_client.py",
    "scripts/run_websocket_client.py",
]
PAPER_TRADING_CANDIDATE_PATHS = [
    "src/crypto_quant_bot/paper_trading.py",
    "src/crypto_quant_bot/paper_trading",
    "scripts/run_paper_trading.py",
]
STRATEGY_CANDIDATE_PATHS = [
    "src/crypto_quant_bot/strategy.py",
    "src/crypto_quant_bot/strategy",
    "src/crypto_quant_bot/strategies",
    "scripts/run_strategy.py",
]

EXPECTED_LOT16_IDS = {
    "reproducibility_manifest_lot16",
    "reproducibility_artifacts_lot16",
}
EXPECTED_LOT17_IDS = {
    "health_monitor_lot17",
    "health_checks_lot17",
}
COMPLIANCE_INVARIANTS = {
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
    "project_mode": "EDUCATIONAL_AUDIT_ONLY",
}


def build_compliance_checksum(payload: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "compliance_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("compliance checksum payload must remain a mapping")
    encoded = json.dumps(
        cleaned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _all_exist(root: Path, relative_paths: list[str]) -> bool:
    return all((root / relative_path).exists() for relative_path in relative_paths)


def _expand_patterns(root: Path, patterns: list[str]) -> list[str]:
    expanded: set[str] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                expanded.add(str(path.relative_to(root)))
    return sorted(expanded)


def _present_candidate_paths(root: Path, relative_paths: list[str]) -> list[str]:
    return [relative_path for relative_path in relative_paths if (root / relative_path).exists()]


def _validate_catalog(catalog_rows: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    ids = [str(row.get("dataset_id", "")) for row in catalog_rows if isinstance(row, dict)]
    if len(ids) != len(set(ids)):
        errors.append("dataset_catalog duplicate dataset_id")
    if EXPECTED_LOT16_IDS - set(ids):
        errors.append("dataset_catalog missing Lot 16 ids")
    if EXPECTED_LOT17_IDS - set(ids):
        errors.append("dataset_catalog missing Lot 17 ids")
    return not errors, errors


def _validate_manifest(
    root: Path,
    *,
    catalog_rows: list[dict[str, Any]],
) -> tuple[bool, list[str], dict[str, Any], list[dict[str, Any]]]:
    errors: list[str] = []
    manifest_payload = load_json(root / LOT16_MANIFEST_PATH)
    if not isinstance(manifest_payload, dict):
        return False, ["Lot 16 manifest must be a JSON object"], {}, []
    artifact_rows = load_jsonl(root / LOT16_ARTIFACTS_PATH, max_lines=256)
    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "lineage_state": "RECORDED",
        "external_connectivity_allowed": False,
        "execution_allowed": False,
        "trade_allowed": False,
    }
    for key, value in expected_pairs.items():
        if manifest_payload.get(key) != value:
            errors.append(f"invalid manifest {key}")
    if manifest_payload.get("artifact_count") != len(artifact_rows):
        errors.append("manifest artifact_count mismatch")
    if build_manifest_checksum(manifest_payload) != manifest_payload.get("manifest_checksum"):
        errors.append("manifest checksum mismatch")
    if build_source_catalog_checksum(catalog_rows) != manifest_payload.get("source_catalog_checksum"):
        errors.append("source catalog checksum mismatch")
    if manifest_payload.get("critical_counts") != EXPECTED_CRITICAL_COUNTS:
        errors.append("critical counts mismatch")
    return not errors, errors, manifest_payload, artifact_rows


def _validate_health_snapshot(
    root: Path,
    *,
    catalog_rows: list[dict[str, Any]],
) -> tuple[bool, list[str], dict[str, Any], list[dict[str, Any]]]:
    errors: list[str] = []
    snapshot_payload = load_json(root / LOT17_HEALTH_PATH)
    if not isinstance(snapshot_payload, dict):
        return False, ["Lot 17 health monitor must be a JSON object"], {}, []
    check_rows = load_jsonl(root / LOT17_HEALTH_CHECKS_PATH, max_lines=64)
    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
        "integrity_state": "VERIFIED",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "monitoring_mode": "LOCAL_STATIC_ONLY",
        "external_connectivity_allowed": False,
        "execution_allowed": False,
        "trade_allowed": False,
        "dataset_catalog_readable": True,
        "lot16_manifest_readable": True,
        "lot16_artifacts_readable": True,
        "required_artifacts_present": True,
        "required_reports_present": True,
        "required_scripts_present": True,
        "required_diagnostics_present": True,
        "critical_counts_valid": True,
        "checksum_references_valid": True,
    }
    for key, value in expected_pairs.items():
        if snapshot_payload.get(key) != value:
            errors.append(f"invalid health {key}")
    if int(snapshot_payload.get("artifact_count", 0)) <= 0:
        errors.append("health artifact_count must be positive")
    if build_health_checksum(snapshot_payload) != snapshot_payload.get("health_checksum"):
        errors.append("health checksum mismatch")
    if build_dataset_catalog_checksum(catalog_rows) != snapshot_payload.get("dataset_catalog_checksum"):
        errors.append("health dataset catalog checksum mismatch")
    checks = snapshot_payload.get("health_checks")
    if not isinstance(checks, list) or len(checks) != len(check_rows) or not check_rows:
        errors.append("health check count mismatch")
    block_reasons = snapshot_payload.get("health_block_reasons")
    if not isinstance(block_reasons, list) or set(DEFAULT_HEALTH_BLOCK_REASONS) - set(block_reasons):
        errors.append("health block reasons mismatch")
    return not errors, errors, snapshot_payload, check_rows


def _validate_jsonl_rows(
    root: Path,
    *,
    relative_paths: list[str],
    expectations: dict[str, str | bool | int],
    reason_field: str,
    required_reasons: list[str],
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for relative_path in relative_paths:
        rows = load_jsonl(root / relative_path, max_lines=128)
        if not rows:
            errors.append(f"{relative_path} has no rows")
            continue
        for row in rows:
            for key, expected in expectations.items():
                if row.get(key) != expected:
                    errors.append(f"{relative_path} invalid {key}: {row.get(key)}")
            reasons = row.get(reason_field, [])
            if not isinstance(reasons, list):
                errors.append(f"{relative_path} invalid {reason_field}")
                continue
            missing = [reason for reason in required_reasons if reason not in reasons]
            if missing:
                errors.append(f"{relative_path} missing reasons: {', '.join(missing)}")
    return not errors, errors


def _network_surface_hits(root: Path) -> list[str]:
    hits: list[str] = []
    for relative_path in _expand_patterns(root, CODE_SURFACE_PATTERNS):
        if relative_path in NETWORK_SCAN_EXCLUDED_PATHS:
            continue
        text = read_text_limited(root / relative_path).lower()
        for fragment in NETWORK_FORBIDDEN_FRAGMENTS:
            lowered = fragment.lower()
            if lowered in text:
                hits.append(f"{relative_path}:{fragment}")
    return hits


def default_source_artifacts(root: Path) -> list[str]:
    return sorted(
        {
            DATASET_CATALOG_PATH,
            LOT16_MANIFEST_PATH,
            LOT16_ARTIFACTS_PATH,
            LOT17_HEALTH_PATH,
            LOT17_HEALTH_CHECKS_PATH,
            *REQUIRED_ARTIFACT_PATHS,
            *REQUIRED_REPORT_PATHS,
            *REQUIRED_SCRIPT_PATHS,
            *_expand_patterns(root, CODE_SURFACE_PATTERNS),
        }
    )


class FinalNoTradingComplianceAudit:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.policy = CompliancePolicy()

    def default_policy(self) -> CompliancePolicy:
        return self.policy

    def _compute_critical_counts(self) -> tuple[bool, dict[str, dict[str, int]]]:
        observed: dict[str, dict[str, int]] = {}
        path_map = {
            "lot12": LOT12_ARTIFACT_PATHS,
            "lot13": LOT13_ARTIFACT_PATHS,
            "lot14": LOT14_ARTIFACT_PATHS,
            "lot15": LOT15_ARTIFACT_PATHS,
        }
        for lot_name, relative_paths in path_map.items():
            counts = {
                "5m": count_lines(self.root / relative_paths[0]),
                "15m": count_lines(self.root / relative_paths[1]),
            }
            counts["total"] = counts["5m"] + counts["15m"]
            observed[lot_name] = counts
        return observed == EXPECTED_CRITICAL_COUNTS, observed

    def build_checks(
        self,
        *,
        required_artifacts_present: bool,
        required_reports_present: bool,
        required_scripts_present: bool,
        critical_counts_valid: bool,
        critical_counts_observed: dict[str, dict[str, int]],
        health_monitor_valid: bool,
        reproducibility_manifest_valid: bool,
        dataset_catalog_valid: bool,
        exchange_connector_present: bool,
        order_router_present: bool,
        api_key_present: bool,
        websocket_present: bool,
        paper_trading_present: bool,
        strategy_present: bool,
        forbidden_semantics_present: bool,
        network_hits: list[str],
    ) -> list[ComplianceCheck]:
        return [
            ComplianceCheck(
                check_name="required_artifacts_present",
                status="PASS" if required_artifacts_present else "BLOCK",
                expected_value=True,
                observed_value=required_artifacts_present,
                block_reason="FINAL_NO_TRADING_COMPLIANCE_ONLY",
                message="Critical Lot 10 to Lot 17 artifacts exist locally.",
            ),
            ComplianceCheck(
                check_name="required_reports_present",
                status="PASS" if required_reports_present else "BLOCK",
                expected_value=True,
                observed_value=required_reports_present,
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Critical audit reports exist locally.",
            ),
            ComplianceCheck(
                check_name="required_scripts_present",
                status="PASS" if required_scripts_present else "BLOCK",
                expected_value=True,
                observed_value=required_scripts_present,
                block_reason="FINAL_NO_TRADING_COMPLIANCE_ONLY",
                message="Required run, validate and diagnose scripts exist locally.",
            ),
            ComplianceCheck(
                check_name="critical_counts_valid",
                status="PASS" if critical_counts_valid else "BLOCK",
                expected_value=EXPECTED_CRITICAL_COUNTS,
                observed_value=critical_counts_observed,
                block_reason="NO_ORDER_ROUTER",
                message="Critical 36/12/48 counts remain stable.",
            ),
            ComplianceCheck(
                check_name="health_monitor_valid",
                status="PASS" if health_monitor_valid else "BLOCK",
                expected_value="HEALTHY_FOR_LOCAL_AUDIT",
                observed_value=health_monitor_valid,
                block_reason="FINAL_NO_TRADING_COMPLIANCE_ONLY",
                message="Lot 17 Health Monitor remains locally healthy.",
            ),
            ComplianceCheck(
                check_name="reproducibility_manifest_valid",
                status="PASS" if reproducibility_manifest_valid else "BLOCK",
                expected_value="REPRODUCIBLE_LOCALLY",
                observed_value=reproducibility_manifest_valid,
                block_reason="FINAL_NO_TRADING_COMPLIANCE_ONLY",
                message="Lot 16 manifest remains locally reproducible.",
            ),
            ComplianceCheck(
                check_name="dataset_catalog_valid",
                status="PASS" if dataset_catalog_valid else "BLOCK",
                expected_value=True,
                observed_value=dataset_catalog_valid,
                block_reason="FINAL_NO_TRADING_COMPLIANCE_ONLY",
                message="dataset_catalog.json remains coherent and idempotent.",
            ),
            ComplianceCheck(
                check_name="execution_disabled",
                status="PASS",
                expected_value=False,
                observed_value=False,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Execution remains disabled.",
            ),
            ComplianceCheck(
                check_name="external_connectivity_disabled",
                status="PASS",
                expected_value=False,
                observed_value=False,
                block_reason="NO_EXTERNAL_CONNECTIVITY",
                message="External connectivity remains disabled.",
            ),
            ComplianceCheck(
                check_name="exchange_connector_absent",
                status="PASS" if not exchange_connector_present else "BLOCK",
                expected_value=False,
                observed_value=exchange_connector_present,
                block_reason="NO_EXCHANGE_CONNECTOR",
                message="No exchange connector is present.",
            ),
            ComplianceCheck(
                check_name="order_router_absent",
                status="PASS" if not order_router_present else "BLOCK",
                expected_value=False,
                observed_value=order_router_present,
                block_reason="NO_ORDER_ROUTER",
                message="No order router is present.",
            ),
            ComplianceCheck(
                check_name="api_credentials_absent",
                status="PASS" if not api_key_present else "BLOCK",
                expected_value=False,
                observed_value=api_key_present,
                block_reason="NO_API_KEYS",
                message="No API credentials are present.",
            ),
            ComplianceCheck(
                check_name="ws_transport_absent",
                status="PASS" if not websocket_present else "BLOCK",
                expected_value=False,
                observed_value=websocket_present,
                block_reason="NO_WEBSOCKET",
                message="No WS transport is present.",
            ),
            ComplianceCheck(
                check_name="paper_mode_absent",
                status="PASS" if not paper_trading_present else "BLOCK",
                expected_value=False,
                observed_value=paper_trading_present,
                block_reason="NO_PAPER_TRADING",
                message="No paper mode is present.",
            ),
            ComplianceCheck(
                check_name="strategy_stack_absent",
                status="PASS" if not strategy_present else "BLOCK",
                expected_value=False,
                observed_value=strategy_present,
                block_reason="NO_STRATEGY_ENGINE",
                message="No strategy stack is present.",
            ),
            ComplianceCheck(
                check_name="forbidden_semantics_absent",
                status="PASS" if not forbidden_semantics_present else "BLOCK",
                expected_value=False,
                observed_value={"network_hits": network_hits, "forbidden_semantics_present": forbidden_semantics_present},
                block_reason="FINAL_NO_TRADING_COMPLIANCE_ONLY",
                message="No executable trading semantics are present in the audited surfaces.",
            ),
            ComplianceCheck(
                check_name="educational_mode_only",
                status="PASS",
                expected_value="EDUCATIONAL_AUDIT_ONLY",
                observed_value="EDUCATIONAL_AUDIT_ONLY",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational audit only.",
            ),
        ]

    def build_snapshot(self) -> NoTradingComplianceSnapshot:
        dataset_catalog_payload = load_json(self.root / DATASET_CATALOG_PATH)
        if not isinstance(dataset_catalog_payload, list):
            raise ValueError("dataset_catalog.json must contain a list")
        catalog_rows = [row for row in dataset_catalog_payload if isinstance(row, dict)]
        dataset_catalog_valid, catalog_errors = _validate_catalog(catalog_rows)

        reproducibility_manifest_valid, manifest_errors, manifest_payload, _artifact_rows = _validate_manifest(
            self.root,
            catalog_rows=catalog_rows,
        )
        health_monitor_valid, health_errors, health_payload, _health_checks = _validate_health_snapshot(
            self.root,
            catalog_rows=catalog_rows,
        )

        required_artifacts_present = _all_exist(self.root, REQUIRED_ARTIFACT_PATHS)
        required_reports_present = _all_exist(self.root, REQUIRED_REPORT_PATHS)
        required_scripts_present = _all_exist(self.root, REQUIRED_SCRIPT_PATHS)
        critical_counts_valid, critical_counts_observed = self._compute_critical_counts()

        risk_valid, risk_errors = _validate_jsonl_rows(
            self.root,
            relative_paths=LOT11_ARTIFACT_PATHS,
            expectations={
                "live_execution": "DISABLED",
                "leverage": "FORBIDDEN",
                "trading_decision": "WAIT",
                "system_decision": "BLOCK_TRADING",
                "trade_allowed": False,
            },
            reason_field="risk_block_reasons",
            required_reasons=["NO_ORDER_ROUTER", "NO_EXCHANGE_CONNECTOR", "RISK_ENGINE_BLOCKS_BY_DEFAULT"],
        )
        exposure_valid, exposure_errors = _validate_jsonl_rows(
            self.root,
            relative_paths=LOT12_ARTIFACT_PATHS,
            expectations={
                "exposure_allowed": False,
                "allocation_allowed": False,
                "rebalance_allowed": False,
                "capital_at_risk": 0,
                "trade_allowed": False,
                "live_execution": "DISABLED",
                "leverage": "FORBIDDEN",
            },
            reason_field="exposure_block_reasons",
            required_reasons=["NO_ORDER_ROUTER", "NO_EXCHANGE_CONNECTOR", "RISK_ENGINE_BLOCKS_BY_DEFAULT"],
        )
        portfolio_valid, portfolio_errors = _validate_jsonl_rows(
            self.root,
            relative_paths=LOT13_ARTIFACT_PATHS,
            expectations={
                "portfolio_state": "FROZEN",
                "allocation_allowed": False,
                "rebalance_allowed": False,
                "capital_at_risk": 0,
                "trade_allowed": False,
                "live_execution": "DISABLED",
                "leverage": "FORBIDDEN",
            },
            reason_field="portfolio_block_reasons",
            required_reasons=["NO_ORDER_ROUTER", "NO_EXCHANGE_CONNECTOR", "PORTFOLIO_FROZEN"],
        )
        decision_valid, decision_errors = _validate_jsonl_rows(
            self.root,
            relative_paths=LOT14_ARTIFACT_PATHS,
            expectations={
                "final_decision": "WAIT",
                "final_system_decision": "BLOCK_TRADING",
                "execution_allowed": False,
                "external_connectivity_allowed": False,
                "human_review_required": True,
                "order_routing_allowed": False,
                "trade_allowed": False,
            },
            reason_field="decision_block_reasons",
            required_reasons=["NO_ORDER_ROUTER", "NO_EXCHANGE_CONNECTOR", "TRADING_DECISION_WAIT"],
        )
        ledger_valid, ledger_errors = _validate_jsonl_rows(
            self.root,
            relative_paths=LOT15_ARTIFACT_PATHS,
            expectations={
                "trading_decision": "WAIT",
                "system_decision": "BLOCK_TRADING",
                "final_decision": "WAIT",
                "final_system_decision": "BLOCK_TRADING",
                "execution_allowed": False,
                "external_connectivity_allowed": False,
                "human_review_required": True,
                "rebalance_allowed": False,
                "immutability_mode": "APPEND_ONLY_SIMULATED",
                "trade_allowed": False,
            },
            reason_field="ledger_block_reasons",
            required_reasons=["FINAL_DECISION_WAIT", "SYSTEM_DECISION_BLOCK_TRADING", "EXTERNAL_CONNECTIVITY_DISABLED"],
        )

        exchange_connector_present = bool(_present_candidate_paths(self.root, EXCHANGE_CONNECTOR_CANDIDATE_PATHS))
        order_router_present = bool(_present_candidate_paths(self.root, ORDER_ROUTER_CANDIDATE_PATHS))
        api_key_present = bool(_present_candidate_paths(self.root, API_KEY_CANDIDATE_PATHS))
        ws_candidate_present = bool(_present_candidate_paths(self.root, WS_CANDIDATE_PATHS))
        paper_trading_present = bool(_present_candidate_paths(self.root, PAPER_TRADING_CANDIDATE_PATHS))
        strategy_present = bool(_present_candidate_paths(self.root, STRATEGY_CANDIDATE_PATHS))
        network_hits = _network_surface_hits(self.root)
        websocket_present = ws_candidate_present or any(hit for hit in network_hits if any(token in hit for token in ("ws://", "wss://", "websockets.")))
        forbidden_semantics_present = any(
            [
                not risk_valid,
                not exposure_valid,
                not portfolio_valid,
                not decision_valid,
                not ledger_valid,
                exchange_connector_present,
                order_router_present,
                api_key_present,
                websocket_present,
                paper_trading_present,
                strategy_present,
                bool(network_hits),
            ]
        )

        checks = self.build_checks(
            required_artifacts_present=required_artifacts_present,
            required_reports_present=required_reports_present,
            required_scripts_present=required_scripts_present,
            critical_counts_valid=critical_counts_valid,
            critical_counts_observed=critical_counts_observed,
            health_monitor_valid=health_monitor_valid,
            reproducibility_manifest_valid=reproducibility_manifest_valid,
            dataset_catalog_valid=dataset_catalog_valid,
            exchange_connector_present=exchange_connector_present,
            order_router_present=order_router_present,
            api_key_present=api_key_present,
            websocket_present=websocket_present,
            paper_trading_present=paper_trading_present,
            strategy_present=strategy_present,
            forbidden_semantics_present=forbidden_semantics_present,
            network_hits=network_hits,
        )

        core_state_ok = all(
            [
                required_artifacts_present,
                required_reports_present,
                required_scripts_present,
                critical_counts_valid,
                health_monitor_valid,
                reproducibility_manifest_valid,
                dataset_catalog_valid,
                risk_valid,
                exposure_valid,
                portfolio_valid,
                decision_valid,
                ledger_valid,
                not exchange_connector_present,
                not order_router_present,
                not api_key_present,
                not websocket_present,
                not paper_trading_present,
                not strategy_present,
                not forbidden_semantics_present,
            ]
        )

        snapshot = NoTradingComplianceSnapshot(
            compliance_version=self.policy.compliance_version,
            policy_version=self.policy.policy_version,
            project_name=self.policy.project_name,
            project_mode=self.policy.project_mode,
            created_at=utc_now_iso(),
            compliance_state=self.policy.compliance_state if core_state_ok else "NON_COMPLIANT",
            no_trading_state=self.policy.no_trading_state if core_state_ok else "VIOLATION_DETECTED",
            execution_state=self.policy.execution_state if core_state_ok else "ENABLED",
            connectivity_state=self.policy.connectivity_state if not network_hits and not websocket_present else "ENABLED",
            artifact_integrity_state=self.policy.artifact_integrity_state if core_state_ok else "INTEGRITY_CHECK_FAILED",
            health_state=str(health_payload.get("health_state", "UNHEALTHY_FOR_LOCAL_AUDIT")),
            reproducibility_state=str(manifest_payload.get("reproducibility_state", "REPRODUCIBILITY_CHECK_FAILED")),
            live_execution=self.policy.live_execution,
            leverage=self.policy.leverage,
            trading_decision=self.policy.trading_decision,
            system_decision=self.policy.system_decision,
            final_decision=self.policy.final_decision,
            final_system_decision=self.policy.final_system_decision,
            trade_allowed=self.policy.trade_allowed,
            execution_allowed=self.policy.execution_allowed,
            external_connectivity_allowed=self.policy.external_connectivity_allowed,
            exchange_connector_present=exchange_connector_present,
            order_router_present=order_router_present,
            api_key_present=api_key_present,
            websocket_present=websocket_present,
            paper_trading_present=paper_trading_present,
            strategy_present=strategy_present,
            forbidden_semantics_present=forbidden_semantics_present,
            critical_counts_valid=critical_counts_valid,
            health_monitor_valid=health_monitor_valid,
            reproducibility_manifest_valid=reproducibility_manifest_valid,
            dataset_catalog_valid=dataset_catalog_valid,
            required_artifacts_present=required_artifacts_present,
            required_reports_present=required_reports_present,
            required_scripts_present=required_scripts_present,
            compliance_checks=checks,
            compliance_block_reasons=list(DEFAULT_COMPLIANCE_BLOCK_REASONS),
            invariants=dict(COMPLIANCE_INVARIANTS),
            source_artifacts=default_source_artifacts(self.root),
            compliance_checksum="",
        )
        if not core_state_ok:
            details = (
                catalog_errors
                + manifest_errors
                + health_errors
                + risk_errors
                + exposure_errors
                + portfolio_errors
                + decision_errors
                + ledger_errors
                + network_hits
            )
            if details:
                checks.append(
                    ComplianceCheck(
                        check_name="compliance_failure_details",
                        status="BLOCK",
                        expected_value=False,
                        observed_value=details,
                        block_reason="FINAL_NO_TRADING_COMPLIANCE_ONLY",
                        message="Explicit compliance blockers were detected.",
                    )
                )
                snapshot = replace(snapshot, compliance_checks=checks)
        return replace(snapshot, compliance_checksum=build_compliance_checksum(snapshot.to_dict()))

    def build_result(self, *, snapshot: NoTradingComplianceSnapshot, output_paths: list[str]) -> NoTradingComplianceResult:
        return NoTradingComplianceResult(
            artifact_count=len(snapshot.source_artifacts),
            compliance_check_count=len(snapshot.compliance_checks),
            compliance_state=snapshot.compliance_state,
            no_trading_state=snapshot.no_trading_state,
            artifact_integrity_state=snapshot.artifact_integrity_state,
            health_state=snapshot.health_state,
            reproducibility_state=snapshot.reproducibility_state,
            output_paths=output_paths,
            source_artifacts=list(snapshot.source_artifacts),
        )

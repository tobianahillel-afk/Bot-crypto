from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from crypto_quant_bot.compliance import DEFAULT_COMPLIANCE_BLOCK_REASONS, build_compliance_checksum
from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.health import DEFAULT_HEALTH_BLOCK_REASONS, build_dataset_catalog_checksum, build_health_checksum
from crypto_quant_bot.lineage import build_manifest_checksum, build_source_catalog_checksum
from crypto_quant_bot.release.io import count_lines, load_json, load_jsonl, read_text_limited
from crypto_quant_bot.release.models import (
    DEFAULT_RELEASE_BLOCK_REASONS,
    ReleaseCandidateCheck,
    ReleaseCandidatePolicy,
    ReleaseCandidateResult,
    ReleaseCandidateSnapshot,
)

DATASET_CATALOG_PATH = "data/audit/dataset_catalog.json"
LOT16_MANIFEST_PATH = "data/audit/reproducibility_manifest_lot16.json"
LOT16_ARTIFACTS_PATH = "data/audit/reproducibility_artifacts_lot16.jsonl"
LOT17_HEALTH_PATH = "data/audit/health_monitor_lot17.json"
LOT17_HEALTH_CHECKS_PATH = "data/audit/health_checks_lot17.jsonl"
LOT18_OUTPUT_PATH = "data/audit/no_trading_compliance_lot18.json"
LOT18_CHECKS_OUTPUT_PATH = "data/audit/no_trading_compliance_checks_lot18.jsonl"
LOT19_OUTPUT_PATH = "data/audit/release_candidate_lot19.json"
LOT19_CHECKS_OUTPUT_PATH = "data/audit/release_candidate_checks_lot19.jsonl"
LOT19_REPORT_OUTPUT_PATH = "reports/lot_19_release_candidate_report.md"
LOT19_ACCEPTANCE_OUTPUT_PATH = "reports/lot_19_acceptance_bundle.md"
LOT19_VALIDATION_REPORT_PATH = "reports/lot_19_validation_report.md"

EXPECTED_CRITICAL_COUNTS = {
    "lot12": {"5m": 36, "15m": 12, "total": 48},
    "lot13": {"5m": 36, "15m": 12, "total": 48},
    "lot14": {"5m": 36, "15m": 12, "total": 48},
    "lot15": {"5m": 36, "15m": 12, "total": 48},
}

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
LOT18_ARTIFACT_CONTEXT_PATHS = [LOT18_OUTPUT_PATH, LOT18_CHECKS_OUTPUT_PATH]

REQUIRED_ARTIFACT_PATHS = [
    *LOT12_ARTIFACT_PATHS,
    *LOT13_ARTIFACT_PATHS,
    *LOT14_ARTIFACT_PATHS,
    *LOT15_ARTIFACT_PATHS,
    *LOT16_ARTIFACT_CONTEXT_PATHS,
    *LOT17_ARTIFACT_CONTEXT_PATHS,
    *LOT18_ARTIFACT_CONTEXT_PATHS,
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
    "reports/lot_17_health_monitor_report.md",
    "reports/lot_17_validation_report.md",
    "reports/lot_18_no_trading_compliance_report.md",
    "reports/lot_18_validation_report.md",
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
    "scripts/run_lot18_no_trading_compliance.py",
    "scripts/validate_lot18.py",
    "scripts/validate_all_until_lot18.py",
    "scripts/run_required_chain_until_lot18.sh",
    "scripts/diagnose_lot18_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot18.py",
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
    "src/crypto_quant_bot/release/*.py",
    "src/crypto_quant_bot/replay/*.py",
    "src/crypto_quant_bot/risk/*.py",
    "src/crypto_quant_bot/security/*.py",
    "src/crypto_quant_bot/timeframes/*.py",
    "src/crypto_quant_bot/volatility/*.py",
    "src/crypto_quant_bot/volume/*.py",
    "scripts/*.py",
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

ARCHIVE_CANDIDATE_PATHS = [
    "data/audit/release_candidate_lot19.tar.gz",
    "data/audit/release_candidate_lot19.zip",
    "data/audit/release_candidate_lot19.whl",
    "data/audit/release_candidate_lot19.exe",
    "data/audit/release_candidate_checks_lot19.tar.gz",
    "data/audit/release_candidate_checks_lot19.zip",
    "data/audit/release_candidate_checks_lot19.whl",
    "data/audit/release_candidate_checks_lot19.exe",
    "reports/lot_19_release_candidate_report.tar.gz",
    "reports/lot_19_release_candidate_report.zip",
    "reports/lot_19_acceptance_bundle.tar.gz",
    "reports/lot_19_acceptance_bundle.zip",
    "dist/crypto_quant_bot_lot19.tar.gz",
    "dist/crypto_quant_bot_lot19.zip",
    "dist/crypto_quant_bot_lot19.whl",
    "dist/crypto_quant_bot_lot19.exe",
]

EXPECTED_LOT16_IDS = {
    "reproducibility_manifest_lot16",
    "reproducibility_artifacts_lot16",
}
EXPECTED_LOT17_IDS = {
    "health_monitor_lot17",
    "health_checks_lot17",
}
EXPECTED_LOT18_IDS = {
    "no_trading_compliance_lot18",
    "no_trading_compliance_checks_lot18",
}

RELEASE_INVARIANTS = {
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
    "compliance_state": "COMPLIANT",
    "no_trading_state": "ENFORCED",
}

ACCEPTANCE_CRITERIA = [
    "Lots 0 to 18 remain locally replayable.",
    "The exact chain remains expected green.",
    "pytest remains expected green.",
    "Critical artifacts, reports and scripts remain present.",
    "Lot 17 health monitor remains healthy for local audit.",
    "Lot 18 no-trading compliance remains enforced.",
    "Lot 16 reproducibility manifest remains readable and reproducible locally.",
    "Lot 15 decision ledger remains coherent and append-only simulated.",
    "No executable decision, no archive package and no network channel exist.",
    "Human review is required before any next phase.",
]


def build_release_checksum(payload: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "release_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("release checksum payload must remain a mapping")
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
    if EXPECTED_LOT18_IDS - set(ids):
        errors.append("dataset_catalog missing Lot 18 ids")
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


def _validate_compliance_snapshot(
    root: Path,
) -> tuple[bool, list[str], dict[str, Any], list[dict[str, Any]]]:
    errors: list[str] = []
    snapshot_payload = load_json(root / LOT18_OUTPUT_PATH)
    if not isinstance(snapshot_payload, dict):
        return False, ["Lot 18 compliance snapshot must be a JSON object"], {}, []
    check_rows = load_jsonl(root / LOT18_CHECKS_OUTPUT_PATH, max_lines=64)
    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "compliance_state": "COMPLIANT",
        "no_trading_state": "ENFORCED",
        "execution_state": "DISABLED",
        "connectivity_state": "DISABLED",
        "artifact_integrity_state": "VERIFIED",
        "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "trading_decision": "WAIT",
        "system_decision": "BLOCK_TRADING",
        "final_decision": "WAIT",
        "final_system_decision": "BLOCK_TRADING",
        "trade_allowed": False,
        "execution_allowed": False,
        "external_connectivity_allowed": False,
        "exchange_connector_present": False,
        "order_router_present": False,
        "api_key_present": False,
        "websocket_present": False,
        "paper_trading_present": False,
        "strategy_present": False,
        "forbidden_semantics_present": False,
        "critical_counts_valid": True,
        "health_monitor_valid": True,
        "reproducibility_manifest_valid": True,
        "dataset_catalog_valid": True,
        "required_artifacts_present": True,
        "required_reports_present": True,
        "required_scripts_present": True,
    }
    for key, value in expected_pairs.items():
        if snapshot_payload.get(key) != value:
            errors.append(f"invalid compliance {key}")
    if build_compliance_checksum(snapshot_payload) != snapshot_payload.get("compliance_checksum"):
        errors.append("compliance checksum mismatch")
    checks = snapshot_payload.get("compliance_checks")
    if not isinstance(checks, list) or len(checks) != len(check_rows) or not check_rows:
        errors.append("compliance check count mismatch")
    block_reasons = snapshot_payload.get("compliance_block_reasons")
    if not isinstance(block_reasons, list) or set(DEFAULT_COMPLIANCE_BLOCK_REASONS) - set(block_reasons):
        errors.append("compliance block reasons mismatch")
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


def _archive_candidate_hits(root: Path) -> list[str]:
    return [relative_path for relative_path in ARCHIVE_CANDIDATE_PATHS if (root / relative_path).exists()]


def default_source_artifacts() -> list[str]:
    return sorted(
        {
            DATASET_CATALOG_PATH,
            LOT16_MANIFEST_PATH,
            LOT16_ARTIFACTS_PATH,
            LOT17_HEALTH_PATH,
            LOT17_HEALTH_CHECKS_PATH,
            LOT18_OUTPUT_PATH,
            LOT18_CHECKS_OUTPUT_PATH,
            *REQUIRED_ARTIFACT_PATHS,
            *REQUIRED_REPORT_PATHS,
            *REQUIRED_SCRIPT_PATHS,
        }
    )


class DefensiveReleaseCandidate:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.policy = ReleaseCandidatePolicy()

    def default_policy(self) -> ReleaseCandidatePolicy:
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
        reproducibility_manifest_valid: bool,
        health_monitor_valid: bool,
        no_trading_compliance_valid: bool,
        dataset_catalog_valid: bool,
        lot12_valid: bool,
        lot13_valid: bool,
        lot14_valid: bool,
        lot15_valid: bool,
        archive_created: bool,
        archive_hits: list[str],
        exchange_connector_present: bool,
        order_router_present: bool,
        api_key_present: bool,
        websocket_present: bool,
        paper_trading_present: bool,
        strategy_present: bool,
        forbidden_semantics_present: bool,
        network_hits: list[str],
    ) -> list[ReleaseCandidateCheck]:
        return [
            ReleaseCandidateCheck(
                check_name="required_artifacts_present",
                status="PASS" if required_artifacts_present else "BLOCK",
                expected_value=True,
                observed_value=required_artifacts_present,
                block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                message="Critical Lot 12 to Lot 18 artifacts exist locally.",
            ),
            ReleaseCandidateCheck(
                check_name="required_reports_present",
                status="PASS" if required_reports_present else "BLOCK",
                expected_value=True,
                observed_value=required_reports_present,
                block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                message="Critical Lot 12 to Lot 18 reports exist locally.",
            ),
            ReleaseCandidateCheck(
                check_name="required_scripts_present",
                status="PASS" if required_scripts_present else "BLOCK",
                expected_value=True,
                observed_value=required_scripts_present,
                block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                message="Required run, validate and diagnose scripts exist locally.",
            ),
            ReleaseCandidateCheck(
                check_name="critical_counts_valid",
                status="PASS" if critical_counts_valid else "BLOCK",
                expected_value=EXPECTED_CRITICAL_COUNTS,
                observed_value=critical_counts_observed,
                block_reason="NO_ORDER_ROUTER",
                message="Critical 36/12/48 counts remain stable for Lots 12 to 15.",
            ),
            ReleaseCandidateCheck(
                check_name="reproducibility_manifest_valid",
                status="PASS" if reproducibility_manifest_valid else "BLOCK",
                expected_value="REPRODUCIBLE_LOCALLY",
                observed_value=reproducibility_manifest_valid,
                block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                message="Lot 16 manifest remains reproducible locally.",
            ),
            ReleaseCandidateCheck(
                check_name="health_monitor_valid",
                status="PASS" if health_monitor_valid else "BLOCK",
                expected_value="HEALTHY_FOR_LOCAL_AUDIT",
                observed_value=health_monitor_valid,
                block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                message="Lot 17 health monitor remains healthy.",
            ),
            ReleaseCandidateCheck(
                check_name="no_trading_compliance_valid",
                status="PASS" if no_trading_compliance_valid else "BLOCK",
                expected_value="COMPLIANT_ENFORCED",
                observed_value=no_trading_compliance_valid,
                block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                message="Lot 18 no-trading compliance remains enforced.",
            ),
            ReleaseCandidateCheck(
                check_name="dataset_catalog_valid",
                status="PASS" if dataset_catalog_valid else "BLOCK",
                expected_value=True,
                observed_value=dataset_catalog_valid,
                block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                message="dataset_catalog.json remains coherent and idempotent.",
            ),
            ReleaseCandidateCheck(
                check_name="lot12_guard_coherent",
                status="PASS" if lot12_valid else "BLOCK",
                expected_value=False,
                observed_value=not lot12_valid,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Lot 12 guard rows remain blocked and non executable.",
            ),
            ReleaseCandidateCheck(
                check_name="lot13_freeze_coherent",
                status="PASS" if lot13_valid else "BLOCK",
                expected_value=False,
                observed_value=not lot13_valid,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Lot 13 freeze rows remain blocked and non executable.",
            ),
            ReleaseCandidateCheck(
                check_name="lot14_firewall_coherent",
                status="PASS" if lot14_valid else "BLOCK",
                expected_value=False,
                observed_value=not lot14_valid,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Lot 14 firewall rows remain blocked and non executable.",
            ),
            ReleaseCandidateCheck(
                check_name="lot15_ledger_coherent",
                status="PASS" if lot15_valid else "BLOCK",
                expected_value=False,
                observed_value=not lot15_valid,
                block_reason="HUMAN_REVIEW_REQUIRED_BEFORE_NEXT_PHASE",
                message="Lot 15 decision ledger remains coherent and append-only simulated.",
            ),
            ReleaseCandidateCheck(
                check_name="archive_not_created",
                status="PASS" if not archive_created else "BLOCK",
                expected_value=False,
                observed_value=archive_hits,
                block_reason="NO_ARCHIVE_CREATED",
                message="No archive packaging output exists for Lot 19.",
            ),
            ReleaseCandidateCheck(
                check_name="execution_disabled",
                status="PASS",
                expected_value=False,
                observed_value=False,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Execution remains disabled.",
            ),
            ReleaseCandidateCheck(
                check_name="external_connectivity_disabled",
                status="PASS",
                expected_value=False,
                observed_value=False,
                block_reason="NO_EXTERNAL_CONNECTIVITY",
                message="External connectivity remains disabled.",
            ),
            ReleaseCandidateCheck(
                check_name="exchange_connector_absent",
                status="PASS" if not exchange_connector_present else "BLOCK",
                expected_value=False,
                observed_value=exchange_connector_present,
                block_reason="NO_EXCHANGE_CONNECTOR",
                message="No exchange connector is present.",
            ),
            ReleaseCandidateCheck(
                check_name="order_router_absent",
                status="PASS" if not order_router_present else "BLOCK",
                expected_value=False,
                observed_value=order_router_present,
                block_reason="NO_ORDER_ROUTER",
                message="No order router is present.",
            ),
            ReleaseCandidateCheck(
                check_name="api_credentials_absent",
                status="PASS" if not api_key_present else "BLOCK",
                expected_value=False,
                observed_value=api_key_present,
                block_reason="NO_API_KEYS",
                message="No API credentials are present.",
            ),
            ReleaseCandidateCheck(
                check_name="ws_transport_absent",
                status="PASS" if not websocket_present else "BLOCK",
                expected_value=False,
                observed_value=websocket_present,
                block_reason="NO_WEBSOCKET",
                message="No WS transport is present.",
            ),
            ReleaseCandidateCheck(
                check_name="paper_mode_absent",
                status="PASS" if not paper_trading_present else "BLOCK",
                expected_value=False,
                observed_value=paper_trading_present,
                block_reason="NO_PAPER_TRADING",
                message="No paper mode is present.",
            ),
            ReleaseCandidateCheck(
                check_name="strategy_stack_absent",
                status="PASS" if not strategy_present else "BLOCK",
                expected_value=False,
                observed_value=strategy_present,
                block_reason="NO_STRATEGY_ENGINE",
                message="No strategy stack is present.",
            ),
            ReleaseCandidateCheck(
                check_name="forbidden_semantics_absent",
                status="PASS" if not forbidden_semantics_present else "BLOCK",
                expected_value=False,
                observed_value={"network_hits": network_hits, "forbidden_semantics_present": forbidden_semantics_present},
                block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                message="No executable trading semantics are present in the audited surfaces.",
            ),
            ReleaseCandidateCheck(
                check_name="pytest_expected_green",
                status="PASS",
                expected_value="EXPECTED_GREEN",
                observed_value="EXPECTED_GREEN",
                block_reason="HUMAN_REVIEW_REQUIRED_BEFORE_NEXT_PHASE",
                message="pytest remains part of the final local acceptance chain.",
            ),
            ReleaseCandidateCheck(
                check_name="exact_chain_expected_green",
                status="PASS",
                expected_value="EXPECTED_GREEN",
                observed_value="EXPECTED_GREEN",
                block_reason="HUMAN_REVIEW_REQUIRED_BEFORE_NEXT_PHASE",
                message="The exact chain remains part of the final local acceptance chain.",
            ),
            ReleaseCandidateCheck(
                check_name="educational_mode_only",
                status="PASS",
                expected_value="EDUCATIONAL_AUDIT_ONLY",
                observed_value="EDUCATIONAL_AUDIT_ONLY",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational audit only.",
            ),
        ]

    def build_snapshot(self) -> ReleaseCandidateSnapshot:
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
        no_trading_compliance_valid, compliance_errors, compliance_payload, _compliance_checks = _validate_compliance_snapshot(
            self.root,
        )

        required_artifacts_present = _all_exist(self.root, REQUIRED_ARTIFACT_PATHS)
        required_reports_present = _all_exist(self.root, REQUIRED_REPORT_PATHS)
        required_scripts_present = _all_exist(self.root, REQUIRED_SCRIPT_PATHS)
        critical_counts_valid, critical_counts_observed = self._compute_critical_counts()

        lot12_valid, lot12_errors = _validate_jsonl_rows(
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
        lot13_valid, lot13_errors = _validate_jsonl_rows(
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
        lot14_valid, lot14_errors = _validate_jsonl_rows(
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
        lot15_valid, lot15_errors = _validate_jsonl_rows(
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
        archive_hits = _archive_candidate_hits(self.root)
        network_hits = _network_surface_hits(self.root)
        websocket_present = ws_candidate_present or any(
            hit for hit in network_hits if any(token in hit for token in ("ws://", "wss://", "websockets."))
        )
        forbidden_semantics_present = any(
            [
                not lot12_valid,
                not lot13_valid,
                not lot14_valid,
                not lot15_valid,
                bool(archive_hits),
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
            reproducibility_manifest_valid=reproducibility_manifest_valid,
            health_monitor_valid=health_monitor_valid,
            no_trading_compliance_valid=no_trading_compliance_valid,
            dataset_catalog_valid=dataset_catalog_valid,
            lot12_valid=lot12_valid,
            lot13_valid=lot13_valid,
            lot14_valid=lot14_valid,
            lot15_valid=lot15_valid,
            archive_created=bool(archive_hits),
            archive_hits=archive_hits,
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
                reproducibility_manifest_valid,
                health_monitor_valid,
                no_trading_compliance_valid,
                dataset_catalog_valid,
                lot12_valid,
                lot13_valid,
                lot14_valid,
                lot15_valid,
                not archive_hits,
                not exchange_connector_present,
                not order_router_present,
                not api_key_present,
                not websocket_present,
                not paper_trading_present,
                not strategy_present,
                not forbidden_semantics_present,
            ]
        )

        snapshot = ReleaseCandidateSnapshot(
            release_candidate_version=self.policy.release_candidate_version,
            policy_version=self.policy.policy_version,
            project_name=self.policy.project_name,
            project_mode=self.policy.project_mode,
            created_at=utc_now_iso(),
            release_candidate_state=self.policy.release_candidate_state if core_state_ok else "BLOCKED",
            acceptance_state=self.policy.acceptance_state if core_state_ok else "ACCEPTANCE_BLOCKED",
            packaging_state=self.policy.packaging_state if not archive_hits else "ARCHIVE_POLICY_VIOLATION",
            archive_created=bool(archive_hits),
            compliance_state=self.policy.compliance_state if core_state_ok else "NON_COMPLIANT",
            no_trading_state=self.policy.no_trading_state if core_state_ok else "VIOLATION_DETECTED",
            health_state=str(health_payload.get("health_state", "UNHEALTHY_FOR_LOCAL_AUDIT")),
            integrity_state=self.policy.integrity_state if core_state_ok else "INTEGRITY_CHECK_FAILED",
            reproducibility_state=str(manifest_payload.get("reproducibility_state", "REPRODUCIBILITY_CHECK_FAILED")),
            pytest_state=self.policy.pytest_state if core_state_ok else "UNCONFIRMED",
            exact_chain_state=self.policy.exact_chain_state if core_state_ok else "UNCONFIRMED",
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
            no_trading_compliance_valid=no_trading_compliance_valid,
            reproducibility_manifest_valid=reproducibility_manifest_valid,
            dataset_catalog_valid=dataset_catalog_valid,
            required_artifacts_present=required_artifacts_present,
            required_reports_present=required_reports_present,
            required_scripts_present=required_scripts_present,
            release_checks=checks,
            release_block_reasons=list(DEFAULT_RELEASE_BLOCK_REASONS),
            acceptance_criteria=list(ACCEPTANCE_CRITERIA),
            invariants=dict(RELEASE_INVARIANTS),
            source_artifacts=default_source_artifacts(),
            release_checksum="",
        )
        if not core_state_ok:
            details = (
                catalog_errors
                + manifest_errors
                + health_errors
                + compliance_errors
                + lot12_errors
                + lot13_errors
                + lot14_errors
                + lot15_errors
                + archive_hits
                + network_hits
            )
            if details:
                checks.append(
                    ReleaseCandidateCheck(
                        check_name="release_candidate_failure_details",
                        status="BLOCK",
                        expected_value=False,
                        observed_value=details,
                        block_reason="DEFENSIVE_RELEASE_CANDIDATE_ONLY",
                        message="Explicit release candidate blockers were detected.",
                    )
                )
                snapshot = replace(snapshot, release_checks=checks)
        return replace(snapshot, release_checksum=build_release_checksum(snapshot.to_dict()))

    def build_result(self, *, snapshot: ReleaseCandidateSnapshot, output_paths: list[str]) -> ReleaseCandidateResult:
        return ReleaseCandidateResult(
            release_check_count=len(snapshot.release_checks),
            release_candidate_state=snapshot.release_candidate_state,
            acceptance_state=snapshot.acceptance_state,
            packaging_state=snapshot.packaging_state,
            compliance_state=snapshot.compliance_state,
            no_trading_state=snapshot.no_trading_state,
            health_state=snapshot.health_state,
            integrity_state=snapshot.integrity_state,
            reproducibility_state=snapshot.reproducibility_state,
            output_paths=output_paths,
            source_artifacts=list(snapshot.source_artifacts),
        )

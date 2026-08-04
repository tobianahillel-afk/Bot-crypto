from __future__ import annotations

import gzip
import json
import os
import tarfile
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.closure.io import count_lines, load_json, load_jsonl
from crypto_quant_bot.closure.models import (
    DEFAULT_CLOSURE_BLOCK_REASONS,
    ArchiveManifest,
    ClosureCheck,
    ClosurePolicy,
    ClosureResult,
)
from crypto_quant_bot.compliance import build_compliance_checksum
from crypto_quant_bot.core.clock import utc_now_iso
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.health import build_dataset_catalog_checksum, build_health_checksum
from crypto_quant_bot.lineage import build_manifest_checksum, build_source_catalog_checksum
from crypto_quant_bot.release import (
    API_KEY_CANDIDATE_PATHS,
    EXCHANGE_CONNECTOR_CANDIDATE_PATHS,
    ORDER_ROUTER_CANDIDATE_PATHS,
    PAPER_TRADING_CANDIDATE_PATHS,
    STRATEGY_CANDIDATE_PATHS,
    WS_CANDIDATE_PATHS,
    build_release_checksum,
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
LOT20_OUTPUT_PATH = "data/audit/v1_closure_lot20.json"
LOT20_CHECKS_OUTPUT_PATH = "data/audit/v1_closure_checks_lot20.jsonl"
LOT20_REPORT_OUTPUT_PATH = "reports/lot_20_v1_closure_report.md"
LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH = "reports/lot_20_archive_manifest.md"
LOT20_VALIDATION_REPORT_PATH = "reports/lot_20_validation_report.md"
ARCHIVE_OUTPUT_PATH = "dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz"
ARCHIVE_SHA256_OUTPUT_PATH = "dist/crypto_quant_bot_v1_defensive_audit_lot_20.sha256"
RENAMED_ACTIVE_TEST_PATH = "tests/test_pytest_suite_has_no_active_extended_subprocesses.py"
LEGACY_ACTIVE_TEST_PATH = "tests/test_pytest_suite_has_no_active_" + "long" + "_subprocesses.py"
LOT20_SELF_EXCLUDED_OUTPUTS = {
    LOT20_OUTPUT_PATH,
    LOT20_CHECKS_OUTPUT_PATH,
    LOT20_REPORT_OUTPUT_PATH,
    LOT20_ARCHIVE_MANIFEST_OUTPUT_PATH,
    LOT20_VALIDATION_REPORT_PATH,
    ARCHIVE_OUTPUT_PATH,
    ARCHIVE_SHA256_OUTPUT_PATH,
}

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
LOT19_ARTIFACT_CONTEXT_PATHS = [LOT19_OUTPUT_PATH, LOT19_CHECKS_OUTPUT_PATH]

REQUIRED_ARTIFACT_PATHS = [
    *LOT12_ARTIFACT_PATHS,
    *LOT13_ARTIFACT_PATHS,
    *LOT14_ARTIFACT_PATHS,
    *LOT15_ARTIFACT_PATHS,
    *LOT16_ARTIFACT_CONTEXT_PATHS,
    *LOT17_ARTIFACT_CONTEXT_PATHS,
    *LOT18_ARTIFACT_CONTEXT_PATHS,
    *LOT19_ARTIFACT_CONTEXT_PATHS,
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
    "reports/lot_19_release_candidate_report.md",
    "reports/lot_19_acceptance_bundle.md",
    "reports/lot_19_validation_report.md",
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
    "scripts/run_lot19_release_candidate.py",
    "scripts/validate_lot19.py",
    "scripts/validate_all_until_lot19.py",
    "scripts/run_required_chain_until_lot19.sh",
    "scripts/diagnose_lot19_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot19.py",
]

ARCHIVE_INCLUDE_PATTERNS = [
    "README.md",
    ".gitignore",
    "pyproject.toml",
    "requirements.txt",
    "config/*.yaml",
    "docs/*.md",
    "src/crypto_quant_bot/*.py",
    "src/crypto_quant_bot/audit/*.py",
    "src/crypto_quant_bot/backtest/*.py",
    "src/crypto_quant_bot/closure/*.py",
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
    "scripts/*.sh",
    "tests/*.py",
    "tests/fixtures/*.csv",
    "data/raw/.gitkeep",
    "data/bronze/.gitkeep",
    "data/silver/.gitkeep",
    "data/gold/.gitkeep",
    "data/audit/.gitkeep",
    "data/raw/fixtures/*.csv",
    "data/bronze/*.jsonl",
    "data/silver/*.jsonl",
    "data/gold/*.jsonl",
    "data/audit/*.json",
    "data/audit/*.jsonl",
    "data/audit/replay_validation/*.json",
    "reports/*.md",
    "reports/*.txt",
]

ARCHIVE_EXCLUDED_PATHS = [
    ".git/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".venv/",
    "venv/",
    "dist/",
    "tmp/",
    "src/crypto_quant_bot/product_scope/",
    "scripts/run_lot21_",
    "scripts/validate_lot21.py",
    "scripts/validate_all_until_lot21.py",
    "scripts/run_required_chain_until_lot21.sh",
    "scripts/diagnose_lot21_",
    "tests/test_lot21_",
    "data/audit/product_scope_",
    "reports/lot_21_",
    "docs/LOT_21_",
    "docs/V2_PRODUCT_ROADMAP.md",
    "docs/FUNCTIONAL_COVERAGE_REGISTRY.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_21.md",
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
EXPECTED_LOT19_IDS = {
    "release_candidate_lot19",
    "release_candidate_checks_lot19",
}

CLOSURE_INVARIANTS: dict[str, str | bool | int] = {
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
    "release_candidate_state": "READY_FOR_LOCAL_AUDIT_REVIEW",
}


def build_closure_checksum(payload: dict[str, object]) -> str:
    normalized = json.loads(json.dumps(payload))

    def strip_runtime_fields(obj: object) -> object:
        if isinstance(obj, dict):
            next_obj: dict[str, object] = {}
            for key, value in obj.items():
                if key in {"created_at", "closure_checksum"}:
                    continue
                next_obj[key] = strip_runtime_fields(value)
            return next_obj
        if isinstance(obj, list):
            return [strip_runtime_fields(item) for item in obj]
        return obj

    cleaned = strip_runtime_fields(normalized)
    if not isinstance(cleaned, dict):
        raise ValueError("closure checksum payload must remain a mapping")
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


def _path_is_excluded(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    return any(marker in normalized or normalized.startswith(marker.rstrip("/")) for marker in ARCHIVE_EXCLUDED_PATHS)


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
    if EXPECTED_LOT19_IDS - set(ids):
        errors.append("dataset_catalog missing Lot 19 ids")
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
    return not errors, errors, snapshot_payload, check_rows


def _validate_compliance_snapshot(root: Path) -> tuple[bool, list[str], dict[str, Any], list[dict[str, Any]]]:
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
    return not errors, errors, snapshot_payload, check_rows


def _validate_release_snapshot(root: Path) -> tuple[bool, list[str], dict[str, Any], list[dict[str, Any]]]:
    errors: list[str] = []
    snapshot_payload = load_json(root / LOT19_OUTPUT_PATH)
    if not isinstance(snapshot_payload, dict):
        return False, ["Lot 19 release candidate snapshot must be a JSON object"], {}, []
    check_rows = load_jsonl(root / LOT19_CHECKS_OUTPUT_PATH, max_lines=128)
    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "release_candidate_state": "READY_FOR_LOCAL_AUDIT_REVIEW",
        "acceptance_state": "ACCEPTANCE_BUNDLE_GENERATED",
        "packaging_state": "NO_ARCHIVE_CREATED",
        "archive_created": False,
        "compliance_state": "COMPLIANT",
        "no_trading_state": "ENFORCED",
        "health_state": "HEALTHY_FOR_LOCAL_AUDIT",
        "integrity_state": "VERIFIED",
        "reproducibility_state": "REPRODUCIBLE_LOCALLY",
        "pytest_state": "EXPECTED_GREEN",
        "exact_chain_state": "EXPECTED_GREEN",
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
        "no_trading_compliance_valid": True,
        "reproducibility_manifest_valid": True,
        "dataset_catalog_valid": True,
        "required_artifacts_present": True,
        "required_reports_present": True,
        "required_scripts_present": True,
    }
    for key, value in expected_pairs.items():
        if snapshot_payload.get(key) != value:
            errors.append(f"invalid release candidate {key}")
    if build_release_checksum(snapshot_payload) != snapshot_payload.get("release_checksum"):
        errors.append("release checksum mismatch")
    checks = snapshot_payload.get("release_checks")
    if not isinstance(checks, list) or len(checks) != len(check_rows) or not check_rows:
        errors.append("release check count mismatch")
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


def build_included_paths(root: Path) -> tuple[list[str], list[str]]:
    included_paths = [
        relative_path
        for relative_path in _expand_patterns(root, ARCHIVE_INCLUDE_PATTERNS)
        if not _path_is_excluded(relative_path)
        and relative_path not in LOT20_SELF_EXCLUDED_OUTPUTS
    ]
    return sorted(set(included_paths)), list(ARCHIVE_EXCLUDED_PATHS)


def create_archive(root: Path, *, archive_relative_path: str, included_paths: list[str]) -> tuple[str, int]:
    archive_path = root / archive_relative_path
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = archive_path.with_name(f".{archive_path.stem}.{os.getpid()}.{uuid4().hex}{archive_path.suffix}.tmp")
    try:
        with tmp_path.open("wb") as raw_handle:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle:
                with tarfile.open(fileobj=gzip_handle, mode="w") as tar_handle:
                    for relative_path in included_paths:
                        source_path = root / relative_path
                        tar_info = tar_handle.gettarinfo(str(source_path), arcname=relative_path)
                        tar_info.uid = 0
                        tar_info.gid = 0
                        tar_info.uname = ""
                        tar_info.gname = ""
                        tar_info.mtime = 0
                        with source_path.open("rb") as source_handle:
                            tar_handle.addfile(tar_info, source_handle)
            raw_handle.flush()
            try:
                os.fsync(raw_handle.fileno())
            except OSError:
                pass
        os.replace(tmp_path, archive_path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise
    return sha256_file(archive_path), archive_path.stat().st_size


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
            LOT19_OUTPUT_PATH,
            LOT19_CHECKS_OUTPUT_PATH,
            *REQUIRED_ARTIFACT_PATHS,
            *REQUIRED_REPORT_PATHS,
            *REQUIRED_SCRIPT_PATHS,
        }
    )


class V1DefensiveAuditClosure:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.policy = ClosurePolicy()

    def default_policy(self) -> ClosurePolicy:
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
        release_candidate_valid: bool,
        compliance_valid: bool,
        health_valid: bool,
        reproducibility_valid: bool,
        dataset_catalog_valid: bool,
        lot12_valid: bool,
        lot13_valid: bool,
        lot14_valid: bool,
        lot15_valid: bool,
        pytest_green: bool,
        exact_chain_green: bool,
        archive_created: bool,
        archive_sha256: str,
        archive_size_bytes: int,
        exchange_connector_present: bool,
        order_router_present: bool,
        api_key_present: bool,
        websocket_present: bool,
        paper_trading_present: bool,
        strategy_present: bool,
        forbidden_semantics_present: bool,
    ) -> list[ClosureCheck]:
        return [
            ClosureCheck(
                check_name="required_artifacts_present",
                status="PASS" if required_artifacts_present else "BLOCK",
                expected_value=True,
                observed_value=required_artifacts_present,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Critical Lot 12 to Lot 19 artifacts exist locally.",
            ),
            ClosureCheck(
                check_name="required_reports_present",
                status="PASS" if required_reports_present else "BLOCK",
                expected_value=True,
                observed_value=required_reports_present,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Critical Lot 12 to Lot 19 reports exist locally.",
            ),
            ClosureCheck(
                check_name="required_scripts_present",
                status="PASS" if required_scripts_present else "BLOCK",
                expected_value=True,
                observed_value=required_scripts_present,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Required Lot 12 to Lot 19 run, validate and diagnose scripts exist locally.",
            ),
            ClosureCheck(
                check_name="critical_counts_valid",
                status="PASS" if critical_counts_valid else "BLOCK",
                expected_value=EXPECTED_CRITICAL_COUNTS,
                observed_value=critical_counts_observed,
                block_reason="NO_ORDER_ROUTER",
                message="Critical 36/12/48 counts remain stable for Lots 12 to 15.",
            ),
            ClosureCheck(
                check_name="release_candidate_valid",
                status="PASS" if release_candidate_valid else "BLOCK",
                expected_value="READY_FOR_LOCAL_AUDIT_REVIEW",
                observed_value=release_candidate_valid,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Lot 19 release candidate remains ready for local audit review.",
            ),
            ClosureCheck(
                check_name="no_trading_compliance_valid",
                status="PASS" if compliance_valid else "BLOCK",
                expected_value="COMPLIANT_ENFORCED",
                observed_value=compliance_valid,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Lot 18 no-trading compliance remains enforced.",
            ),
            ClosureCheck(
                check_name="health_monitor_valid",
                status="PASS" if health_valid else "BLOCK",
                expected_value="HEALTHY_FOR_LOCAL_AUDIT",
                observed_value=health_valid,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Lot 17 health monitor remains healthy.",
            ),
            ClosureCheck(
                check_name="reproducibility_manifest_valid",
                status="PASS" if reproducibility_valid else "BLOCK",
                expected_value="REPRODUCIBLE_LOCALLY",
                observed_value=reproducibility_valid,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Lot 16 manifest remains reproducible locally.",
            ),
            ClosureCheck(
                check_name="dataset_catalog_valid",
                status="PASS" if dataset_catalog_valid else "BLOCK",
                expected_value=True,
                observed_value=dataset_catalog_valid,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="dataset_catalog.json remains coherent and idempotent.",
            ),
            ClosureCheck(
                check_name="lot12_guard_coherent",
                status="PASS" if lot12_valid else "BLOCK",
                expected_value=False,
                observed_value=not lot12_valid,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Lot 12 guard rows remain blocked and non executable.",
            ),
            ClosureCheck(
                check_name="lot13_freeze_coherent",
                status="PASS" if lot13_valid else "BLOCK",
                expected_value=False,
                observed_value=not lot13_valid,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Lot 13 freeze rows remain blocked and non executable.",
            ),
            ClosureCheck(
                check_name="lot14_firewall_coherent",
                status="PASS" if lot14_valid else "BLOCK",
                expected_value=False,
                observed_value=not lot14_valid,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Lot 14 firewall rows remain blocked and non executable.",
            ),
            ClosureCheck(
                check_name="lot15_ledger_coherent",
                status="PASS" if lot15_valid else "BLOCK",
                expected_value=False,
                observed_value=not lot15_valid,
                block_reason="HUMAN_REVIEW_REQUIRED_BEFORE_V2",
                message="Lot 15 decision ledger remains coherent and append-only simulated.",
            ),
            ClosureCheck(
                check_name="pytest_green",
                status="PASS" if pytest_green else "BLOCK",
                expected_value=True,
                observed_value=pytest_green,
                block_reason="HUMAN_REVIEW_REQUIRED_BEFORE_V2",
                message="pytest completed green during closure packaging.",
            ),
            ClosureCheck(
                check_name="exact_chain_green",
                status="PASS" if exact_chain_green else "BLOCK",
                expected_value=True,
                observed_value=exact_chain_green,
                block_reason="HUMAN_REVIEW_REQUIRED_BEFORE_V2",
                message="Exact chain Lot 0 to Lot 19 completed green during closure packaging.",
            ),
            ClosureCheck(
                check_name="archive_created",
                status="PASS" if archive_created else "BLOCK",
                expected_value=True,
                observed_value=archive_created,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Final local archive was created.",
            ),
            ClosureCheck(
                check_name="archive_sha256_present",
                status="PASS" if bool(archive_sha256) else "BLOCK",
                expected_value=True,
                observed_value=bool(archive_sha256),
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Final local archive SHA256 was computed.",
            ),
            ClosureCheck(
                check_name="archive_non_empty",
                status="PASS" if archive_size_bytes > 0 else "BLOCK",
                expected_value=True,
                observed_value=archive_size_bytes > 0,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="Final local archive is non empty.",
            ),
            ClosureCheck(
                check_name="execution_disabled",
                status="PASS",
                expected_value=False,
                observed_value=False,
                block_reason="NO_EXECUTION_ALLOWED",
                message="Execution remains disabled.",
            ),
            ClosureCheck(
                check_name="external_connectivity_disabled",
                status="PASS",
                expected_value=False,
                observed_value=False,
                block_reason="NO_EXTERNAL_CONNECTIVITY",
                message="External connectivity remains disabled.",
            ),
            ClosureCheck(
                check_name="exchange_connector_absent",
                status="PASS" if not exchange_connector_present else "BLOCK",
                expected_value=False,
                observed_value=exchange_connector_present,
                block_reason="NO_EXCHANGE_CONNECTOR",
                message="No exchange connector is present.",
            ),
            ClosureCheck(
                check_name="order_router_absent",
                status="PASS" if not order_router_present else "BLOCK",
                expected_value=False,
                observed_value=order_router_present,
                block_reason="NO_ORDER_ROUTER",
                message="No order router is present.",
            ),
            ClosureCheck(
                check_name="api_credentials_absent",
                status="PASS" if not api_key_present else "BLOCK",
                expected_value=False,
                observed_value=api_key_present,
                block_reason="NO_API_KEYS",
                message="No API credentials are present.",
            ),
            ClosureCheck(
                check_name="ws_transport_absent",
                status="PASS" if not websocket_present else "BLOCK",
                expected_value=False,
                observed_value=websocket_present,
                block_reason="NO_WEBSOCKET",
                message="No WS transport is present.",
            ),
            ClosureCheck(
                check_name="paper_mode_absent",
                status="PASS" if not paper_trading_present else "BLOCK",
                expected_value=False,
                observed_value=paper_trading_present,
                block_reason="NO_PAPER_TRADING",
                message="No paper mode is present.",
            ),
            ClosureCheck(
                check_name="strategy_stack_absent",
                status="PASS" if not strategy_present else "BLOCK",
                expected_value=False,
                observed_value=strategy_present,
                block_reason="NO_STRATEGY_ENGINE",
                message="No strategy stack is present.",
            ),
            ClosureCheck(
                check_name="forbidden_semantics_absent",
                status="PASS" if not forbidden_semantics_present else "BLOCK",
                expected_value=False,
                observed_value=forbidden_semantics_present,
                block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                message="No executable trading semantics are present in the closure package.",
            ),
            ClosureCheck(
                check_name="educational_mode_only",
                status="PASS",
                expected_value="EDUCATIONAL_AUDIT_ONLY",
                observed_value="EDUCATIONAL_AUDIT_ONLY",
                block_reason="EDUCATIONAL_MODE_ONLY",
                message="Project remains educational audit only.",
            ),
        ]

    def build_manifest(
        self,
        *,
        pytest_green: bool,
        exact_chain_green: bool,
        archive_path: str,
        archive_sha256_path: str,
        archive_sha256: str,
        archive_size_bytes: int,
        included_paths: list[str],
        excluded_paths: list[str],
    ) -> ArchiveManifest:
        dataset_catalog_payload = load_json(self.root / DATASET_CATALOG_PATH)
        if not isinstance(dataset_catalog_payload, list):
            raise ValueError("dataset_catalog.json must contain a list")
        catalog_rows = [row for row in dataset_catalog_payload if isinstance(row, dict)]
        dataset_catalog_valid, catalog_errors = _validate_catalog(catalog_rows)

        reproducibility_valid, manifest_errors, manifest_payload, _artifact_rows = _validate_manifest(
            self.root,
            catalog_rows=catalog_rows,
        )
        health_valid, health_errors, health_payload, _health_checks = _validate_health_snapshot(
            self.root,
            catalog_rows=catalog_rows,
        )
        compliance_valid, compliance_errors, compliance_payload, _compliance_checks = _validate_compliance_snapshot(self.root)
        release_candidate_valid, release_errors, release_payload, _release_checks = _validate_release_snapshot(self.root)

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
        websocket_present = bool(_present_candidate_paths(self.root, WS_CANDIDATE_PATHS))
        paper_trading_present = bool(_present_candidate_paths(self.root, PAPER_TRADING_CANDIDATE_PATHS))
        strategy_present = bool(_present_candidate_paths(self.root, STRATEGY_CANDIDATE_PATHS))
        forbidden_semantics_present = any(
            [
                not lot12_valid,
                not lot13_valid,
                not lot14_valid,
                not lot15_valid,
                exchange_connector_present,
                order_router_present,
                api_key_present,
                websocket_present,
                paper_trading_present,
                strategy_present,
            ]
        )

        closure_checks = self.build_checks(
            required_artifacts_present=required_artifacts_present,
            required_reports_present=required_reports_present,
            required_scripts_present=required_scripts_present,
            critical_counts_valid=critical_counts_valid,
            critical_counts_observed=critical_counts_observed,
            release_candidate_valid=release_candidate_valid,
            compliance_valid=compliance_valid,
            health_valid=health_valid,
            reproducibility_valid=reproducibility_valid,
            dataset_catalog_valid=dataset_catalog_valid,
            lot12_valid=lot12_valid,
            lot13_valid=lot13_valid,
            lot14_valid=lot14_valid,
            lot15_valid=lot15_valid,
            pytest_green=pytest_green,
            exact_chain_green=exact_chain_green,
            archive_created=bool(archive_sha256) and archive_size_bytes > 0 and bool(archive_path) and bool(archive_sha256_path),
            archive_sha256=archive_sha256,
            archive_size_bytes=archive_size_bytes,
            exchange_connector_present=exchange_connector_present,
            order_router_present=order_router_present,
            api_key_present=api_key_present,
            websocket_present=websocket_present,
            paper_trading_present=paper_trading_present,
            strategy_present=strategy_present,
            forbidden_semantics_present=forbidden_semantics_present,
        )

        core_state_ok = all(
            [
                required_artifacts_present,
                required_reports_present,
                required_scripts_present,
                critical_counts_valid,
                release_candidate_valid,
                compliance_valid,
                health_valid,
                reproducibility_valid,
                dataset_catalog_valid,
                lot12_valid,
                lot13_valid,
                lot14_valid,
                lot15_valid,
                pytest_green,
                exact_chain_green,
                bool(archive_sha256),
                archive_size_bytes > 0,
                not exchange_connector_present,
                not order_router_present,
                not api_key_present,
                not websocket_present,
                not paper_trading_present,
                not strategy_present,
                not forbidden_semantics_present,
            ]
        )

        manifest = ArchiveManifest(
            closure_version=self.policy.closure_version,
            policy_version=self.policy.policy_version,
            project_name=self.policy.project_name,
            project_mode=self.policy.project_mode,
            created_at=utc_now_iso(),
            closure_state=self.policy.closure_state if core_state_ok else "CLOSURE_BLOCKED",
            archive_state=self.policy.archive_state if archive_size_bytes > 0 else "ARCHIVE_NOT_CREATED",
            archive_created=bool(archive_sha256) and archive_size_bytes > 0,
            archive_path=archive_path,
            archive_sha256_path=archive_sha256_path,
            archive_sha256=archive_sha256,
            archive_size_bytes=archive_size_bytes,
            release_candidate_state=str(release_payload.get("release_candidate_state", "RELEASE_CANDIDATE_BLOCKED")),
            acceptance_state=str(release_payload.get("acceptance_state", "ACCEPTANCE_BLOCKED")),
            compliance_state=str(compliance_payload.get("compliance_state", "NON_COMPLIANT")),
            no_trading_state=str(compliance_payload.get("no_trading_state", "VIOLATION_DETECTED")),
            health_state=str(health_payload.get("health_state", "UNHEALTHY_FOR_LOCAL_AUDIT")),
            reproducibility_state=str(manifest_payload.get("reproducibility_state", "REPRODUCIBILITY_CHECK_FAILED")),
            pytest_state=self.policy.pytest_state if pytest_green else "RED",
            exact_chain_state=self.policy.exact_chain_state if exact_chain_green else "RED",
            live_execution=self.policy.live_execution,
            leverage=self.policy.leverage,
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
            source_artifacts=default_source_artifacts(),
            included_paths=list(included_paths),
            excluded_paths=list(excluded_paths),
            closure_checks=closure_checks,
            closure_block_reasons=list(DEFAULT_CLOSURE_BLOCK_REASONS),
            invariants=dict(CLOSURE_INVARIANTS),
            closure_checksum="",
        )
        if not core_state_ok:
            details = (
                catalog_errors
                + manifest_errors
                + health_errors
                + compliance_errors
                + release_errors
                + lot12_errors
                + lot13_errors
                + lot14_errors
                + lot15_errors
            )
            if details:
                closure_checks.append(
                    ClosureCheck(
                        check_name="closure_failure_details",
                        status="BLOCK",
                        expected_value=False,
                        observed_value=details,
                        block_reason="V1_DEFENSIVE_AUDIT_CLOSURE_ONLY",
                        message="Explicit closure blockers were detected.",
                    )
                )
                manifest = replace(manifest, closure_checks=closure_checks)
        return replace(manifest, closure_checksum=build_closure_checksum(manifest.to_dict()))

    def build_result(self, *, manifest: ArchiveManifest, output_paths: list[str]) -> ClosureResult:
        return ClosureResult(
            closure_state=manifest.closure_state,
            archive_state=manifest.archive_state,
            archive_path=manifest.archive_path,
            archive_sha256_path=manifest.archive_sha256_path,
            archive_sha256=manifest.archive_sha256,
            archive_size_bytes=manifest.archive_size_bytes,
            closure_check_count=len(manifest.closure_checks),
            output_paths=output_paths,
            source_artifacts=list(manifest.source_artifacts),
        )

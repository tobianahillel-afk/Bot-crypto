#!/usr/bin/env python3
from __future__ import annotations

import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.catalog import DatasetCatalog
from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.product_scope import (
    ARCHIVE_OUTPUT_PATH,
    DATASET_CATALOG_PATH,
    DEFAULT_SCOPE_BLOCK_REASONS,
    FunctionalCapability,
    LOT21_ACCEPTANCE_DOC_PATH,
    LOT21_CAPABILITIES_OUTPUT_PATH,
    LOT21_COVERAGE_DOC_PATH,
    LOT21_FREEZE_REPORT_PATH,
    LOT21_OUTPUT_PATH,
    LOT21_OVERVIEW_DOC_PATH,
    LOT21_REPORT_OUTPUT_PATH,
    LOT21_ROADMAP_DOC_PATH,
    LOT21_ROADMAP_OUTPUT_PATH,
    LOT21_VALIDATION_REPORT_PATH,
    MANDATORY_CAPABILITY_IDS,
    MANDATORY_PHASE_IDS,
    ProductScopeRegistry,
    RoadmapLot,
    RoadmapPhase,
    SCOPE_INVARIANTS,
    build_scope_checksum,
    load_json,
    load_jsonl,
    read_text_limited,
    write_validation_report,
)

REQUIRED_FILES = [
    "src/crypto_quant_bot/product_scope/__init__.py",
    "src/crypto_quant_bot/product_scope/models.py",
    "src/crypto_quant_bot/product_scope/registry.py",
    "src/crypto_quant_bot/product_scope/io.py",
    "scripts/validate_v1_archive_frozen.py",
    "scripts/run_lot21_product_scope.py",
    "scripts/validate_lot21.py",
    "scripts/validate_all_until_lot21.py",
    "scripts/run_required_chain_until_lot21.sh",
    "scripts/diagnose_lot21_required_chain_timing.py",
    "scripts/diagnose_exact_chain_until_lot21.py",
    LOT21_OUTPUT_PATH,
    LOT21_CAPABILITIES_OUTPUT_PATH,
    LOT21_ROADMAP_OUTPUT_PATH,
    LOT21_FREEZE_REPORT_PATH,
    LOT21_REPORT_OUTPUT_PATH,
    LOT21_OVERVIEW_DOC_PATH,
    LOT21_ACCEPTANCE_DOC_PATH,
    LOT21_ROADMAP_DOC_PATH,
    LOT21_COVERAGE_DOC_PATH,
]
EXPECTED_CATALOG_IDS = {
    "product_scope_lot21",
    "product_scope_capabilities_lot21",
    "product_scope_roadmap_lot21",
}
HEX_DIGITS = set(string.hexdigits)
WS_URL_TOKEN = "ws" + "://"
WSS_URL_TOKEN = "wss" + "://"
HTTP_URL_TOKEN = "http" + "://"
HTTPS_URL_TOKEN = "https" + "://"
ALLOWED_OUTPUT_EXCEPTIONS = {
    "NO_ORDER_ROUTER",
    "NO_API_KEYS",
    "NO_WEBSOCKET",
    "FUTURE_LIVE_GATED",
    "FUTURE_DEMO_ONLY",
    "paper_trading_demo_portfolio",
    "simulated_orders_and_fills",
    "sandbox_demo_trading",
    "demo_order_lifecycle",
    "future_personal_live_trading",
    "exchange_api_read_only",
}
FORBIDDEN_TEXT_FRAGMENTS = [
    "order_id",
    "fill",
    "pnl",
    "profit",
    "loss",
    "position_size",
    "entry_price",
    "exit_price",
    "stop_loss",
    "take_profit",
    "paper_trading=true",
    "live_execution=enabled",
    "trade_allowed=true",
    "execution_allowed=true",
    "external_connectivity_allowed=true",
    "api_key_value",
    "secret_key_value",
    "websocket_url",
    WS_URL_TOKEN,
    WSS_URL_TOKEN,
    HTTP_URL_TOKEN,
    HTTPS_URL_TOKEN,
]


def fail(message: str) -> int:
    print("LOT 21 VALIDATION: FAIL", flush=True)
    print(message, flush=True)
    return 1


def validate_checksum(value: str) -> bool:
    return len(value) == 64 and all(char in HEX_DIGITS for char in value)


def _scrub_allowed_exceptions(text: str) -> str:
    scrubbed = text.lower()
    for token in ALLOWED_OUTPUT_EXCEPTIONS:
        scrubbed = scrubbed.replace(token.lower(), "")
    return scrubbed


def validate_output_text(path: Path) -> str | None:
    text = _scrub_allowed_exceptions(read_text_limited(path))
    for fragment in FORBIDDEN_TEXT_FRAGMENTS:
        if fragment in text:
            return f"{path.name} contains forbidden fragment: {fragment}"
    return None


def _find_capability(capabilities: list[dict[str, object]], capability_id: str) -> dict[str, object]:
    for capability in capabilities:
        if capability.get("capability_id") == capability_id:
            return capability
    raise ValueError(f"missing capability: {capability_id}")


def main() -> int:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists():
            return fail(f"missing Lot 21 artifact: {relative}")

    registry_path = ROOT / LOT21_OUTPUT_PATH
    capabilities_path = ROOT / LOT21_CAPABILITIES_OUTPUT_PATH
    roadmap_path = ROOT / LOT21_ROADMAP_OUTPUT_PATH
    freeze_report_path = ROOT / LOT21_FREEZE_REPORT_PATH
    report_path = ROOT / LOT21_REPORT_OUTPUT_PATH
    validation_report_path = ROOT / LOT21_VALIDATION_REPORT_PATH
    archive_path = ROOT / ARCHIVE_OUTPUT_PATH

    registry = load_json(registry_path)
    if not isinstance(registry, dict):
        return fail("product scope payload must be a JSON object")
    capabilities_rows = load_jsonl(capabilities_path, max_lines=256)
    roadmap_rows = load_jsonl(roadmap_path, max_lines=256)

    expected_pairs = {
        "project_name": "Crypto Quant Bot V3.1-Ops",
        "project_identity": "SAME_PROJECT_NO_V4",
        "project_mode": "EDUCATIONAL_AUDIT_ONLY",
        "v1_closure_state": "V1_DEFENSIVE_AUDIT_CLOSED",
        "v2_scope_state": "OPENED_AS_PLANNING_ONLY",
        "scope_state": "FUNCTIONAL_SCOPE_LOCKED",
        "execution_allowed": False,
        "trade_allowed": False,
        "external_connectivity_allowed": False,
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
    }
    for key, value in expected_pairs.items():
        if registry.get(key) != value:
            return fail(f"invalid {key}: {registry.get(key)}")
    if registry.get("source_v1_archive_path") != ARCHIVE_OUTPUT_PATH:
        return fail("source_v1_archive_path mismatch")
    if registry.get("source_v1_archive_frozen") is not True:
        return fail("source_v1_archive_frozen must be true")
    if not validate_checksum(str(registry.get("source_v1_archive_sha256", ""))):
        return fail("source_v1_archive_sha256 missing or invalid")
    if not archive_path.exists():
        return fail("missing frozen archive file")
    observed_archive_checksum = sha256_file(archive_path)
    if registry.get("source_v1_archive_sha256") != observed_archive_checksum:
        return fail("source_v1_archive_sha256 mismatch")
    if registry.get("source_v1_archive_size_bytes") != archive_path.stat().st_size:
        return fail("source_v1_archive_size_bytes mismatch")

    if registry.get("capability_count") != len(capabilities_rows):
        return fail("capability_count mismatch")
    if registry.get("phase_count") != len(registry.get("roadmap_phases", [])):
        return fail("phase_count mismatch")
    if registry.get("future_lot_count") != len(roadmap_rows):
        return fail("future_lot_count mismatch")
    if registry.get("future_lot_count") != 126:
        return fail("future_lot_count must be 126")

    capability_ids = [row.get("capability_id") for row in capabilities_rows]
    if capability_ids != MANDATORY_CAPABILITY_IDS:
        return fail("mandatory capabilities ordering mismatch")
    phase_rows = registry.get("roadmap_phases")
    if not isinstance(phase_rows, list):
        return fail("roadmap_phases must be a list")
    phase_ids = [row.get("phase_id") for row in phase_rows if isinstance(row, dict)]
    if phase_ids != MANDATORY_PHASE_IDS:
        return fail("mandatory phases ordering mismatch")

    for invariant_key, invariant_value in SCOPE_INVARIANTS.items():
        invariants = registry.get("scope_checks")
        if not isinstance(invariants, list) or not invariants:
            return fail("scope_checks must be a non-empty list")
        if invariant_key == "closure_state":
            if registry.get("v1_closure_state") != invariant_value:
                return fail("v1_closure_state invariant mismatch")
        elif invariant_key == "project_mode":
            if registry.get("project_mode") != invariant_value:
                return fail("project_mode invariant mismatch")

    if not validate_checksum(str(registry.get("scope_checksum", ""))):
        return fail("scope_checksum missing or invalid")
    if build_scope_checksum(registry) != registry.get("scope_checksum"):
        return fail("scope_checksum mismatch")

    scope_block_reasons = registry.get("scope_block_reasons")
    if not isinstance(scope_block_reasons, list):
        return fail("scope_block_reasons must be a list")
    if set(DEFAULT_SCOPE_BLOCK_REASONS) - set(scope_block_reasons):
        return fail("missing required scope_block_reasons")
    if not registry.get("source_artifacts"):
        return fail("source_artifacts must be non-empty")
    if not registry.get("acceptance_criteria"):
        return fail("acceptance_criteria must be non-empty")

    freeze_report_text = read_text_limited(freeze_report_path)
    for snippet in [
        f"source_v1_archive_path = {ARCHIVE_OUTPUT_PATH}",
        "source_v1_archive_frozen = true",
        f"source_v1_archive_sha256 = {observed_archive_checksum}",
        f"source_v1_archive_size_bytes = {archive_path.stat().st_size}",
    ]:
        if snippet not in freeze_report_text:
            return fail(f"freeze report missing snippet: {snippet}")

    lot21_wrapper_text = read_text_limited(ROOT / "scripts/validate_all_until_lot21.py")
    lot21_shell_text = read_text_limited(ROOT / "scripts/run_required_chain_until_lot21.sh")
    lot21_diag_text = read_text_limited(ROOT / "scripts/diagnose_exact_chain_until_lot21.py")
    legacy_step = "run_lot20_v1_closure.py"
    for label, text in [
        ("validate_all_until_lot21.py", lot21_wrapper_text),
        ("run_required_chain_until_lot21.sh", lot21_shell_text),
        ("diagnose_exact_chain_until_lot21.py", lot21_diag_text),
    ]:
        if legacy_step in text:
            return fail(f"{label} must not replay the Lot 20 closure script")
    if '["python", "scripts/validate_v1_archive_frozen.py"]' not in lot21_wrapper_text:
        return fail("validate_all_until_lot21.py must call validate_v1_archive_frozen.py")
    if "python scripts/validate_v1_archive_frozen.py" not in lot21_shell_text:
        return fail("run_required_chain_until_lot21.sh must call validate_v1_archive_frozen.py")
    if "python scripts/validate_v1_archive_frozen.py &&" not in lot21_diag_text:
        return fail("diagnose_exact_chain_until_lot21.py must call validate_v1_archive_frozen.py")

    for capability in capabilities_rows:
        if capability.get("capability_id") != "v1_defensive_audit_closure":
            if capability.get("not_yet_implemented") is not True:
                return fail(f"{capability.get('capability_id')} must remain not_yet_implemented=true")
            if capability.get("execution_allowed") is not False:
                return fail(f"{capability.get('capability_id')} must remain execution_allowed=false")
        if capability.get("external_connectivity_allowed") is not False:
            return fail(f"{capability.get('capability_id')} must remain external_connectivity_allowed=false")
    if _find_capability(capabilities_rows, "research_os").get("status") != "RESEARCH_ONLY":
        return fail("Research OS must remain RESEARCH_ONLY")
    if _find_capability(capabilities_rows, "ai_news_event_engine").get("phase") != "V7_AI_NEWS_EVENT_ENGINE":
        return fail("AI / News / Event Engine phase mismatch")
    if _find_capability(capabilities_rows, "graphical_interface").get("phase") != "V8_UI_DASHBOARD":
        return fail("UI / Dashboard phase mismatch")
    if _find_capability(capabilities_rows, "account_analysis_read_only").get("phase") != "V9_ACCOUNT_READ_ONLY":
        return fail("Account Read-Only phase mismatch")
    if _find_capability(capabilities_rows, "sandbox_demo_trading").get("status") != "FUTURE_DEMO_ONLY":
        return fail("Sandbox Demo Trading must remain FUTURE_DEMO_ONLY")
    if _find_capability(capabilities_rows, "future_personal_live_trading").get("status") != "FUTURE_LIVE_GATED":
        return fail("Future Personal Live Trading must remain FUTURE_LIVE_GATED")

    for path in [
        registry_path,
        capabilities_path,
        roadmap_path,
        freeze_report_path,
        report_path,
        ROOT / LOT21_OVERVIEW_DOC_PATH,
        ROOT / LOT21_ACCEPTANCE_DOC_PATH,
        ROOT / LOT21_ROADMAP_DOC_PATH,
        ROOT / LOT21_COVERAGE_DOC_PATH,
    ]:
        message = validate_output_text(path)
        if message:
            return fail(message)

    catalog_records = DatasetCatalog(ROOT / DATASET_CATALOG_PATH).load()
    catalog_ids = [record.get("dataset_id") for record in catalog_records]
    if len(catalog_ids) != len(set(catalog_ids)):
        return fail("dataset_catalog contains duplicate dataset_id entries")
    if set(EXPECTED_CATALOG_IDS) - set(catalog_ids):
        return fail("dataset_catalog missing Lot 21 entries")

    registry_object = ProductScopeRegistry(
        **{
            **registry,
            "capabilities": [FunctionalCapability(**row) for row in capabilities_rows],
            "roadmap_phases": [RoadmapPhase(**row) for row in phase_rows if isinstance(row, dict)],
            "roadmap_lots": [RoadmapLot(**row) for row in roadmap_rows],
        }
    )
    write_validation_report(validation_report_path, registry=registry_object)
    validation_message = validate_output_text(validation_report_path)
    if validation_message:
        return fail(validation_message)

    print("LOT 21 VALIDATION: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

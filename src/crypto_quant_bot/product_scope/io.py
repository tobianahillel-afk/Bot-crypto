from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.product_scope.models import FunctionalCapability, ProductScopeRegistry, RoadmapLot, RoadmapPhase

MAX_JSON_BYTES = 2_000_000
MAX_JSONL_BYTES = 2_000_000
MAX_TEXT_BYTES = 1_000_000
MAX_JSONL_LINES = 512


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"json payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path, *, max_lines: int = MAX_JSONL_LINES) -> list[dict[str, Any]]:
    if path.stat().st_size > MAX_JSONL_BYTES:
        raise ValueError(f"jsonl payload too large: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > max_lines:
                raise ValueError(f"too many jsonl rows in {path}")
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"invalid jsonl row in {path}")
                rows.append(payload)
    return rows


def read_text_limited(path: Path, *, max_bytes: int = MAX_TEXT_BYTES) -> str:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _atomic_replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}{path.suffix}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_replace_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_capabilities_jsonl(path: Path, capabilities: list[FunctionalCapability]) -> None:
    lines = [json.dumps(capability.to_dict(), ensure_ascii=False, sort_keys=True) for capability in capabilities]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_roadmap_jsonl(path: Path, roadmap_lots: list[RoadmapLot]) -> None:
    lines = [json.dumps(roadmap_lot.to_dict(), ensure_ascii=False, sort_keys=True) for roadmap_lot in roadmap_lots]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def _source_archive_block(registry: ProductScopeRegistry) -> str:
    return (
        f"source_v1_archive_path = {registry.source_v1_archive_path}\n\n"
        f"source_v1_archive_frozen = {str(registry.source_v1_archive_frozen).lower()}\n\n"
        f"source_v1_archive_sha256 = {registry.source_v1_archive_sha256}\n\n"
        f"source_v1_archive_size_bytes = {registry.source_v1_archive_size_bytes}\n\n"
    )


def write_scope_report(path: Path, *, registry: ProductScopeRegistry) -> None:
    phase_lines = "".join(
        f"- {phase.phase_id}: {phase.start_lot_estimate} -> {phase.end_lot_estimate}\n"
        for phase in registry.roadmap_phases
    )
    body = (
        "# Lot 21-bis Product Scope Report\n\n"
        "Functional scope lock finalised after the V1 archive freeze guard, with no execution and no external connectivity.\n\n"
        f"Project: {registry.project_name}\n\n"
        f"Project identity: {registry.project_identity}\n\n"
        f"Project mode: {registry.project_mode}\n\n"
        f"V1 closure state: {registry.v1_closure_state}\n\n"
        f"V2 scope state: {registry.v2_scope_state}\n\n"
        f"Scope state: {registry.scope_state}\n\n"
        + _source_archive_block(registry)
        + "trade_allowed: false\n\n"
        + "execution_allowed: false\n\n"
        + "external_connectivity_allowed: false\n\n"
        + "Live execution: DISABLED\n\n"
        + "Leverage: FORBIDDEN\n\n"
        + f"capability_count: {registry.capability_count}\n\n"
        + f"phase_count: {registry.phase_count}\n\n"
        + f"future_lot_count: {registry.future_lot_count}\n\n"
        + f"scope_checksum: {registry.scope_checksum}\n\n"
        + "Lot 21-bis note: the project-manager-approved Lot 20-bis archive checksum 372f6e85353ce147766a4d4d724096aabb820c0872bffad14bf70a56f62d162d was overwritten on the canonical path before the freeze guard existed.\n\n"
        + "Lot 21-bis now freezes the currently validated archive at the canonical V1 path and forbids any V2 chain from regenerating or overwriting it.\n\n"
        + "Roadmap phases:\n"
        + f"{phase_lines}\n"
        + "The roadmap is forecast-only and remains blocked until dedicated implementation lots are approved.\n"
    )
    _atomic_replace_text(
        path,
        body,
    )


def write_roadmap_doc(path: Path, *, registry: ProductScopeRegistry) -> None:
    phase_sections = []
    for phase in registry.roadmap_phases:
        phase_sections.append(
            f"## {phase.phase_id} — {phase.title}\n\n"
            f"Objective: {phase.objective}\n\n"
            f"Estimated lot span: {phase.start_lot_estimate} to {phase.end_lot_estimate}\n\n"
            f"Status: {phase.status}\n\n"
            "Activation constraints:\n"
            + "".join(f"- {constraint}\n" for constraint in phase.activation_constraints)
            + "\nCapabilities:\n"
            + "".join(f"- `{capability}`\n" for capability in phase.capabilities)
            + "\n"
        )
    body = (
        "# V2 Product Roadmap\n\n"
        "Roadmap officielle V2+ du meme projet Crypto Quant Bot V3.1-Ops.\n\n"
        "Le Lot 21-bis existe parce que les premieres chaines V2 rejouaient encore la cloture V1 et pouvaient ecraser l'archive finale validee au Lot 20-bis.\n\n"
        "La V1 defensive/audit est fermee et reference uniquement une archive figee.\n\n"
        + _source_archive_block(registry)
        + "La V2 est ouverte uniquement comme cadrage fonctionnel et verrouillage de portefeuille de fonctionnalites.\n\n"
        + "Le Lot 22 pourra demarrer la Market Analysis Foundation en mode local/offline sans modifier l'archive V1 figee et sans activer le trading.\n\n"
        + "Le Lot 23 pourra ajouter un premier pack d'indicateurs techniques strictement descriptifs, toujours sans execution et sans connectivite externe.\n\n"
        + "Aucune phase ci-dessous n'est active au Lot 21. Chaque phase reste forecast-only jusqu'a validation d'un lot dedie.\n\n"
        + "".join(phase_sections)
    )
    _atomic_replace_text(path, body)


def write_coverage_doc(path: Path, *, registry: ProductScopeRegistry) -> None:
    lines = []
    for capability in registry.capabilities:
        lines.append(
            f"## {capability.capability_id}\n\n"
            f"Title: {capability.title}\n\n"
            f"Status: {capability.status}\n\n"
            f"Phase: {capability.phase}\n\n"
            f"Description: {capability.description}\n\n"
            f"Risk level: {capability.risk_level}\n\n"
            f"Not yet implemented: {str(capability.not_yet_implemented).lower()}\n\n"
            "Dependencies:\n"
            + ("- None\n" if not capability.depends_on else "".join(f"- `{dependency}`\n" for dependency in capability.depends_on))
            + "\nActivation gate:\n"
            + "".join(f"- {criterion}\n" for criterion in capability.acceptance_required_before_activation)
            + "\n"
        )
    body = (
        "# Functional Coverage Registry\n\n"
        "Registre complet du scope fonctionnel V2+ fige au Lot 21-bis.\n\n"
        "Le registre documente les modules attendus sans activer trading, connectivite externe ou interface operative.\n\n"
        + _source_archive_block(registry)
        + "Le Lot 21-bis confirme aussi que la V2 reference seulement l'archive V1 figee et n'a plus le droit de la regenerer.\n\n"
        + "".join(lines)
    )
    _atomic_replace_text(path, body)


def write_acceptance_doc(path: Path, *, registry: ProductScopeRegistry) -> None:
    criteria_lines = "".join(f"- {criterion}\n" for criterion in registry.acceptance_criteria)
    _atomic_replace_text(
        path,
        "# Acceptance Criteria - Lot 21-bis\n\n"
        "Le Lot 21-bis est accepte si :\n\n"
        "```text\n"
        "src/crypto_quant_bot/product_scope/__init__.py existe.\n"
        "src/crypto_quant_bot/product_scope/models.py existe.\n"
        "src/crypto_quant_bot/product_scope/registry.py existe.\n"
        "src/crypto_quant_bot/product_scope/io.py existe.\n"
        "scripts/validate_v1_archive_frozen.py existe.\n"
        "scripts/run_lot21_product_scope.py existe et produit les artefacts attendus.\n"
        "scripts/validate_lot21.py existe et valide le registre.\n"
        "scripts/validate_all_until_lot21.py existe.\n"
        "scripts/run_required_chain_until_lot21.sh existe.\n"
        "scripts/diagnose_lot21_required_chain_timing.py existe.\n"
        "scripts/diagnose_exact_chain_until_lot21.py existe.\n"
        "data/audit/product_scope_lot21.json existe.\n"
        "data/audit/product_scope_capabilities_lot21.jsonl existe.\n"
        "data/audit/product_scope_roadmap_lot21.jsonl existe.\n"
        "reports/lot_21_v1_archive_freeze_report.md existe.\n"
        "reports/lot_21_product_scope_report.md existe.\n"
        "reports/lot_21_validation_report.md existe.\n"
        "docs/LOT_21_PRODUCT_SCOPE.md existe.\n"
        "docs/V2_PRODUCT_ROADMAP.md existe.\n"
        "docs/FUNCTIONAL_COVERAGE_REGISTRY.md existe.\n"
        "docs/ACCEPTANCE_CRITERIA_LOT_21.md existe.\n"
        "project_name = Crypto Quant Bot V3.1-Ops.\n"
        "project_identity = SAME_PROJECT_NO_V4.\n"
        "v1_closure_state = V1_DEFENSIVE_AUDIT_CLOSED.\n"
        "v2_scope_state = OPENED_AS_PLANNING_ONLY.\n"
        "scope_state = FUNCTIONAL_SCOPE_LOCKED.\n"
        "source_v1_archive_path = dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz.\n"
        "source_v1_archive_frozen = true.\n"
        "source_v1_archive_sha256 est present.\n"
        "source_v1_archive_size_bytes est present.\n"
        "execution_allowed = false.\n"
        "trade_allowed = false.\n"
        "external_connectivity_allowed = false.\n"
        "live_execution = DISABLED.\n"
        "leverage = FORBIDDEN.\n"
        "scope_checksum est present.\n"
        "V1 ARCHIVE FROZEN VALIDATION: PASS.\n"
        "LOT 21 PRODUCT SCOPE: PASS.\n"
        "LOT 21 VALIDATION: PASS.\n"
        "LOT 21 ORCHESTRATED VALIDATION: PASS.\n"
        "LOT 21 REQUIRED CHAIN: PASS.\n"
        "DIAGNOSE LOT21 REQUIRED CHAIN TIMING: PASS.\n"
        "DIAGNOSE EXACT CHAIN LOT21: PASS.\n"
        "EXACT_CHAIN_LOT21_DONE.\n"
        "rc=0.\n"
        "```\n\n"
        "Acceptance details:\n"
        f"{criteria_lines}\n"
        "Apres acceptation, le Lot 22 peut uniquement ouvrir une couche Market Analysis locale/offline, sans execution et sans regeneration de l'archive V1.\n\n"
        "Le Lot 21-bis reste un registre de cadrage uniquement, sans execution, sans ordre, sans connectivite externe et sans module actif de trading.\n"
    )


def write_overview_doc(path: Path, *, registry: ProductScopeRegistry) -> None:
    body = (
        "# Lot 21-bis Product Scope\n\n"
        "Le Lot 21-bis finalise le Lot 21 apres correction d'un probleme bloquant de regeneration de l'archive V1 dans des chaines V2.\n\n"
        "La V2 reste ouverte uniquement comme registre fonctionnel et roadmap officielle, sans implementation active.\n\n"
        f"Project: {registry.project_name}\n\n"
        f"Project identity: {registry.project_identity}\n\n"
        f"V1 closure state: {registry.v1_closure_state}\n\n"
        f"V2 scope state: {registry.v2_scope_state}\n\n"
        f"Scope state: {registry.scope_state}\n\n"
        + _source_archive_block(registry)
        + "Le scope couvre explicitement l'analyse de marche, la microstructure offline, le Scenario Engine, l'Expected Value Engine, le Research OS, l'AI / News / Event Engine, l'UI / Dashboard, les modules read-only, le sandbox/demo trading et la gouvernance future du live personnel.\n\n"
        + "Aucun de ces blocs n'est actif au Lot 21. Toute implementation future doit passer par un lot dedie avec audit et validation propres.\n\n"
        + "Les chaines V2 ne doivent plus regenerer l'archive V1 et doivent seulement la valider comme source figee.\n\n"
        + "Le Lot 22 est reserve a une Market Analysis Foundation locale/offline, toujours non executable et sans connectivite externe.\n"
    )
    _atomic_replace_text(path, body)


def write_validation_report(path: Path, *, registry: ProductScopeRegistry) -> None:
    body = (
        "# Lot 21-bis Validation Report\n\n"
        "Status: PASS\n\n"
        f"Project: {registry.project_name}\n\n"
        f"Project identity: {registry.project_identity}\n\n"
        f"V1 closure state: {registry.v1_closure_state}\n\n"
        f"V2 scope state: {registry.v2_scope_state}\n\n"
        f"Scope state: {registry.scope_state}\n\n"
        + _source_archive_block(registry)
        + "trade_allowed: false\n\n"
        + "execution_allowed: false\n\n"
        + "external_connectivity_allowed: false\n\n"
        + "Live execution: DISABLED\n\n"
        + "Leverage: FORBIDDEN\n\n"
        + f"capability_count: {registry.capability_count}\n\n"
        + f"phase_count: {registry.phase_count}\n\n"
        + f"future_lot_count: {registry.future_lot_count}\n\n"
        + f"scope_checksum: {registry.scope_checksum}\n\n"
        + "Le registre confirme que toutes les activations futures restent bloquees, soumises a revue humaine et reference uniquement l'archive V1 figee.\n"
    )
    _atomic_replace_text(path, body)

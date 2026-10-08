#!/usr/bin/env python3
"""Adversarial qualification for registered documentation consistency."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    path = ROOT / "scripts" / "governance" / "validate_documentation_consistency.py"
    spec = importlib.util.spec_from_file_location("documentation_consistency_selftest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"documentation-consistency negative scenario unexpectedly passed: {label}")


def _item(registry: dict[str, Any], path: str) -> dict[str, Any]:
    return next(item for item in registry["documents"] if item["path"] == path)


def main() -> int:
    mod = _module()
    policy = mod._json(mod.POLICY_PATH)
    registry = mod._json(ROOT / policy["authority_registry"])
    state = mod._json(ROOT / policy["state_source"])
    mod.validate_policy(policy)
    mod.validate_registry(registry)
    mod.run()

    identity = _item(registry, "docs/PROJECT_IDENTITY.md")
    identity_text = (ROOT / identity["path"]).read_text(encoding="utf-8")
    _expect(
        mod.DocumentationConsistencyError,
        lambda: mod.validate_document(
            identity,
            identity_text.replace("Crypto Quant Bot V3.1-Ops", "Crypto Quant Bot V4.1-Ops"),
            canonical_identity=state["project"]["canonical_name"],
            bridge_path=registry["compatibility_bridge"]["path"],
        ),
        "legacy project identity",
    )

    roadmap = _item(registry, "docs/ROADMAP_V1_TO_V21.md")
    roadmap_text = (ROOT / roadmap["path"]).read_text(encoding="utf-8")
    _expect(
        mod.DocumentationConsistencyError,
        lambda: mod.validate_document(
            roadmap,
            roadmap_text.replace("config/governance/project_state.json", "engineering/STATE.json"),
            canonical_identity=state["project"]["canonical_name"],
            bridge_path=registry["compatibility_bridge"]["path"],
        ),
        "legacy current authority",
    )

    coverage = _item(registry, "docs/FUNCTIONAL_COVERAGE_REGISTRY.md")
    coverage_text = (ROOT / coverage["path"]).read_text(encoding="utf-8")
    _expect(
        mod.DocumentationConsistencyError,
        lambda: mod.validate_document(
            coverage,
            coverage_text.replace("Snapshot de couverture métier", "Statut courant dérivé"),
            canonical_identity=state["project"]["canonical_name"],
            bridge_path=registry["compatibility_bridge"]["path"],
        ),
        "snapshot mislabeled as current state",
    )

    agents = _item(registry, "AGENTS.md")
    agents_text = (ROOT / agents["path"]).read_text(encoding="utf-8")
    mod.validate_document(
        agents,
        agents_text,
        canonical_identity=state["project"]["canonical_name"],
        bridge_path=registry["compatibility_bridge"]["path"],
    )
    _expect(
        mod.DocumentationConsistencyError,
        lambda: mod.validate_document(
            agents,
            agents_text.replace("migration compatibility bridge", "current authority"),
            canonical_identity=state["project"]["canonical_name"],
            bridge_path=registry["compatibility_bridge"]["path"],
        ),
        "bridge presented as authority",
    )

    duplicate = copy.deepcopy(registry)
    duplicate["documents"].append(copy.deepcopy(duplicate["documents"][0]))
    _expect(mod.DocumentationConsistencyError, lambda: mod.validate_registry(duplicate), "duplicate registered document")

    broad = copy.deepcopy(policy)
    broad["scan_scope"] = "ALL_DOCS"
    _expect(mod.DocumentationConsistencyError, lambda: mod.validate_policy(broad), "historical global scan")

    paid = copy.deepcopy(policy)
    paid["cost_policy"]["paid_saas_required"] = True
    _expect(mod.DocumentationConsistencyError, lambda: mod.validate_policy(paid), "paid documentation gate")

    print("DOCUMENTATION_CONSISTENCY_SELFTEST_PASS probes=7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

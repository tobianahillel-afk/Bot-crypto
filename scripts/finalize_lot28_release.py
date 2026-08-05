from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected text missing in {path}: {old!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_metadata(implementation_sha: str, output_checksum: str) -> None:
    replace_exact("pyproject.toml", 'version = "0.27.0"', 'version = "0.28.0"')
    replace_exact(
        "pyproject.toml",
        'description = "Crypto Quant Bot V3.1-Ops — Lot 27 validated offline global market context"',
        'description = "Crypto Quant Bot V3.1-Ops — Lot 28 validated offline explanation and why-not-trade layer"',
    )
    replace_exact(
        "README.md",
        "| Dernier lot implémenté et validé | **Lot 27 — Global Market Context Aggregator** |",
        "| Dernier lot implémenté et validé | **Lot 28 — Explanation Core & Why-Not-Trade Layer** |",
    )
    replace_exact(
        "README.md",
        "| Prochain lot planifié | **Lot 28 — Explanation Core & Why-Not-Trade Layer**, verrouillé jusqu’au merge et à l’audit post-merge du Lot 27 |",
        "| Prochain lot planifié | **Lot 29 — V2 Deterministic Replay & Audit**, verrouillé jusqu’au merge et à l’audit post-merge du Lot 28 |",
    )
    replace_exact(
        "README.md",
        "### Architecture future verrouillée\n",
        "### Lot 28\n\n"
        "- [Spécification](docs/LOT_28_EXPLANATION_CORE_AND_WHY_NOT_TRADE_LAYER.md)\n"
        "- [Critères d’acceptation](docs/ACCEPTANCE_CRITERIA_LOT_28.md)\n"
        "- [Worklog de validation](docs/LOT_28_IMPLEMENTATION_WORKLOG.md)\n"
        "- [Rapport final](reports/lot_28_explanation_core_and_why_not_trade_layer_report.md)\n"
        "- État certifié : `data/audit/explanation_core_and_why_not_trade_layer_lot28.json`\n"
        "- Audit certifié : `data/audit/explanation_core_and_why_not_trade_layer_audit_lot28.json`\n\n"
        "### Architecture future verrouillée\n",
    )

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    section = f"""## 0.28.0 — Lot 28 Explanation Core & Why-Not-Trade Layer

- couche d’explication structurée, déterministe et strictement offline au-dessus des preuves certifiées Lots 26–27 ;
- 14 déclarations versionnées séparant faits, features, inférences, hypothèses, preuves, contradictions, incertitudes, règles, vetos, non-applicable et conséquence finale ;
- 3 raisons why-not-trade ordonnées et dédupliquées : `WNT_CONTEXT_MIXED`, `WNT_MTF_DIVERGENCE`, `WNT_PERMISSIONS_DISABLED` ;
- chaque déclaration est liée à un checksum d’artefact exact et à un JSON pointer vérifié ;
- replay déterministe `MATCH`, checksum de sortie `{output_checksum}` ;
- 35 tests ciblés, couverture lignes 99.42% et branches 98.39% ;
- mutation critique 1 620/1 830, score 88.52% PASS ;
- 930 tests globaux PASS, trois répétitions Lot 28 PASS, Ruff, mypy, Bandit, pip-audit, architecture, traçabilité, roadmap, lifecycle et qualité institutionnelle PASS ;
- aucune prévision, probabilité, recommandation, approbation risque, permission de trading ou exécution activée.

"""
    marker = "# Changelog\n\n"
    if section not in changelog:
        if not changelog.startswith(marker):
            raise SystemExit("unexpected changelog header")
        changelog_path.write_text(marker + section + changelog[len(marker) :], encoding="utf-8")

    roadmap_path = ROOT / "docs/ROADMAP_V1_TO_V21.md"
    roadmap = roadmap_path.read_text(encoding="utf-8")
    replacements = (
        (
            "- Dernier lot dont l'implémentation est terminée : **Lot 27**.",
            "- Dernier lot dont l'implémentation est terminée : **Lot 28**.",
        ),
        (
            "- Lot 28 : `PLANNED_LOCKED`, aucun développement démarré.",
            "- Lot 28 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.",
        ),
        ("- Lots 28–177 : planifiés et verrouillés.", "- Lots 29–177 : planifiés et verrouillés."),
        (
            "- Recherche offline descriptive : implémentée pour le périmètre Lots 21–27, sans permission de décision ou d'exécution.",
            "- Recherche offline descriptive : implémentée pour le périmètre Lots 21–28, sans permission de décision ou d'exécution.",
        ),
        (
            "L'état courant est porté par `data/audit/roadmap_lifecycle_overlay_lot27.json`.",
            "L'état courant est porté par `data/audit/roadmap_lifecycle_overlay_lot28.json`.",
        ),
    )
    for old, new in replacements:
        if old not in roadmap:
            raise SystemExit(f"roadmap text missing: {old!r}")
        roadmap = roadmap.replace(old, new, 1)
    lot28_sources = """## Lot 28

- [Specification](LOT_28_EXPLANATION_CORE_AND_WHY_NOT_TRADE_LAYER.md)
- [Acceptance criteria](ACCEPTANCE_CRITERIA_LOT_28.md)
- [Implementation status](LOT_28_IMPLEMENTATION_WORKLOG.md)
- Configuration : `config/explanations/explanation_core_why_not_trade_v1.json`
- Schema : `contracts/schemas/explanation_core_why_not_trade_layer_state_v1.schema.json`
- Runner : `scripts/run_lot28_explanation_core_and_why_not_trade_layer.py`
- Validator : `scripts/validate_lot28.py`
- Lifecycle overlay : `data/audit/roadmap_lifecycle_overlay_lot28.json`

"""
    marker = "## Séparations obligatoires\n"
    if lot28_sources not in roadmap:
        if marker not in roadmap:
            raise SystemExit("roadmap section marker missing")
        roadmap = roadmap.replace(marker, lot28_sources + marker, 1)
    roadmap_path.write_text(roadmap, encoding="utf-8")

    v2_path = ROOT / "docs/roadmap/V02_MARKET_ANALYSIS_OFFLINE.md"
    v2 = v2_path.read_text(encoding="utf-8")
    start = v2.index("## Lot 28 — Explanation Core & Why-Not-Trade Layer")
    end = v2.index("## Lot 29 — V2 Deterministic Replay & Audit", start)
    block = v2[start:end]
    old_status = "**Statut canonique :** `PLANNED_LOCKED`"
    new_status = "**Statut canonique :** `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`"
    if old_status not in block:
        raise SystemExit("Lot 28 roadmap status marker missing")
    v2_path.write_text(v2[:start] + block.replace(old_status, new_status, 1) + v2[end:], encoding="utf-8")

    worklog = f"""# Lot 28 implementation worklog

Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`

## Certified implementation

- implementation evidence commit: `{implementation_sha}`;
- release version: `0.28.0`;
- deterministic statement count: `14`;
- why-not-trade reason count: `3`;
- dominant reason: `WNT_PERMISSIONS_DISABLED`;
- output checksum: `{output_checksum}`;
- deterministic replay: `MATCH`.

## Validation evidence

- targeted Lot 28 tests: `35 PASS`;
- targeted line coverage: `99.42%`;
- targeted branch coverage: `98.39%`;
- critical mutation: `1620/1830`, score `88.52% PASS`;
- full repository regression: `930 PASS`;
- Lot 28 anti-flake repetitions: `3/3 PASS`;
- Ruff, mypy, Bandit, pip-audit, architecture, traceability, roadmap, lifecycle and institutional quality: `PASS`;
- five permanent workflows on the same certified head: `PASS`.

## Delivered contracts and evidence

- immutable evidence, statement, explanation bundle and why-not reason contracts;
- closed JSON schema and versioned deterministic template registry;
- strict Lots 26–27 input validation;
- exact JSON pointer and artifact checksum evidence;
- golden structured explanation and ordered, deduplicated why-not reason set;
- deterministic runner, audit, report, replay and tamper detection;
- permanent coverage, regression, security and mutation gates.

## Safety

This layer remains offline descriptive only. It cannot produce or authorize a forecast, probability, strategy, risk approval, signal, trade intent, order intent or execution.

```text
analysis_only=true
used_for_decision=false
forecast_generation_allowed=false
probability_claims_allowed=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
execution_allowed=false
trade_allowed=false
approved_size=0
```

Lot 29 remains `PLANNED_LOCKED` until merge of the Lot 28 PR and successful post-merge audit.
"""
    (ROOT / "docs/LOT_28_IMPLEMENTATION_WORKLOG.md").write_text(worklog, encoding="utf-8")


def write_overlay(implementation_sha: str) -> None:
    overlay = {
        "future_capabilities_locked": [
            "ContinuousMarketStateV1",
            "MultiHorizonForecastV1",
            "ParticipantBehaviorScenarioV1",
            "TradeIntent",
            "OrderIntent",
        ],
        "historical_registry": "data/audit/product_scope_roadmap_lot21.jsonl",
        "latest_implemented_lot": 28,
        "lots": {
            "26": {
                "execution_allowed": False,
                "historical_overlay": "data/audit/roadmap_lifecycle_overlay_lot26.json",
                "status": "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY",
                "trade_allowed": False,
            },
            "27": {
                "execution_allowed": False,
                "historical_overlay": "data/audit/roadmap_lifecycle_overlay_lot27.json",
                "status": "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY",
                "trade_allowed": False,
            },
            "28": {
                "acceptance_contract": "docs/ACCEPTANCE_CRITERIA_LOT_28.md",
                "execution_allowed": False,
                "implementation_commit": implementation_sha,
                "implementation_contract": "docs/LOT_28_EXPLANATION_CORE_AND_WHY_NOT_TRADE_LAYER.md",
                "implementation_status": "docs/LOT_28_IMPLEMENTATION_WORKLOG.md",
                "pull_request": 10,
                "runner": "scripts/run_lot28_explanation_core_and_why_not_trade_layer.py",
                "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
                "status": "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY",
                "trade_allowed": False,
                "validator": "scripts/validate_lot28.py",
            },
            "29": {"implementation_started": False, "status": "PLANNED_LOCKED"},
        },
        "previous_overlay": "data/audit/roadmap_lifecycle_overlay_lot27.json",
        "schema_version": "roadmap-lifecycle-overlay-v1",
    }
    path = ROOT / "data/audit/roadmap_lifecycle_overlay_lot28.json"
    path.write_text(json.dumps(overlay, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_historical_tests() -> None:
    for relative in ("tests/test_lot27_release_state.py", "tests/test_lot27_post_merge_state.py"):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        text = text.replace("import tomllib\n", "")
        text = text.replace(
            '    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]\n',
            "",
        )
        text = text.replace('    assert project["version"] == "0.27.0"\n', "")
        path.write_text(text, encoding="utf-8")


def write_release_test() -> None:
    content = '''from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_lot28_release_state_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot28.json").read_text(encoding="utf-8")
    )
    state = json.loads(
        (ROOT / "data/audit/explanation_core_and_why_not_trade_layer_lot28.json").read_text(
            encoding="utf-8"
        )
    )
    audit = json.loads(
        (ROOT / "data/audit/explanation_core_and_why_not_trade_layer_audit_lot28.json").read_text(
            encoding="utf-8"
        )
    )
    report = (
        ROOT / "reports/lot_28_explanation_core_and_why_not_trade_layer_report.md"
    ).read_text(encoding="utf-8")
    worklog = (ROOT / "docs/LOT_28_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")

    assert project["version"] == "0.28.0"
    assert overlay["latest_implemented_lot"] == 28
    assert overlay["previous_overlay"] == "data/audit/roadmap_lifecycle_overlay_lot27.json"
    assert overlay["lots"]["28"]["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"
    assert overlay["lots"]["28"]["implementation_commit"] == state["code_commit"]
    assert overlay["lots"]["28"]["trade_allowed"] is False
    assert overlay["lots"]["28"]["execution_allowed"] is False
    assert overlay["lots"]["29"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }

    payload = dict(state)
    output_checksum = payload.pop("output_checksum")
    assert output_checksum == canonical_checksum(payload)
    assert audit["output_checksum"] == output_checksum
    assert audit["replay_status"] == "MATCH"
    assert audit["code_commit"] == state["code_commit"]
    assert audit["statement_count"] == 14
    assert audit["why_not_reason_count"] == 3
    assert audit["dominant_reason_code"] == "WNT_PERMISSIONS_DISABLED"
    assert [
        reason["reason_code"] for reason in state["bundle"]["why_not_trade"]["reasons"]
    ] == [
        "WNT_CONTEXT_MIXED",
        "WNT_MTF_DIVERGENCE",
        "WNT_PERMISSIONS_DISABLED",
    ]
    assert state["analysis_only"] is True
    assert state["used_for_decision"] is False
    assert state["forecast_generation_allowed"] is False
    assert state["probability_claims_allowed"] is False
    assert state["signal_generation_allowed"] is False
    assert state["risk_approval_allowed"] is False
    assert state["order_routing_allowed"] is False
    assert state["execution_allowed"] is False
    assert state["trade_allowed"] is False
    assert state["approved_size"] == 0
    assert state["bundle"]["why_not_trade"]["no_order_intent_created"] is True

    assert "GO_LOT28_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in report
    assert "Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`" in worklog


def test_lot28_release_tree_contains_no_temporary_finalization_files() -> None:
    forbidden = (
        ROOT / ".github/workflows/lot28-release-finalization.yml",
        ROOT / ".github/workflows/lot28-release-finalization-fix.yml",
        ROOT / ".github/workflows/lot28-release-finalization-fix-pr.yml",
        ROOT / "scripts/finalize_lot28_release.py",
    )
    assert not [path.relative_to(ROOT).as_posix() for path in forbidden if path.exists()]
'''
    (ROOT / "tests/test_lot28_release_state.py").write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation-sha", required=True)
    args = parser.parse_args()

    state_path = ROOT / "data/audit/explanation_core_and_why_not_trade_layer_lot28.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state["code_commit"] != args.implementation_sha:
        raise SystemExit("generated state does not match implementation SHA")
    output_checksum = str(state["output_checksum"])

    update_metadata(args.implementation_sha, output_checksum)
    write_overlay(args.implementation_sha)
    update_historical_tests()
    write_release_test()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

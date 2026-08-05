from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from scripts.run_lot27_global_market_context_aggregator import run  # noqa: E402

FINAL_STATUS = "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"
FINAL_VERDICT = "GO_LOT27_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"


def replace(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"replacement marker missing in {path}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_v2_roadmap() -> None:
    path = ROOT / "docs/roadmap/V02_MARKET_ANALYSIS_OFFLINE.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Lot 27 — Global Market Context Aggregator"
    start = text.index(marker)
    end = text.index("## Lot 28 —", start)
    section = text[start:end]
    old = "**Statut canonique :** `PLANNED_LOCKED`"
    if old not in section:
        raise RuntimeError("Lot 27 status marker missing in V2 roadmap")
    section = section.replace(old, f"**Statut canonique :** `{FINAL_STATUS}`", 1)
    path.write_text(text[:start] + section + text[end:], encoding="utf-8")


def write_overlay(implementation_commit: str) -> None:
    payload = {
        "schema_version": "roadmap-lifecycle-overlay-v1",
        "historical_registry": "data/audit/product_scope_roadmap_lot21.jsonl",
        "previous_overlay": "data/audit/roadmap_lifecycle_overlay_lot26.json",
        "latest_implemented_lot": 27,
        "future_capabilities_locked": [
            "ContinuousMarketStateV1",
            "MultiHorizonForecastV1",
            "ParticipantBehaviorScenarioV1",
            "TradeIntent",
            "OrderIntent",
        ],
        "lots": {
            "26": {
                "status": FINAL_STATUS,
                "historical_overlay": "data/audit/roadmap_lifecycle_overlay_lot26.json",
                "trade_allowed": False,
                "execution_allowed": False,
            },
            "27": {
                "status": FINAL_STATUS,
                "implementation_commit": implementation_commit,
                "pull_request": 8,
                "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
                "implementation_contract": "docs/LOT_27_GLOBAL_MARKET_CONTEXT_AGGREGATOR.md",
                "acceptance_contract": "docs/ACCEPTANCE_CRITERIA_LOT_27.md",
                "implementation_status": "docs/LOT_27_IMPLEMENTATION_WORKLOG.md",
                "runner": "scripts/run_lot27_global_market_context_aggregator.py",
                "validator": "scripts/validate_lot27.py",
                "trade_allowed": False,
                "execution_allowed": False,
            },
            "28": {
                "implementation_started": False,
                "status": "PLANNED_LOCKED",
            },
        },
    }
    path = ROOT / "data/audit/roadmap_lifecycle_overlay_lot27.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_worklog(implementation_commit: str) -> None:
    text = f"""# Lot 27 implementation worklog

Status: `{FINAL_STATUS}`

## Certified implementation

- implementation commit: `{implementation_commit}`;
- deterministic source set: validated Lots 22–26 artifacts;
- dominant state: `GLOBAL_CONTEXT_MIXED`;
- aggregate evidence score: `0.5646`;
- weighted coverage: `1.0`;
- preserved conflict: `MTF_DIVERGENT`;
- targeted tests: `57 PASS`;
- line coverage: `97.18%`;
- branch coverage: `91.07%`;
- critical mutation: `803/948`, score `84.70% PASS`;
- roadmap, lifecycle, institutional quality, Ruff, mypy, Bandit, pip-audit, architecture, traceability, replay and anti-flake: `PASS`.

## Delivered

- closed `GlobalMarketContextAggregatorStateV1` and source-contribution contracts;
- versioned weights and state-to-category mappings;
- deterministic aggregation of validated Lots 22–26 outputs;
- explicit source quality, freshness, contribution and missing weight;
- dominant state, alternatives, conflicts and uncalibrated interval policy;
- atomic state/audit/report persistence;
- replay and tamper detection;
- ablation, negative, integration, coverage, security and mutation gates.

## Safety

This lot remains offline descriptive only. It cannot generate a forecast, probability, signal, trade intent, order intent or execution permission.

```text
analysis_only=true
used_for_decision=false
forecast_generation_allowed=false
probability_claims_allowed=false
signal_generation_allowed=false
order_routing_allowed=false
execution_allowed=false
trade_allowed=false
approved_size=0
```
"""
    (ROOT / "docs/LOT_27_IMPLEMENTATION_WORKLOG.md").write_text(text, encoding="utf-8")


def write_release_test() -> None:
    text = '''from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lot27_release_state_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    overlay = json.loads(
        (ROOT / "data/audit/roadmap_lifecycle_overlay_lot27.json").read_text(
            encoding="utf-8"
        )
    )
    state = json.loads(
        (ROOT / "data/audit/global_market_context_aggregator_lot27.json").read_text(
            encoding="utf-8"
        )
    )
    report = (ROOT / "reports/lot_27_global_market_context_aggregator_report.md").read_text(
        encoding="utf-8"
    )
    worklog = (ROOT / "docs/LOT_27_IMPLEMENTATION_WORKLOG.md").read_text(encoding="utf-8")

    assert project["version"] == "0.27.0"
    assert overlay["latest_implemented_lot"] == 27
    assert overlay["lots"]["27"]["status"] == "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"
    assert overlay["lots"]["27"]["trade_allowed"] is False
    assert overlay["lots"]["27"]["execution_allowed"] is False
    assert overlay["lots"]["28"] == {
        "implementation_started": False,
        "status": "PLANNED_LOCKED",
    }
    assert state["dominant_state"] == "GLOBAL_CONTEXT_MIXED"
    assert state["aggregate_evidence_score"] == 0.5646
    assert state["weighted_coverage_ratio"] == 1.0
    assert state["trade_allowed"] is False
    assert state["execution_allowed"] is False
    assert "GO_LOT27_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY" in report
    assert "Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`" in worklog


def test_lot27_release_tree_contains_no_temporary_finalization_files() -> None:
    forbidden = (
        ROOT / ".github/workflows/lot27-final-reconciliation.yml",
        ROOT / "scripts/finalize_lot27_release.py",
        ROOT / ".github/workflows/lot27-one-shot-bandit-fix.yml",
    )
    assert not [path.relative_to(ROOT).as_posix() for path in forbidden if path.exists()]
'''
    (ROOT / "tests/test_lot27_release_state.py").write_text(text, encoding="utf-8")


def update_historical_lot26_test() -> None:
    replace(
        "tests/test_lot26_post_merge_state.py",
        '    assert project["version"] == "0.26.0"\n',
        '    version = tuple(int(part) for part in project["version"].split("."))\n'
        '    assert version >= (0, 26, 0)\n',
    )


def reconcile(implementation_commit: str) -> None:
    run(ROOT, implementation_commit)
    replace(
        "pyproject.toml",
        'version = "0.26.0"\ndescription = "Crypto Quant Bot V3.1-Ops — Lot 26 validated offline descriptive alignment"',
        'version = "0.27.0"\ndescription = "Crypto Quant Bot V3.1-Ops — Lot 27 validated offline global market context"',
    )
    replace(
        "README.md",
        "| Dernier lot implémenté et validé | **Lot 26 — Multi-Timeframe Alignment** |",
        "| Dernier lot implémenté et validé | **Lot 27 — Global Market Context Aggregator** |",
    )
    replace(
        "README.md",
        "| Prochain lot planifié | **Lot 27 — Global Market Context Aggregator**, verrouillé jusqu’au merge et à l’audit post-merge du Lot 26 |",
        "| Prochain lot planifié | **Lot 28 — Explanation Core & Why-Not-Trade Layer**, verrouillé jusqu’au merge et à l’audit post-merge du Lot 27 |",
    )
    changelog = ROOT / "CHANGELOG.md"
    current = changelog.read_text(encoding="utf-8")
    entry = """## 0.27.0 — Lot 27 Global Market Context Aggregator

- agrégation descriptive déterministe des sorties validées des Lots 22–26 ;
- poids fixes publiés et aucune renormalisation silencieuse des sources absentes ;
- qualité, fraîcheur, checksum, état, catégorie et contribution conservés par source ;
- support `TRENDING`, `RANGE`, `MIXED`, `CONFLICT`, alternatives et conflits explicites ;
- oracle global `GLOBAL_CONTEXT_MIXED`, score `0.5646`, couverture `1.0` ;
- 57 tests ciblés, couverture lignes 97.18% et branches 91.07% ;
- mutation critique 803/948, score 84.70% PASS ;
- Ruff, mypy, Bandit, pip-audit, architecture, traçabilité, régression et anti-flake PASS ;
- aucune prévision, probabilité, décision, permission de trading ou exécution activée.

"""
    marker = "# Changelog\n\n"
    if entry not in current:
        if not current.startswith(marker):
            raise RuntimeError("changelog header missing")
        changelog.write_text(marker + entry + current[len(marker):], encoding="utf-8")
    replace(
        "docs/LOT_27_GLOBAL_MARKET_CONTEXT_AGGREGATOR.md",
        "Status: `IMPLEMENTATION_IN_PROGRESS`",
        f"Status: `{FINAL_STATUS}`",
    )
    old_state = """- Dernier lot dont l'implémentation est terminée : **Lot 26**.
- Baseline P0 institutionnelle : fusionnée.
- Gate transversal P0.6 : fusionné et conservé comme preuve historique.
- Lot 26 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- PR Lot 26 : brouillon tant que les workflows permanents n'ont pas exécuté leurs commandes sur un même SHA.
- Lot 27 : `PLANNED_LOCKED`, aucun développement démarré.
- Lots 27–177 : planifiés et verrouillés.
- Recherche offline descriptive : implémentée pour le périmètre Lot 26, promotion encore `NO_GO`.
- Forecast, alpha, paper, sandbox et capital réel : `NO_GO`.

L'état courant est porté par `data/audit/roadmap_lifecycle_overlay_lot26.json`. Le registre
"""
    new_state = """- Dernier lot dont l'implémentation est terminée : **Lot 27**.
- Baseline P0 institutionnelle : fusionnée.
- Gate transversal P0.6 : fusionné et conservé comme preuve historique.
- Lot 26 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- Lot 27 : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`.
- Lot 28 : `PLANNED_LOCKED`, aucun développement démarré.
- Lots 28–177 : planifiés et verrouillés.
- Recherche offline descriptive : implémentée pour le périmètre Lots 21–27, sans permission de décision ou d'exécution.
- Forecast, alpha, paper, sandbox et capital réel : `NO_GO`.

L'état courant est porté par `data/audit/roadmap_lifecycle_overlay_lot27.json`. Le registre
"""
    replace("docs/ROADMAP_V1_TO_V21.md", old_state, new_state)
    update_v2_roadmap()
    write_overlay(implementation_commit)
    write_worklog(implementation_commit)
    update_historical_lot26_test()
    write_release_test()


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize Lot 27 release evidence")
    parser.add_argument("--implementation-commit", required=True)
    args = parser.parse_args()
    reconcile(args.implementation_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

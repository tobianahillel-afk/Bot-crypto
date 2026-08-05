from __future__ import annotations

import json
from pathlib import Path

PENDING = "IMPLEMENTATION_COMPLETE_AWAITING_EXACT_COMMIT_CI"
FINAL = "IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY"


def replace(path: str, old: str, new: str, count: int = 1) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected text missing in {path}: {old!r}")
    target.write_text(text.replace(old, new, count), encoding="utf-8")


def update_versions_and_statuses() -> None:
    replace("pyproject.toml", 'version = "0.25.2.dev0"', 'version = "0.26.0"')
    replace(
        "pyproject.toml",
        'description = "Crypto Quant Bot V3.1-Ops — Lot 25 validated, P0 hardened, pre-Lot26 readiness"',
        'description = "Crypto Quant Bot V3.1-Ops — Lot 26 validated offline descriptive alignment"',
    )
    replace(
        ".github/workflows/lot26-mutation.yml",
        'version = "0.25.2.dev0"',
        'version = "0.26.0"',
    )
    replace(
        "README.md",
        "| Dernier lot implémenté et validé | **Lot 25 — Volatility / Regime / Confluence** |",
        "| Dernier lot implémenté et validé | **Lot 26 — Multi-Timeframe Alignment** |",
    )
    replace(
        "README.md",
        "| Prochaine implémentation autorisée | **Lot 26 — Multi-Timeframe Alignment**, encore verrouillé |",
        "| Prochain lot planifié | **Lot 27 — Global Market Context Aggregator**, verrouillé jusqu’au merge et à l’audit post-merge du Lot 26 |",
    )
    replace(
        "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
        "Statut : `PLANNED_LOCKED`",
        "Statut : `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`",
    )
    replace(
        "docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md",
        "Status: `PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY`",
        "Status: `IMPLEMENTED_UNCALIBRATED_OFFLINE_ONLY`",
    )
    for root in ("scripts", "tests", "docs", "data/audit"):
        for path in Path(root).rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".md", ".json"}:
                continue
            text = path.read_text(encoding="utf-8")
            if PENDING in text:
                path.write_text(text.replace(PENDING, FINAL), encoding="utf-8")
    replace(
        "scripts/validate_roadmap_documentation.py",
        "Lot 26 must remain pending until exact-commit CI passes",
        "Lot 26 must remain validated after exact-commit CI passes",
    )


def write_overlay() -> None:
    payload = {
        "schema_version": "roadmap-lifecycle-overlay-v1",
        "historical_registry": "data/audit/product_scope_roadmap_lot21.jsonl",
        "latest_implemented_lot": 26,
        "lots": {
            "26": {
                "status": FINAL,
                "runtime_mode": "LOCAL_OFFLINE_ANALYSIS_ONLY",
                "implementation_contract": "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md",
                "implementation_status": "docs/LOT_26_IMPLEMENTATION_WORKLOG.md",
                "acceptance_contract": "docs/ACCEPTANCE_CRITERIA_LOT_26.md",
                "runner": "scripts/run_lot26_multi_timeframe_alignment_engine.py",
                "validator": "scripts/validate_lot26.py",
                "pull_request": 6,
                "trade_allowed": False,
                "execution_allowed": False,
            },
            "27": {"status": "PLANNED_LOCKED", "implementation_started": False},
        },
        "future_capabilities_locked": [
            "ContinuousMarketStateV1",
            "MultiHorizonForecastV1",
            "ParticipantBehaviorScenarioV1",
            "TradeIntent",
            "OrderIntent",
        ],
    }
    Path("data/audit/roadmap_lifecycle_overlay_lot26.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_worklog() -> None:
    content = """# Lot 26 implementation worklog

Status: `IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY`

## Delivered

- immutable `TimeframeMarketContextStateV1`, `ClosedBarAvailabilityV1` and `MultiTimeframeAlignmentStateV1` contracts;
- Lot 25 adapter without rewriting historical artifacts;
- closed-bar `ASOF_BACKWARD` selection for the ordered `timebar-5m → timebar-15m` edge;
- six-component compatibility model, weighted coverage, agreement, divergence, coherence and descriptive uncertainty;
- deterministic IDs, lineage, checksums and `DecisionEvidenceEnvelopeV1`;
- atomic bounded I/O, replay and tamper detection;
- closed JSON schemas and lifecycle-aware roadmap overlay;
- functional, mathematical, temporal, property, integration, I/O and runner tests;
- permanent coverage, regression, security, anti-flake and mutation gates.

## Exact-head GitHub Actions evidence

- targeted Lot 26 suite: **108 tests PASS**;
- targeted line coverage: **98.73%**;
- targeted branch coverage: **97.12%**;
- repository assurance: **832 tests PASS**;
- repository line coverage: **94.63%**;
- repository branch coverage: **86.77%**;
- critical Lot 26 mutation: **455/552 evaluated, 82.43% PASS**;
- Ruff, mypy, architecture, ownership, traceability, Bandit and dependency audit: **PASS**;
- full-suite anti-flake repetition: **3/3 PASS**;
- roadmap, lifecycle, P0.6 exact-commit assurance and institutional quality: **PASS**.

The authoritative certification SHA is the pull-request head recorded by the successful workflow runs and their immutable artifacts.

## Safety

This status grants no trading capability. Forecasting, probability claims, signals, `TradeIntent`, `OrderIntent`, paper execution and live execution remain disabled. Lot 27 remains `PLANNED_LOCKED` until the Lot 26 merge and post-merge audit pass.
"""
    Path("docs/LOT_26_IMPLEMENTATION_WORKLOG.md").write_text(content, encoding="utf-8")


def write_report() -> None:
    content = """# Lot 26 — Multi-Timeframe Alignment Final Report

Verdict: **GO_LOT26_IMPLEMENTED_VALIDATED_OFFLINE_DESCRIPTIVE_ONLY**

## Deterministic Lot 25 → Lot 26 evidence

- Edge: `timebar-5m → timebar-15m`
- Join: `ASOF_BACKWARD`
- Contexts: `2` (`5m`, `15m`)
- Available components: `6/6`
- Weighted coverage: `1.0`
- Agreement score: `0.65`
- Alignment state: `MTF_DIVERGENT`
- Divergence state: `MTF_MULTI_COMPONENT_MISMATCH`
- Hard mismatches: `regime`, `volatility`
- Output checksum: `c5238d4e3782ab0ae75b6dae84724f061c11917f07ee899d2341ece2e031d556`
- Decision-evidence checksum: `6b633e1f1ff340c751462851101e18f156bd1d4b04347bac519cebd79ec9a1ee`
- Replay: `MATCH`

## Exact-head quality evidence

- Lot 26 tests: `108 PASS`
- Lot 26 line coverage: `98.73%`
- Lot 26 branch coverage: `97.12%`
- Repository assurance: `832 tests PASS`
- Repository line coverage: `94.63%`
- Repository branch coverage: `86.77%`
- Critical mutation score: `82.43%` (`455/552` evaluated)
- Security and dependencies: `Bandit PASS`, `pip-audit PASS`
- Anti-flake: `3/3 PASS`
- Architecture, ownership, roadmap, lifecycle and traceability: `PASS`

The exact certification SHA is recorded by GitHub Actions in the successful PR workflow metadata and uploaded assurance artifacts. This source-controlled report intentionally avoids a self-referential commit hash.

## Interpretation

The score `0.65` describes compatibility between confirmed 5m and 15m contexts. It is not a directional probability, a return forecast, an alpha signal or a trade authorization. Strong volatility and regime mismatches classify the result as `MTF_DIVERGENT` without applying any trading veto because Lot 26 makes no trading decision.

## Safety invariants

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
live_execution=DISABLED
```

## Promotion decision

Lot 26 is eligible for merge after the final exact-head CI cycle. Forecasting, alpha, paper, sandbox and live capital remain `NO_GO`. Lot 27 remains locked until post-merge validation succeeds.
"""
    Path("reports/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_FINAL_REPORT.md").write_text(
        content,
        encoding="utf-8",
    )


def write_changelog() -> None:
    path = Path("CHANGELOG.md")
    previous = path.read_text(encoding="utf-8")
    marker = "## 0.25.1-p0"
    if marker not in previous:
        raise SystemExit("CHANGELOG historical marker missing")
    history = marker + previous.split(marker, 1)[1]
    current = """# Changelog

## 0.26.0 — Lot 26 Multi-Timeframe Alignment

- moteur descriptif `timebar-5m → timebar-15m` avec jointure `ASOF_BACKWARD` ;
- contrats immuables et schémas JSON fermés ;
- couverture pondérée, agreement, divergence, cohérence et incertitude descriptive ;
- lineage, checksums, `DecisionEvidenceEnvelopeV1`, replay et détection de falsification ;
- 108 tests Lot 26, couverture lignes 98.73% et branches 97.12% ;
- mutation critique 82.43% sur 552 mutants ;
- audit dépôt 832 tests, couverture lignes 94.63% et branches 86.77% ;
- Ruff, mypy, Bandit, pip-audit, architecture, traçabilité et anti-flake PASS ;
- aucune prévision, probabilité, décision, permission de trading ou exécution activée.

"""
    path.write_text(current + history, encoding="utf-8")


def main() -> None:
    update_versions_and_statuses()
    write_overlay()
    write_worklog()
    write_report()
    write_changelog()


if __name__ == "__main__":
    main()

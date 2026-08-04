# Crypto Quant Bot V3.1-Ops

Plateforme quantitative crypto défensive, déterministe et auditable.

## État courant

| Élément | État |
|---|---|
| Dernier lot implémenté et validé | **Lot 25 — Volatility / Regime / Confluence** |
| Baseline qualité | **P0 institutionnel fusionné** |
| Prochaine implémentation autorisée | **Lot 26 — Multi-Timeframe Alignment**, encore verrouillé |
| Runtime maximal | `LOCAL_OFFLINE_ANALYSIS_ONLY` |
| Trading | **désactivé** |
| Connectivité exchange | **désactivée** |

Invariants permanents :

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
execution_allowed = false
approved_size = 0
live_execution = DISABLED
leverage = FORBIDDEN
withdrawals = FORBIDDEN
```

## Flux continu et états 5m / 15m

L’ingestion peut être continue, mais un état analytique n’est publié qu’à partir de données
temporellement disponibles et de barres fermées.

```text
flux continu
→ matérialisation de barres fermées 5m et 15m
→ état local 5m à chaque nouvelle barre 5m fermée
→ dernier état 15m fermé disponible
→ jointure as-of backward : available_at <= decision_time
→ contexte multi-timeframe descriptif
```

Le 15m apporte un contexte supérieur. Il ne bloque jamais automatiquement une structure 5m.
Une divergence 5m/15m est un résultat descriptif à expliquer, pas une permission ou une interdiction
de trader.

La théorie des jeux, les zones probables de stops, les sweeps de liquidité, l’absorption et les
comportements de participants restent la responsabilité de **V4 — Microstructure / Liquidity /
Game Theory, Lots 37–52**. Ils ne sont pas implémentés dans le Lot 26.

## Environnement canonique

```text
Python 3.11.9
timezone UTC
locale indépendante
seed/config/horloge injectées
```

Installation de la toolchain verrouillée :

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.lock
```

## Validation

```bash
python scripts/validate_pre_lot26_readiness.py
python scripts/validate_roadmap_documentation.py
python scripts/validate_architecture_boundaries.py
python scripts/check_no_silent_numeric_coercion.py
pytest -q
```

La CI complète ajoute Ruff, mypy, coverage lignes/branches, diff coverage, Bandit,
`pip-audit`, inventaire de complexité et mutation testing.

## Sources de vérité

- [Roadmap V1 → V21](docs/ROADMAP_V1_TO_V21.md)
- [Gate d’entrée pré-Lot26](docs/PRE_LOT26_ENTRY_GATE.md)
- [Spécification Lot 26](docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md)
- [Critères d’acceptation Lot 26](docs/ACCEPTANCE_CRITERIA_LOT_26.md)
- [Spécification mathématique Lot 26](docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md)
- [Sémantique temporelle et jointure as-of](docs/adr/ADR_0001_TIME_SEMANTICS_AND_ASOF_JOIN.md)
- [Contrats temporels Lot 26](docs/contracts/LOT26_TEMPORAL_CONTRACTS.md)
- [Rapport P0](reports/P0_INSTITUTIONAL_HARDENING_REPORT.md)
- [Rapport de readiness pré-Lot26](reports/PRE_LOT26_ENTRY_GATE_REPORT.md)

## Contribution

Toute modification suit [CONTRIBUTING.md](CONTRIBUTING.md), les standards de développement,
les gates de tests et le template de PR. Aucun lot suivant ne commence sans rapport `GO` sur le
commit exact.

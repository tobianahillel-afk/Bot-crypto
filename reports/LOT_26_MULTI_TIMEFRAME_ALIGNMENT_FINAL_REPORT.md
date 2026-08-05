# Lot 26 — Multi-Timeframe Alignment Final Report

Verdict d'implémentation : **IMPLEMENTED_OFFLINE_DESCRIPTIVE_ONLY**

## Preuve déterministe

- Source commit : `8ad774038b6dcc974b37291f5fc3239a095b4252`
- Alignment ID : `0d87a551-16fb-56e4-aaa9-4ff3245b4839`
- Edge : `timebar-5m → timebar-15m`
- Jointure : `ASOF_BACKWARD`
- Contextes : `2` (`5m`, `15m`)
- Composantes disponibles : `6/6`
- Couverture pondérée : `1.0`
- Agreement score : `0.65`
- Alignment state : `MTF_DIVERGENT`
- Divergence state : `MTF_MULTI_COMPONENT_MISMATCH`
- Hard mismatches : `regime`, `volatility`
- Output checksum : `c5238d4e3782ab0ae75b6dae84724f061c11917f07ee899d2341ece2e031d556`
- Decision-evidence checksum : `6b633e1f1ff340c751462851101e18f156bd1d4b04347bac519cebd79ec9a1ee`
- Replay : `MATCH`

## Interprétation

Le score `0.65` décrit la compatibilité des contextes 5m et 15m. Il ne constitue ni une
probabilité directionnelle, ni une prévision de rendement, ni un signal. Les contextes de
volatilité et de régime sont en incompatibilité forte, ce qui classe le résultat en
`MTF_DIVERGENT` sans veto de trading, car le Lot 26 ne prend aucune décision de trading.

## Sécurité

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

## Validation

Le noyau, les contrats, les oracles mathématiques, la causalité temporelle, l'intégration
Lot 25 → Lot 26, les écritures atomiques, le replay et la détection de falsification sont
couverts par les suites `tests/test_lot26_*.py`.

La promotion paper/live, toute prédiction, tout `TradeIntent` et tout `OrderIntent` restent
`NO_GO`.

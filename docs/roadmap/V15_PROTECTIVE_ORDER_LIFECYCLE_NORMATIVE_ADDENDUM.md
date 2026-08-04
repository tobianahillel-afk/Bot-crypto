# V15 Normative Addendum — Protective Orders and Exit Lifecycle

Ce document complète V15 Lots 133–141.

## Objective

Transformer un `OrderIntentV1` risk-approved et un `ProtectiveOrderPlanV1` en lifecycle durable, idempotent et réconciliable. V15 ne choisit pas la stratégie de sortie ; il exécute le plan approuvé.

## Required capabilities

- bracket order lifecycle ;
- OCO natif ou émulation explicitement autorisée ;
- stop-loss ;
- un ou plusieurs take-profits ;
- break-even économique incluant frais/funding/slippage ;
- trailing stop ;
- partial exits ;
- activation proportionnelle aux partial fills ;
- reduce-only ;
- cancel/replace ;
- expiry ;
- restart/recovery ;
- reconciliation venue/ledger/position.

## Lot mapping

### Lot 133

Ajoute `ProtectiveOrderPlanV1`, `ExitPolicyV1` references, OCO/bracket groups et invariants de protection.

### Lot 134

La state machine inclut les transitions des ordres parents/enfants et états de protection/reconciliation.

### Lot 135

Les IDs et idempotency keys couvrent plans et branches protectrices.

### Lots 136–138

Validation instrument/venue, submission/ack, cancel/replace et partial fills conservent les quantités exactes protégées.

### Lots 139–140

Recovery et reconciliation reconstruisent :

```text
position_qty
protected_qty
remaining_unprotected_qty
active_stop_qty
active_take_profit_qty
```

Toute divergence bloque les nouvelles entrées.

### Lot 141

Closure V15 inclut fault injection, crash recovery, OCO race, duplicate events, timeout et replay.

## Non-negotiable invariants

- aucune quantité protectrice supérieure à la position réconciliée ;
- aucune fenêtre silencieuse non protégée après partial fill ;
- aucune augmentation du risque sans nouvelle RiskDecision ;
- aucun retry aveugle sur résultat UNKNOWN ;
- tout fill d'une branche met à jour/annule les branches liées ;
- tout événement est idempotent ;
- restart reconstruit l'état depuis le ledger et la venue autorisée.

## Tests

- parent unfilled ;
- partial fills successifs ;
- stop/TP concurrency ;
- OCO natif/émulé ;
- duplicate ack/fill/cancel ;
- crash entre persist et submit ;
- timeout après submit ;
- gap au-delà du stop ;
- trailing monotone ;
- break-even net de coûts ;
- multiple take-profits ;
- reconciliation mismatch ;
- replay déterministe.

## Scope restriction

Aucun de ces mécanismes n'est implémenté dans la préparation ou le Lot 26.

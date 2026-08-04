# Runtime Modes and State Machines

## Runtime modes

```text
OFFLINE_RESEARCH
BACKTEST
PAPER
READ_ONLY
SHADOW_LIVE
SANDBOX
LIVE_DISABLED
LIVE_MANUAL_APPROVAL
LIVE_SMALL_CAPITAL
LIVE_REDUCED_RISK
LIVE_PAUSED
EMERGENCY_STOP
```

Default au démarrage : `LIVE_DISABLED`. Un mode non reconnu est équivalent à `EMERGENCY_STOP` pour l’exécution.

## Transitions de runtime autorisées

- OFFLINE_RESEARCH ↔ BACKTEST.
- BACKTEST → PAPER uniquement via backtest promotion gate.
- PAPER → SANDBOX via paper promotion gate.
- READ_ONLY et SHADOW_LIVE ne soumettent jamais d’ordre.
- SANDBOX → LIVE_MANUAL_APPROVAL uniquement via sandbox gate + human approval.
- LIVE_MANUAL_APPROVAL → LIVE_SMALL_CAPITAL uniquement via capital-tier approval.
- Tout mode → LIVE_PAUSED ou EMERGENCY_STOP.
- EMERGENCY_STOP → LIVE_DISABLED seulement après reconciliation + incident closure + approbation humaine.

## Strategy lifecycle

```text
DRAFT → CANDIDATE → BACKTEST_APPROVED → PAPER_ENABLED
→ SANDBOX_ENABLED → LIVE_ELIGIBLE → LIVE_MANUAL_APPROVAL
→ LIVE_SMALL_CAPITAL
```

Transitions latérales/terminales : `REVIEW_REQUIRED`, `DE_RISKED`, `PAUSED`, `RETIRED`. Aucune réactivation automatique.

## Order state machine

```text
RECEIVED → VALIDATED → PENDING_SUBMIT → SUBMITTED → ACKNOWLEDGED
ACKNOWLEDGED → PARTIALLY_FILLED → FILLED
ACKNOWLEDGED/PARTIALLY_FILLED → CANCEL_PENDING → CANCELED
ACKNOWLEDGED/PARTIALLY_FILLED → REPLACE_PENDING → CANCELED + NEW_ORDER
ANY_ACTIVE → EXPIRED / REJECTED / UNKNOWN / RECONCILIATION_REQUIRED
```

`UNKNOWN` et `RECONCILIATION_REQUIRED` gèlent toute nouvelle exposition liée jusqu’à résolution.

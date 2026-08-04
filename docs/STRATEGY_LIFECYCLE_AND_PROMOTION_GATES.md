# Strategy Lifecycle and Promotion Gates

## Research → Candidate

Requis : hypothèse pré-enregistrée, mécanisme, null hypothesis, features permises, régime/horizon, falsification, data availability et coûts attendus.

## Candidate → Backtest

Requis : contrat immuable, aucune feature future, labels séparés, baselines, plan OOS, paramètres recherchés vs gelés, minimum sample policy.

## Backtest → Paper

Requis : EV net/stressée, walk-forward/OOS, purged CV/embargo si nécessaire, placebo/multiple-testing, stabilité paramètres, capacité, drawdown et model card.

## Paper → Sandbox

Requis : période minimale configurable, nombre suffisant de décisions/trades/no-trades, reconciliation clean, coût réalisé vs attendu, absence d’incident critique non résolu, drift acceptable.

## Sandbox → Live eligible

Requis : OMS/EMS idempotent, failure matrix, crash recovery, exchange constraints, security/permissions, DR, operator runbooks, release/rollback et revue humaine.

## Live small capital → Scale-up

Aucun scale-up automatique. Chaque tier exige nouvelle preuve, limites, approbation, expiry et rollback. Les échecs entraînent de-risk/pause/retirement.

## PromotionDecisionV1

Chaque critère est PASS/FAIL/NOT_APPLICABLE avec evidence IDs. Une preuve absente vaut FAIL. Les seuils sont dans une config versionnée et non dans cette documentation.

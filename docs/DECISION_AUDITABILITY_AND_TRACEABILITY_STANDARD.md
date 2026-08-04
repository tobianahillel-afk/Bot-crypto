# Decision Auditability and Traceability Standard

Toute décision, absence de décision, veto, transition, ordre simulé ou ordre futur de **Crypto Quant Bot V3.1-Ops** doit être reconstruisible sans dépendre de la mémoire d'un opérateur ni d'un log textuel incomplet.

## 1. Principe de reconstruction

À partir d'un `decision_id`, un auditeur doit pouvoir retrouver :

- les données exactes disponibles ;
- leur provenance et qualité ;
- les features et formules ;
- les scénarios concurrents ;
- la stratégie et sa version ;
- les modèles, paramètres et calibration ;
- les règles et limites de risque ;
- la configuration et le commit ;
- les décisions intermédiaires ;
- les reason codes et vetos ;
- l'action finale ;
- les événements ultérieurs et la réconciliation.

## 2. Decision Evidence Envelope

Chaque décision persistée contient au minimum :

```text
decision_id
parent_decision_ids
run_id
correlation_id
replay_id
event_time
decision_time
generated_at
runtime_mode
instrument_id
venue_id
data_snapshot_id
data_quality_state_id
feature_set_id
market_context_id
scenario_set_id
strategy_id
strategy_version
model_versions
calibration_version
risk_state_id
risk_decision_id
config_version
code_commit
input_checksums
output_checksum
decision_state
reason_codes
veto_codes
uncertainty
human_approval_id
```

Les champs non applicables sont explicitement `null` avec une raison ; ils ne sont jamais omis silencieusement.

## 3. Provenance et lineage

Chaque artefact doit former un DAG de dépendances vérifiable. Les arêtes portent :

- type de transformation ;
- version du transformateur ;
- timestamp de disponibilité ;
- checksum entrée/sortie ;
- règles de filtrage ;
- pertes ou agrégations ;
- qualité et corrections appliquées.

Aucun artefact dérivé sans parent connu n'est consommable.

## 4. Journal append-only

Les événements critiques sont écrits dans un journal append-only :

- décisions ;
- vetos ;
- approvals ;
- transitions runtime ;
- order lifecycle ;
- fills ;
- ledger ;
- reconciliation ;
- incidents ;
- changements de configuration.

Toute correction est un nouvel événement ; aucun historique n'est réécrit.

## 5. Explainability structurée

Une explication doit séparer :

```text
facts_observed
features_computed
inferences
assumptions
supporting_evidence
contradicting_evidence
uncertainty
rules_triggered
vetos_triggered
final_consequence
```

Un texte LLM éventuel n'est qu'une vue dérivée et ne remplace jamais l'explication structurée.

## 6. Audit de l'absence de trade

`WAIT` ou `BLOCK_TRADING` est une décision complète. Elle doit indiquer :

- condition non satisfaite ;
- seuil et valeur observée ;
- owner du veto ;
- durée/expiry ;
- condition nécessaire pour reconsidération ;
- preuve qu'aucun OrderIntent n'a été créé.

## 7. Audit ordre et exécution

Pour chaque ordre :

- lien vers Signal, TradeIntent, RiskDecision et HumanApproval ;
- hash exact approuvé ;
- client_order_id et idempotency key ;
- transitions OMS ;
- request/ack/reject/fill/cancel/replace ;
- timestamps source/receive/process ;
- coûts attendus et réalisés ;
- slippage et TCA ;
- position, cash et PnL avant/après ;
- résultat de reconciliation.

## 8. Intégrité

- checksums sur artefacts ;
- manifests de run ;
- horodatage UTC ;
- ordre causal explicite ;
- détection des trous et duplications ;
- signatures ou mécanisme d'intégrité pour approvals et journaux critiques ;
- politique de rétention et export audit.

## 9. Replay d'audit

Un replay d'audit doit pouvoir :

1. charger manifest, code, config, modèles et données ;
2. reconstruire l'ordre événementiel ;
3. recalculer chaque étape ;
4. comparer checksums et décisions ;
5. produire le premier point de divergence ;
6. conclure `REPLAY_MATCH`, `REPLAY_DIVERGENCE` ou `REPLAY_IMPOSSIBLE`.

`REPLAY_DIVERGENCE` ou `REPLAY_IMPOSSIBLE` bloque la promotion.

## 10. Matrice de traçabilité

Chaque lot maintient :

```text
requirement_id -> design_section -> implementation_symbol -> test_ids -> evidence_artifacts -> audit_result
```

Aucune exigence sans test ou justification formelle ; aucun test sans exigence ; aucun fichier critique sans owner.

## 11. Audit queries minimales

Le système doit permettre de répondre de manière déterministe à :

- pourquoi cette décision ?
- pourquoi pas de trade ?
- quelles données étaient réellement disponibles ?
- quelle formule et quels paramètres ?
- quel changement de code/config a modifié le résultat ?
- quel veto a dominé ?
- l'approval correspondait-elle au hash exact ?
- l'ordre a-t-il été dupliqué ?
- le ledger est-il réconcilié ?
- le replay est-il identique ?

Tout lot ne permettant pas ces reconstructions reçoit `NO_GO_AUDITABILITY`.
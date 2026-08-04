# Protective Orders and Exit Lifecycle Standard

Statut : `PLANNED_LOCKED_STANDARD`  
Applicabilité future : V5 stratégie, V7 risque, V8 paper, V15 OMS/EMS, V16+ exécution gouvernée.

## 1. Objectif

Définir comment une hypothèse de sortie devient une politique de protection, puis des intents et ordres réconciliables. Ce document ne crée aucun ordre et ne modifie aucune permission d'exécution.

## 2. Séparation des responsabilités

| Domaine | Responsabilité |
|---|---|
| V5 Strategy Research | logique d'entrée, sortie, invalidation et horizon |
| V6 Backtest/TCA | réalisme des exits, coûts, fills, MAE/MFE et robustesse |
| V7 Risk | risque maximal, stop obligatoire, sizing, limites et veto |
| V8 Paper | simulation des ordres de protection et incidents |
| V15 OMS/EMS | état durable, idempotence, OCO/bracket, cancel/replace, fills |
| V17 Live Governance | approbation humaine et permissions live |

Le modèle prédictif ne soumet jamais directement un ordre protecteur.

## 3. `ExitPolicyV1`

Une stratégie candidate doit déclarer :

```text
exit_policy_id
strategy_id + version
entry_reference
invalidation_logic
initial_stop_policy
take_profit_policy
break_even_policy
trailing_policy
partial_exit_policy
maximum_holding_horizon
time_exit_policy
regime_exit_policy
emergency_exit_policy
forbidden_order_behaviors
```

Toute politique est versionnée et immuable pendant une position, sauf transition explicitement autorisée.

## 4. Types de protection

### 4.1 Stop-loss

- niveau structurel ;
- volatilité ajustée ;
- liquidité ajustée ;
- perte monétaire maximale ;
- horizon et régime ;
- condition d'invalidation.

Le stop ne peut pas augmenter le risque au-delà du budget approuvé.

### 4.2 Take-profit

- target unique ;
- targets multiples ;
- réduction partielle ;
- sortie sur liquidité ;
- sortie sur rendement marginal net négatif ;
- sortie temporelle.

### 4.3 Break-even

Le déplacement au break-even doit inclure :

```text
entry_average_price
fees
funding
slippage
minimum_profit_buffer
activation_condition
```

Un prix d'entrée brut n'est pas nécessairement un break-even économique.

### 4.4 Trailing stop

Toute règle précise :

- référence de suivi ;
- distance ou modèle ;
- fréquence de mise à jour ;
- direction monotone autorisée ;
- comportement lors d'un gap ;
- politique d'arrondi instrument ;
- invalidation lors d'un état inconnu.

### 4.5 Time/regime exit

Une position peut expirer même sans target ou stop touché. Les changements de régime, la péremption du signal, la dérive du modèle ou la dégradation des données peuvent produire un exit intent selon une politique approuvée.

## 5. `ProtectiveOrderPlanV1`

Après RiskDecision APPROVE, un plan peut contenir :

```text
plan_id
position_or_entry_intent_id
risk_decision_id
stop_order_intent
take_profit_order_intents
oco_group_id
bracket_group_id
activation_rules
quantity_allocation
reduce_only_policy
replacement_policy
expiry_policy
reconciliation_policy
```

Le plan est une intention gouvernée, pas un ordre soumis.

## 6. Bracket et OCO

Règles obligatoires :

- l'ordre protecteur ne devient actif qu'après quantité exécutée correspondante ;
- les quantités protectrices ne dépassent jamais la position réconciliée ;
- un fill d'une branche réduit ou annule les branches liées ;
- les événements dupliqués sont idempotents ;
- un état `UNKNOWN` déclenche réconciliation avant nouvelle soumission ;
- l'émulation locale d'un OCO doit être explicitement autorisée et testée ;
- aucune fenêtre sans protection silencieuse après un partial fill.

## 7. Partial fills et sorties partielles

Après chaque fill :

```text
position_qty
protected_qty
remaining_unprotected_qty
active_stop_qty
active_take_profit_qty
```

sont réconciliés. Une divergence produit `PAUSE` ou `KILL_SWITCH` selon la sévérité.

## 8. Cancel/replace

Toute modification :

1. valide une nouvelle politique et son hash ;
2. vérifie que le risque ne croît pas sans nouvelle approbation ;
3. crée une transition OMS durable ;
4. attend ack/reconciliation ;
5. interdit le retry aveugle ;
6. conserve la causalité et l'ancien ordre.

## 9. Redémarrage et récupération

Après crash :

- reconstruire position et ordres depuis le ledger ;
- interroger l'état venue lorsque le mode l'autorise ;
- comparer toutes les quantités ;
- restaurer ou recréer une protection seulement via politique idempotente ;
- ne pas supposer qu'un cancel/submit a échoué ;
- bloquer les nouvelles entrées jusqu'à réconciliation.

## 10. Tests obligatoires

- entry non fillée → aucune protection de quantité inexistante ;
- partial fill → protection proportionnelle ;
- fill simultané stop/target simulé selon règles venue ;
- duplicate fill/ack/cancel idempotent ;
- crash entre persist et submit ;
- timeout après submit ;
- OCO natif et émulé ;
- déplacement break-even incluant les coûts ;
- trailing stop monotone ;
- réduction partielle et quantités exactes ;
- gap au-delà du stop ;
- état venue inconnu ;
- replay déterministe ;
- aucune permission live implicite.

## 11. Auditabilité

Chaque transition référence :

```text
strategy_version
exit_policy_id
protective_plan_id
risk_decision_id
order_intent_ids
position_state_id
previous_order_state
new_order_state
causal_event_id
config_version
code_commit
reconciliation_evidence
```

## 12. Restrictions pré-Lot26

Aucun `ExitPolicyV1`, `ProtectiveOrderPlanV1`, bracket, OCO, stop, take-profit ou trailing order n'est implémenté dans le Lot 26. La roadmap est seulement rendue suffisamment précise pour les lots futurs.

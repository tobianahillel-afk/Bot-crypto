# Model Retraining and Promotion Policy

Statut : `P0_6_NORMATIVE`  
Applicabilité : tout modèle statistique, probabiliste, ML ou adaptatif des versions V4–V21.

## 1. Principe

Aucun modèle contrôlant une feature, une prévision, un signal, un sizing, un veto ou une décision ne peut modifier silencieusement son comportement en production. L'apprentissage autonome directement dans un runtime paper, sandbox ou live est interdit.

```text
online_self_modification = FORBIDDEN
unreviewed_model_promotion = FORBIDDEN
autonomous_scale_up = FORBIDDEN
```

Le réentraînement est un processus offline, reproductible, versionné et séparé de l'inférence.

## 2. Contrats obligatoires

Chaque entraînement produit :

```text
TrainingRunV1
ModelArtifactV1
ModelCardV1
CalibrationArtifactV1
TrainingDataManifestV1
EvaluationEvidenceV1
ModelPromotionDecisionV1
```

Chaque artefact référence dataset, feature set, labels, split policy, code commit, environment, seed, hyperparamètres, dépendances, checksums et owner.

## 3. Déclencheurs de réentraînement

Un réentraînement peut être proposé après :

- arrivée d'une fenêtre de données approuvée ;
- dérive de données, features, calibration, performance ou coûts ;
- changement de régime documenté ;
- évolution de contrat ou de feature set ;
- calendrier de maintenance versionné ;
- correction d'un défaut démontré.

Un déclencheur ne constitue jamais une autorisation de promotion.

## 4. Séparation des données

Les données d'entraînement, calibration, validation, test final et shadow evaluation sont temporellement séparées. Les règles suivantes sont obligatoires :

- `available_at <= decision_time` pour chaque feature ;
- labels construits uniquement offline ;
- purged split et embargo lorsque les horizons se chevauchent ;
- normalisation ajustée uniquement sur le train ;
- aucun résultat du test final utilisé pour choisir les hyperparamètres ;
- conservation des essais négatifs et abandonnés.

## 5. Champion / challenger

Le modèle actif est le `champion`. Tout nouveau modèle commence comme `challenger`.

Séquence minimale :

```text
TRAINED
→ OFFLINE_VALIDATED
→ CALIBRATED
→ SHADOW_APPROVED
→ PAPER_APPROVED
→ SANDBOX_APPROVED
→ HUMAN_PROMOTION_APPROVED
→ ELIGIBLE_FOR_RUNTIME_MODE
```

Aucune étape ne peut être sautée. Une promotion est liée au hash exact du modèle, de la configuration, du code, des features et des données d'évaluation.

## 6. Critères de promotion

Le challenger doit démontrer, par rapport au champion et aux baselines simples :

- amélioration statistique hors échantillon ;
- calibration suffisante pour tout champ probabiliste ;
- PnL net de coûts supérieur selon l'objectif économique approuvé ;
- absence de dégradation majeure sur les régimes critiques ;
- stabilité aux paramètres et aux perturbations ;
- capacité et liquidité compatibles ;
- drawdown, expected shortfall et risque de ruine dans les limites ;
- reproductibilité exacte ou déterminisme conditionnel à la seed ;
- aucune régression sécurité, auditabilité ou latence.

L'amélioration moyenne seule est insuffisante.

## 7. Shadow, paper et sandbox

Le shadow compare les décisions du challenger sans action exécutable. Le paper vérifie la chaîne décisionnelle et les coûts simulés. Le sandbox vérifie les contrats d'exécution, incidents et réconciliation.

Les résultats doivent conserver les divergences champion/challenger, les conditions de marché, les reason codes et les conséquences économiques.

## 8. Dérive et expiration

Chaque modèle définit :

```text
monitoring_metrics
drift_thresholds
calibration_expiry
maximum_data_age
review_frequency
pause_conditions
retirement_conditions
rollback_target
```

Une dérive peut réduire le risque, bloquer ou retirer un modèle. Elle ne peut jamais augmenter automatiquement son exposition.

## 9. Continual learning

Le continual learning est autorisé uniquement comme expérience offline. Il doit tester :

- catastrophic forgetting ;
- contamination des fenêtres ;
- biais de sélection issu des propres décisions du système ;
- stabilité des anciennes capacités ;
- sensibilité à l'ordre des observations ;
- rollback vers un checkpoint immuable.

Aucun poids mis à jour en continu n'est consommable par un runtime autorisé sans nouvelle promotion complète.

## 10. Rollback et retrait

Le rollback doit être atomique, auditable et testé. Le modèle retiré reste conservé avec ses preuves. Une restauration ne réactive pas automatiquement une permission live expirée.

## 11. Tests obligatoires

- unitaires et contractuels ;
- oracles indépendants lorsque possible ;
- property-based ;
- anti-lookahead ;
- calibration ;
- walk-forward et OOS ;
- placebo et randomisation ;
- stress de régime ;
- mutation des règles critiques ;
- replay ;
- champion/challenger ;
- rollback ;
- non-régression des modèles précédents.

## 12. Gate

`GO_MODEL_PROMOTION` exige zéro BLOCKER/MAJOR, toutes les preuves signées, CI verte sur le commit exact et approbation humaine. Sinon :

```text
NO_GO_MODEL_PROMOTION
```

# Institutional Hedge Fund Audit — Crypto Quant Bot V3.1-Ops

Date d’audit : 2026-08-04  
Périmètre : code et preuves disponibles jusqu’au Lot 25, roadmap canonique V1→V21 / Lots 0→177  
Position actuelle : Lot 25 validé ; Lot 26 non commencé  
Verdict global : **NO_GO pour capital réel ; CONDITIONAL_GO pour poursuivre la recherche offline**

## 1. Opinion exécutive

Le projet est une fondation de recherche défensive, auditable et volontairement non exécutable. Sa gouvernance documentaire est désormais très supérieure à celle d’un bot retail ordinaire. En revanche, il ne constitue pas encore un système d’investissement, un moteur d’alpha prouvé, une plateforme de portefeuille, ni une infrastructure d’exécution institutionnelle.

La distinction essentielle est :

```text
software correctness ≠ mathematical validity ≠ statistical evidence
statistical evidence ≠ economic edge ≠ executable alpha
executable alpha ≠ scalable portfolio ≠ production readiness
```

Les Lots 22–25 démontrent surtout :

- une chaîne locale déterministe ;
- des artefacts auditables et checksumés ;
- des indicateurs et états descriptifs ;
- le maintien des invariants no-trading.

Ils ne démontrent pas encore :

- une espérance nette positive ;
- une calibration probabiliste ;
- une robustesse hors échantillon ;
- une capacité après frais, impact et liquidité ;
- une gestion de portefeuille ;
- une exécution réaliste ;
- une sécurité opérationnelle live.

## 2. Tableau de notation institutionnelle

Échelle : 0 = absent ; 5 = niveau institutionnel démontré.

| Domaine | Note actuelle | Opinion |
|---|---:|---|
| Gouvernance documentaire | 4.0/5 | Structure forte, responsabilités et gates bien définis. |
| Sécurité no-trading | 4.5/5 | Fail-closed, archive figée et absence de chemin live : très bon pour le stade actuel. |
| Reproductibilité locale | 3.5/5 | Checksums et replay présents, mais pas encore de reproductibilité multi-environnement démontrée. |
| Qualité logicielle démontrée | 2.0/5 | Tests historiques importants, mais aucun pipeline général visible imposant lint, typing et coverage. |
| Qualité des données | 1.5/5 | Fixtures locales utiles ; absence actuelle de data lineage institutionnel multi-source et de reconciliation de marché. |
| Rigueur mathématique implémentée | 1.5/5 | Formules simples et bornées ; nombreux seuils heuristiques non estimés ou calibrés. |
| Recherche d’alpha | 0.5/5 | Aucun alpha ou mécanisme économique falsifiable actuellement démontré. |
| Validation statistique | 0.5/5 | Pas encore d’OOS, walk-forward, purged CV, multiple-testing control ou power analysis implémentés. |
| TCA / capacité | 1.0/5 | Fondation de coûts au Lot 10, mais pas de calibration venue/taille/queue/impact suffisante. |
| Risque de stratégie | 1.0/5 | Blocage défensif fort ; absence de modèle actif de sizing, drawdown, factor/correlation et risk budget. |
| Portfolio / PnL | 0.5/5 | Prévu, non implémenté. |
| OMS / EMS / réconciliation | 0.5/5 | Prévu, non implémenté. |
| Observabilité / incidents | 1.0/5 | Gouvernance prévue, infrastructure production non démontrée. |
| Readiness paper trading | 1.0/5 | Trop tôt : alpha, TCA et modèle de fill non validés. |
| Readiness capital réel | 0.0/5 | Interdit et non prêt, conformément aux invariants. |

## 3. Audit du code actuellement implémenté

### 3.1 Forces

1. **Déterminisme et checksums** : les résultats excluent les champs runtime du hash et produisent des empreintes stables.
2. **Validation défensive** : les dépendances, archives et artefacts amont sont contrôlés avant calcul.
3. **Séparation descriptive/exécutable** : les moteurs actuels n’émettent pas d’ordre.
4. **Contrats de modèles** : les états sont fermés par des modèles et des ensembles autorisés.
5. **Bibliothèque standard** : faible surface de dépendances et reproductibilité initiale simple.

### 3.2 Défauts de conception quantitatifs

#### A. Seuils constants non calibrés

Exemples observés dans les moteurs actuels :

```text
slope_percent >= 0.15
close_change_percent >= 0.25
range_width_percent <= 1.4
ATR percent >= 0.8
expansion_score >= 0.70
compression_score >= 0.68
```

Ces seuils sont déterministes, mais leur justification économique/statistique n’est pas démontrée. Ils doivent devenir :

- paramètres versionnés ;
- estimés exclusivement sur train ;
- évalués par sensibilité ;
- robustes par régime et venue ;
- assortis d’intervalles d’incertitude ;
- invalidés s’ils ne survivent pas OOS.

#### B. Agrégations par moyenne simple

Plusieurs scores utilisent la moyenne arithmétique de composantes normalisées arbitrairement. Une moyenne simple suppose implicitement :

- comparabilité des composantes ;
- poids égaux ;
- indépendance ou absence de double comptage ;
- linéarité de l’effet ;
- bonne calibration de chaque composante.

Ces hypothèses ne sont pas démontrées. Chaque agrégateur devra comparer au minimum :

- baseline égale ;
- pondération régularisée ;
- modèle monotone ;
- calibration isotonic/Platt si sortie probabiliste ;
- ablation de chaque composante ;
- contrôle de colinéarité et information redondante.

#### C. Fenêtres très courtes et indicateurs non standards

Les fenêtres 3/5/6 sont utiles pour fixtures, mais insuffisantes pour inférer un comportement de marché stable. Le MACD 3/6/3 et le RSI 5 ne sont pas des erreurs, mais ils ne doivent pas être présentés comme preuves d’alpha sans recherche dédiée.

#### D. Initialisation EMA simplifiée

L’EMA est initialisée avec le premier point, ce qui crée un effet de warm-up. Le système doit :

- documenter la convention ;
- imposer un warm-up minimal ;
- comparer à une référence indépendante ;
- tester l’impact de l’initialisation ;
- ne jamais consommer une valeur avant maturité.

#### E. Gestion permissive des valeurs invalides

La conversion `_as_float` transforme certaines valeurs non numériques en `0.0`. Pour un système financier, une donnée invalide ne doit généralement pas devenir silencieusement zéro. Elle doit produire `INVALID_DATA`, `UNKNOWN` ou un veto selon le contrat.

#### F. Pas d’incertitude statistique

Les scores actuels sont ponctuels. Il manque :

- erreur standard ;
- intervalle de confiance ou crédibilité ;
- stabilité bootstrap ;
- calibration ;
- probabilité de changement de régime ;
- uncertainty decomposition data/model/regime/execution.

### 3.3 Dette d’ingénierie observée

- `pyproject.toml` conserve une version et une description liées au Lot 10, donc les métadonnées projet sont obsolètes.
- `pytest` désactive explicitement le plugin coverage ; le seuil de 90 % est documenté mais non appliqué par la configuration actuelle.
- Ruff et mypy ont des sections minimales, sans commande CI démontrée.
- Le workflow visible valide uniquement la documentation de roadmap.
- `requirements.txt` reste une déclaration historique du Lot 1 et ne représente pas un environnement de développement/test institutionnel.
- Les modules Market Analysis sont volumineux et mélangent validation amont, calcul, agrégation, persistance et reporting ; ils devront être progressivement séparés selon les frontières de domaine sans réécrire l’historique validé.

## 4. Audit de la roadmap

### 4.1 Ce qui est bien conçu

- progression offline → research → backtest → risk → paper → OMS/EMS → sandbox → live gouverné ;
- séparation Signal / TradeIntent / RiskDecision / OrderIntent ;
- data governance avant microstructure ;
- TCA et model risk avant toute promotion ;
- OMS/EMS avant sandbox ;
- account read-only et exchange health avant live ;
- observabilité, incident response et réconciliation explicitement prévus ;
- HFT maintenu en research-only ;
- options/on-chain traités comme contextes, non comme permissions autonomes.

### 4.2 Ce qui manque ou doit être renforcé

#### A. Investment mandate et univers

Avant l’alpha, le système doit figer :

- objectif de rendement ;
- volatilité cible ;
- drawdown maximal tolérable ;
- horizon ;
- liquidité minimale ;
- univers d’instruments ;
- devises de base ;
- contraintes spot/perp ;
- capacité cible ;
- fréquence de turnover ;
- benchmark et cash benchmark.

#### B. Alpha taxonomy et economic rationale

Chaque stratégie doit être classée :

- momentum/trend ;
- mean reversion ;
- liquidity provision ;
- volatility/risk premium ;
- funding/basis ;
- cross-sectional ;
- event-driven ;
- microstructure/order-flow.

Elle doit expliquer qui paie l’alpha, pourquoi il devrait persister, ce qui le détruit, et quelles contraintes empêchent son arbitrage immédiat.

#### C. Research budget et multiple testing

Le Research OS doit gérer :

- nombre total d’hypothèses ;
- familles d’hypothèses ;
- false discovery rate ;
- Deflated Sharpe Ratio ;
- Probability of Backtest Overfitting ;
- White’s Reality Check ou méthode équivalente ;
- combinatorial purged cross-validation lorsque pertinent ;
- journal des essais abandonnés.

#### D. Data realism

Il faudra ajouter :

- survivorship et symbol mapping ;
- delistings/halted markets ;
- exchange maintenance ;
- timestamp drift ;
- trades annulés/corrigés ;
- order-book sequence gaps ;
- crossed/locked book ;
- fee tiers historiques ;
- funding exact ;
- tick/lot size historiques ;
- timezone/calendar sessions ;
- provenance et licence des données.

#### E. Portfolio construction institutionnelle

La roadmap doit rendre explicites :

- risk budgeting ;
- marginal contribution to risk ;
- factor exposures ;
- concentration et crowding ;
- correlation stressée ;
- liquidity-adjusted exposure ;
- turnover penalty ;
- transaction-cost-aware optimization ;
- drawdown control ;
- tail scenarios ;
- capital allocation entre stratégies ;
- capacity allocation.

#### F. Independent model validation

Le développeur du modèle ne doit pas être l’unique valideur conceptuel. Même en projet individuel, il faut séparer les rôles documentaires :

- Model Owner ;
- Independent Validator ;
- Risk Approver ;
- Release Approver ;
- Operator.

Un même humain peut tenir plusieurs rôles, mais doit produire des preuves séparées et signées.

#### G. Production change management

Avant live :

- canary/shadow ;
- rollback testé ;
- configuration diff ;
- schema migration rehearsal ;
- secret rotation ;
- break-glass ;
- disaster recovery ;
- RTO/RPO ;
- exchange/API outage drills ;
- reconciliation drills ;
- kill-switch drills ;
- operator runbooks.

## 5. Ordre de priorité recommandé

### Priorité P0 — avant Lot 26

1. Ajouter une CI du code complète : compile, tests, coverage, branch coverage, lint, typing et audit documentaire.
2. Corriger les métadonnées `pyproject.toml` sans changer l’identité du projet.
3. Introduire un environnement dev/test versionné.
4. Mesurer la couverture actuelle au lieu de supposer qu’elle atteint 90 %.
5. Créer un inventaire des fonctions/modules avec taille, complexité et duplication.
6. Classer toute conversion de donnée invalide en fail-closed au lieu de zéro silencieux.
7. Créer un template de validation mathématique obligatoire par feature.

### Priorité P1 — Lots 26–30

- terminer l’alignement multi-timeframe ;
- séparer accord, divergence, dominance et uncertainty ;
- éviter qu’une moyenne de scores soit interprétée comme probabilité ;
- produire explications et reason codes ;
- ajouter tests de perturbation et ablation ;
- clôturer V2 comme moteur descriptif, pas comme alpha.

### Priorité P2 — Data Governance et microstructure

- mettre la qualité des données avant toute sophistication de modèle ;
- définir `event_time`, `receive_time`, `available_at`, `usable_from` ;
- reconstruire et réconcilier carnet/trades ;
- évaluer la confiance de l’aggressor classification ;
- séparer observation de liquidité et inférence comportementale.

### Priorité P3 — Alpha et validation

- exiger hypothèse falsifiable et economic rationale ;
- définir label, horizon et purge avant le calcul ;
- baselines naïves ;
- OOS, walk-forward, CPCV/purged CV ;
- multiple-testing control ;
- TCA et capacité avant promotion.

### Priorité P4 — risque, paper et exécution

- RiskDecision indépendante ;
- sizing = 0 par défaut ;
- portfolio accounting exact ;
- fill realism ;
- paper suffisamment long et multi-régime ;
- OMS/EMS/reconciliation avant sandbox ;
- sandbox et fault injection avant toute étude live.

## 6. Gates institutionnels

### Gate pour commencer Lot 26

**CONDITIONAL_GO**, à condition de :

- ne pas présenter les scores existants comme probabilités ou alpha ;
- conserver no-trading ;
- ouvrir un chantier P0 de CI et qualité ;
- documenter les seuils heuristiques comme provisoires ;
- ne pas promouvoir V2 vers paper/backtest de stratégie.

### Gate pour commencer Alpha Research

**NO_GO** tant que ne sont pas opérationnels : data governance, anti-lookahead systématique, research registry, baselines, multiple-testing policy et datasets suffisamment longs.

### Gate pour Paper Trading

**NO_GO** tant qu’aucune stratégie n’a passé OOS + TCA + model risk + capacity + promotion indépendante.

### Gate pour capital réel

**NO_GO**. Le projet ne dispose volontairement ni des preuves d’alpha, ni des systèmes de risque/exécution/ops requis.

## 7. Verdict du gestionnaire

Comme fondation éducative et d’audit : **très prometteur**.  
Comme plateforme de recherche institutionnelle : **architecture crédible, implémentation encore précoce**.  
Comme stratégie d’investissement : **non démontrée**.  
Comme système paper : **non prêt**.  
Comme système live : **interdit et non prêt**.

La meilleure décision n’est pas d’ajouter davantage d’indicateurs. Elle est de transformer chaque prochain lot en expérience falsifiable, statistiquement contrôlée, économiquement justifiée, réconciliable et exploitable uniquement après coûts et risques.

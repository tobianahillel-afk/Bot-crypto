# Crypto Quant Bot V3.1-Ops — Lot 0

Lot 0 crée uniquement la fondation défensive et auditable du projet.

Le projet est un bot / plateforme de trading quant crypto, orienté au départ sur BTC/EUR, sans trading réel au démarrage.

## Principes

- `trade_allowed = false` par défaut.
- Aucun trading réel dans ce lot.
- Aucune clé API réelle.
- Aucun appel Kraken.
- Aucun WebSocket.
- Aucun modèle ML.
- Aucun backtest.
- Aucun paper trading réel.

## Validation rapide

```bash
python scripts/validate_lot0.py
python scripts/run_smoke_test.py
```

Résultat attendu :

```text
LOT 0 VALIDATION: PASS
```

## Lot 1 — Data Platform Foundation

Lot 1 adds the first data foundation without changing the defensive behavior of the bot.

Included:

- raw/bronze/silver/gold/audit data layers;
- local BTC/EUR OHLCVT fixture;
- OHLCVT parser;
- dataset catalog;
- data quality validation;
- dataset and OHLCVT contracts;
- Lot 1 validation script and tests.

Excluded:

- API calls;
- WebSocket;
- strategy;
- backtest;
- paper trading;
- live trading.

Validation:

```bash
python scripts/validate_lot0.py
python scripts/validate_lot1.py
python -m pytest -q
```

## Lot 2 — Multi-timeframes & Basic Feature Foundation

Objectif : transformer une fixture OHLCVT 1m de 60 candles en datasets silver 5m/15m, puis en datasets gold de features mathématiques de base, sans stratégie, sans backtest, sans WebSocket, sans API, sans ML, sans IA/news, sans paper trading et sans live execution.

Commandes :

```bash
python scripts/validate_lot0.py
python scripts/ingest_ohlcvt_fixture.py
python scripts/validate_lot1.py
python scripts/build_lot2_datasets.py
python scripts/validate_lot2.py
python -m pytest -q
```

Invariants : `TradingDecision = WAIT`, `SystemDecision = BLOCK_TRADING`, `trade_allowed = false`, `live_execution = DISABLED`, `leverage = FORBIDDEN`.



## Lot 3 — Pivot Engine & Support/Resistance Zones V1

Lot 3 adds analytical fractal pivots and simple support/resistance zones. It reuses the Lot 2 resampler, generates 5m and 15m datasets from a deterministic 180-candle BTC/EUR fixture, and writes gold datasets for pivots and zones.

Safety constraints remain unchanged: no trading, no strategy, no backtest, no WebSocket, no API, no paper trading, no ML, no AI/news and no live execution. All pivots and zones have `used_for_decision=false`.

Validation:

```bash
python scripts/build_lot3_pivots.py
python scripts/validate_lot3.py
python -m pytest -q
```


## Lot 4 — Volume Profile + VWAP / Anchored VWAP V1

Lot 4 ajoute un moteur Volume Profile candle-based, un VWAP session et un Anchored VWAP avec ancres déterministes.

Périmètre strict : objets d'analyse uniquement, sans trading, sans stratégie, sans backtest, sans API, sans WebSocket, sans ML et sans IA/news.

Commandes :

```bash
python scripts/build_lot4_volume_vwap.py
python scripts/validate_lot4.py
python -m pytest -q
```

Invariants conservés :

```text
TradingDecision = WAIT
SystemDecision = BLOCK_TRADING
trade_allowed = false
```

## Lot 4-bis — Validation Robustness

Lot 4-bis corrige uniquement la robustesse des validations du Lot 4. Il ne change pas le moteur Volume Profile, VWAP ou Anchored VWAP et n'ajoute aucune stratégie.

Objectifs :

- `validate_lot3.py` termine proprement ;
- `validate_lot4.py` termine proprement ;
- aucune validation ne reste bloquée dans une chaîne de subprocess imbriqués ;
- `validate_all_until_lot4.py` orchestre la chaîne complète avec timeouts explicites ;
- les replays de validation ne s'accumulent plus sous forme de nombreux fichiers `reports/replay_*.json`.

Commandes :

```bash
python scripts/validate_lot0.py
python scripts/ingest_ohlcvt_fixture.py
python scripts/validate_lot1.py
python scripts/build_lot2_datasets.py
python scripts/validate_lot2.py
python scripts/build_lot3_pivots.py
python scripts/validate_lot3.py
python scripts/build_lot4_volume_vwap.py
python scripts/validate_lot4.py
python scripts/validate_all_until_lot4.py
python -m pytest -q
```

Commandes avec timeout :

```bash
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 300s python scripts/validate_all_until_lot4.py
```

Invariants conservés : `TradingDecision = WAIT`, `SystemDecision = BLOCK_TRADING`, `trade_allowed = false`, `live_execution = DISABLED`, `leverage = FORBIDDEN`.

## Lot 4-quinquies — Orchestrator Validation Robustness

Lot 4-quinquies corrige uniquement l'orchestrateur de validation complet. Il ne change pas le moteur Volume Profile, VWAP ou Anchored VWAP, et n'ajoute aucune stratégie.

Objectifs :

- `validate_lot3.py` termine proprement en moins de 60 secondes ;
- `validate_lot4.py` termine proprement en moins de 60 secondes ;
- `validate_all_until_lot4.py` termine proprement en moins de 300 secondes ;
- l'orchestrateur ne capture plus stdout/stderr avec `capture_output=True` ;
- stdout/stderr sont streamés directement vers la console ;
- `CQB_SKIP_NESTED_PYTEST=1` évite toute récursion pytest pendant les tests.

Commandes :

```bash
python scripts/validate_all_until_lot4.py
CQB_SKIP_NESTED_PYTEST=1 python scripts/validate_all_until_lot4.py
```

Commandes avec timeout :

```bash
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 300s python scripts/validate_all_until_lot4.py
```

Invariants conservés : `TradingDecision = WAIT`, `SystemDecision = BLOCK_TRADING`, `trade_allowed = false`, `live_execution = DISABLED`, `leverage = FORBIDDEN`.

## Lot 4-quinquies — definitive validation orchestrator

The complete validation up to Lot 4 is now delegated to:

```bash
scripts/validate_all_until_lot4.sh
```

The Python wrapper is intentionally minimal:

```bash
python scripts/validate_all_until_lot4.py
```

Use this audit command:

```bash
timeout 300s python scripts/validate_all_until_lot4.py
```

Expected result:

```text
LOT 4-quinquies VALIDATION: PASS
```

## Lot 4-quinquies — validation orchestrée définitive

- `CQB_ORCHESTRATOR_MODE=fast` est le mode par défaut de `scripts/validate_all_until_lot4.sh`.
- Le mode fast vérifie les artefacts clés et lance les validations Lot 0 à Lot 4 sans rebuild lourd.
- `CQB_ORCHESTRATOR_MODE=full` conserve le rebuild complet explicite.
- `scripts/validate_all_until_lot4.py` reste un wrapper Python minimal vers le script Bash.
- Le test orchestrateur lance réellement le wrapper avec `CQB_SKIP_NESTED_PYTEST=1` et ne skippe plus.
- La sortie attendue est `LOT 4-quinquies VALIDATION: PASS`.

## Lot 15 — Decision Ledger & Immutable Audit Trail V0

Lot 15 ajoute un journal d'audit local qui enregistre uniquement des décisions déjà bloquées par le Lot 14.

Le correctif Lot 15-bis stabilise d'abord la base Lot 14 en conservant le replay de validation Lot 0 et en l'écrivant de manière atomique, ce qui supprime le faux échec `replay file missing`.

Le `Decision Ledger` reste strictement non exécutable :

- `final_decision = WAIT`
- `final_system_decision = BLOCK_TRADING`
- `execution_allowed = false`
- `trade_allowed = false`
- `external_connectivity_allowed = false`
- `human_review_required = true`

Les artefacts Lot 7, Lot 10, Lot 11, Lot 12, Lot 13 et Lot 14 restent du contexte documentaire uniquement.

## Lot 16 — Dataset Lineage & Reproducibility Manifest V0

Lot 16 ajoute un manifeste local de reproductibilité qui référence uniquement des artefacts explicites déjà générés.

Le manifeste :

- ne produit aucune décision exécutable ;
- ne fait aucun appel réseau ;
- calcule uniquement des checksums locaux ;
- vérifie les comptages critiques des lots 12 à 15 ;
- conserve `trade_allowed = false`, `live_execution = DISABLED` et `leverage = FORBIDDEN`.

Depuis le Lot 17, le calcul `source_catalog_checksum` du Lot 16 ignore aussi les entrées audit-only du Health Monitor pour éviter qu'un ajout documentaire local ne casse la reproductibilité déjà validée.
Le checksum du catalogue est aussi normalisé de manière déterministe, indépendamment de l'ordre physique des entrées, ce qui supprime les faux écarts après `upsert` atomique local.

## Lot 17 — Local Health Monitor & Integrity Checks V0

Le Lot 17 ajoute une couche locale de surveillance d'intégrité et de santé projet.

Le correctif Lot 17-bis répare d'abord un point faible de la chaîne existante : `scripts/audit_lot8_feature_registry.py` utilisait un tmp fixe sur le workspace partagé. Le script utilise maintenant un tmp unique avec `flush`, `fsync` et `replace` atomique.
Le correctif finalise aussi la cohérence Lot 16/Lot 17 en recalculant les checksums de catalogue sur un ordre canonique, afin qu'une simple réécriture idempotente du `dataset_catalog` ne casse plus la validation.
Depuis le Lot 18, les checksums Lot 16 et Lot 17 ignorent aussi les entrées audit-only du controle final no-trading, ce qui garde les validations historiques stables après ajout des artefacts documentaire Lot 18.

## Lot 22 — Market Analysis Foundation V0

Le Lot 22 ouvre la V2 avec une couche d'analyse de marche strictement locale, offline, audit-only et non executable.

Cette base produit uniquement :

- un score de contexte descriptif ;
- des resumes par timeframe ;
- des artefacts JSON, JSONL et Markdown auditables.

Le score de contexte reste purement descriptif. Aucun routage, aucune allocation, aucun ordre et aucune connectivite externe ne sont actives.

## Lot 23 — Technical Indicators Pack V0

Le Lot 23 ajoute un premier pack d'indicateurs techniques descriptifs au-dessus du Lot 22.

Les indicateurs restent locaux, offline et non executables. Ils enrichissent l'analyse sans produire d'instruction de marche exploitable, sans papier de trading actif et sans toucher a l'archive V1 figee.

## Lot 24 — Trend / Range / Momentum Engine V0

Le Lot 24 interprete les artefacts Lots 22 et 23 pour decrire le contexte technique sous trois angles : trend, range et momentum.

Le moteur produit uniquement :

- des etats descriptifs par timeframe ;
- un etat combine descriptif ;
- des scores bornes entre `0.0` et `1.0` ;
- des rapports et artefacts auditables.

Le moteur repond uniquement a une question de contexte technique descriptif. Il ne produit ni ordre, ni logique d'execution, ni serveur, ni connectivite externe.

L'archive V1 reste figee et les chaines V2 continuent de la referencer sans la regenerer. Le prochain enrichissement envisage reste limite a volatility, regime et confluence, toujours sans activer le trading.

## Lot 25 — Volatility / Regime / Confluence Enrichment V0

Le Lot 25 interprete les artefacts Lots 22, 23 et 24 pour enrichir la lecture descriptive du contexte sous trois angles : volatility, regime et confluence.

Le moteur produit uniquement :

- des etats descriptifs par timeframe ;
- un etat combine descriptif ;
- des scores bornes entre `0.0` et `1.0` ;
- des rapports et artefacts auditables.

Le moteur repond uniquement a une question de coherence descriptive entre volatilite, regime et contexte technique. Il ne produit ni ordre, ni execution, ni allocation, ni connectivite externe.

L'archive V1 reste figee, les chaines V2 ne la regenerent jamais, et le prochain enrichissement envisage reste limite a l'alignement multi-timeframe du contexte, toujours sans activer le trading.

## Lot 23-quinquies — Lot16 checksum stability after Lot10 diagnostic

Le Lot 23-quinquies corrige un probleme de preparation : `scripts/diagnose_lot10_transaction_cost_writer.py` relancait auparavant `scripts/run_lot10_transaction_costs.py` par defaut, ce qui reecrivait `data/audit/dataset_catalog.json` avant `scripts/diagnose_lot16_source_catalog_checksum.py`.

Le diagnostic Lot 10 est maintenant non-mutant par defaut :

- il lit les artefacts Lot 10 existants ;
- il execute `scripts/validate_lot10.py` ;
- il verifie les counts `5m=36` et `15m=12` ;
- il confirme qu'aucun tmp fixe residuel ne reste ;
- il verifie que `dataset_catalog.json` et `reproducibility_manifest_lot16.json` ne changent pas pendant le diagnostic.

Un mode explicite `--rerun` reste disponible uniquement pour une regeneration volontaire des artefacts Lot 10.

## Lot 19 — Defensive Release Candidate & Final Acceptance Bundle V0

Le Lot 19 produit une release candidate locale defensive, sans archive, pour figer l'etat V1 avant cloture.

Il :

- relit uniquement des artefacts locaux explicites ;
- confirme les Lots 16, 17 et 18 ;
- confirme les comptages critiques `36 / 12 / 48` pour les Lots 12 a 15 ;
- confirme que la chaine exacte Lot 0 a Lot 19 reste attendue verte ;
- ne produit aucune decision executable ;
- ne fait aucun appel reseau ;
- ne cree aucune strategie ni aucun connecteur exchange.

Etats defensifs conserves :

- `project_mode = EDUCATIONAL_AUDIT_ONLY`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`
- `trade_allowed = false`

## Lot 20 — V1 Defensive Audit Closure & Archive Packaging V0

Le Lot 20 cloture la V1 defensive/audit/no-trading locale en produisant une archive finale locale et son SHA256.

Il :

- confirme que les Lots 0 a 19 restent rejouables localement ;
- confirme que la chaine exacte Lot 0 a Lot 20 doit rester verte ;
- confirme que `pytest` doit rester vert ;
- relit le Release Candidate Lot 19, la conformite no-trading Lot 18, le Health Monitor Lot 17 et le manifeste de reproductibilite Lot 16 ;
- calcule une archive `dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz` ;
- calcule un fichier `dist/crypto_quant_bot_v1_defensive_audit_lot_20.sha256` ;
- ne produit aucune decision executable et aucun appel reseau.

Les invariants defensifs restent inchanges :

- `project_mode = EDUCATIONAL_AUDIT_ONLY`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`
- `trade_allowed = false`

Toute V2 eventuelle devra etre ouverte dans un lot separe apres audit du chef de projet.

## Lot 20-bis — Archive Completeness & Extracted Release Verification

Le Lot 20-bis existe parce que la premiere archive finale excluait un test actif uniquement pour contourner un faux positif de scan.

La correction retenue :

- renomme le test technique au lieu de le supprimer ;
- conserve sa logique anti-regression ;
- reintegre ce test dans l'archive finale ;
- regenere l'archive et le SHA256 ;
- verifie l'archive depuis une extraction temporaire ;
- confirme que l'ancien nom n'apparait plus dans l'archive finale.

La V1 defensive/audit n'est consideree fermee qu'apres audit du chef de projet.

## Lot 21 — V2 Functional Scope Lock & Product Roadmap Registry V0

Le Lot 21 n'ouvre pas encore d'implementation produit. Il ouvre uniquement la V2 comme registre fonctionnel et roadmap officielle du meme projet `Crypto Quant Bot V3.1-Ops`.

Il :

- conserve la cloture V1 defensive/audit et ses invariants ;
- documente toutes les capabilities attendues pour la suite, y compris Research OS, AI / News / Event Engine, UI / Dashboard, Account Read-Only, Sandbox Demo Trading et Future Personal Live Trading ;
- fige les phases roadmap Lot 22 a Lot 147 comme forecast-only ;
- produit un registre `data/audit/product_scope_lot21.json` avec checksum deterministe ;
- ne cree aucun trading actif, aucun ordre, aucune connectivite externe et aucun serveur.

Etats obligatoires :

- `project_identity = SAME_PROJECT_NO_V4`
- `v1_closure_state = V1_DEFENSIVE_AUDIT_CLOSED`
- `v2_scope_state = OPENED_AS_PLANNING_ONLY`
- `scope_state = FUNCTIONAL_SCOPE_LOCKED`
- `trade_allowed = false`
- `execution_allowed = false`
- `external_connectivity_allowed = false`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

Tout bloc futur reste non actif au Lot 21 et devra passer par un lot dedie avant toute implementation.

## Lot 21-bis — V1 Archive Freeze Guard & Product Scope Finalization

Le Lot 21-bis existe parce que les premieres chaines V2 rejouaient encore `scripts/run_lot20_v1_closure.py`, ce qui regenerait et ecrasait l'archive V1 finale validee au Lot 20-bis.

La correction retenue :

- traite `dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz` comme preuve V1 immuable pour toute la V2 ;
- ajoute `scripts/validate_v1_archive_frozen.py` pour valider l'archive existante sans la regenerer ;
- remplace dans les chaines Lot 21+ tout rerun de cloture Lot 20 par `validate_lot20.py`, `validate_lot20_archive_extracted.py` et `validate_v1_archive_frozen.py` ;
- finalise le registre produit Lot 21 avec `source_v1_archive_frozen = true` ;
- confirme que la V2 reste strictement `OPENED_AS_PLANNING_ONLY` et `FUNCTIONAL_SCOPE_LOCKED`.

Le registre fonctionnel couvre toujours Research OS, AI / News / Event Engine, UI / Dashboard, Account Read-Only, Sandbox Demo Trading et Future Personal Live Trading, mais aucun de ces blocs n'est actif au Lot 21-bis.

## Lot 22 — Market Analysis Foundation V0

Le Lot 22 demarre l'implementation V2 avec une premiere couche Market Analysis locale, offline, audit-only et non executable.

Il :

- consomme les artefacts marche deja valides des lots precedents via les chemins reels du workspace ;
- produit un resume de contexte par timeframe pour `5m` et `15m` ;
- calcule un `market_context_score` borne entre `0.0` et `1.0` uniquement comme score descriptif ;
- ecrit des artefacts JSON, JSONL et Markdown auditables ;
- conserve `trade_allowed = false`, `execution_allowed = false` et `external_connectivity_allowed = false`.

Le score de contexte n'est pas un signal de trading, aucun terme directionnel d'execution n'est autorise dans les sorties Lot 22 et l'archive V1 gelee reste intouchable.

## Lot 22-bis — Lot16 Source Catalog Checksum Stability After V2 Catalog Entries

Le Lot 22-bis existe parce que la preparation obligatoire du Lot 23 a expose une instabilite sur `source_catalog_checksum` pendant `scripts/validate_lot16.py`.

La correction retenue :

- stabilise le checksum historique Lot 16 sur un perimetre reproductible borne au catalogue jusqu'au Lot 15 inclus ;
- exclut les entrees posterieures, notamment Lots 17 a 22 et futures entrees audit-only ou planning-only detectees via les hints de lot du catalogue ;
- applique exactement la meme normalisation dans le run Lot 16 et dans la validation Lot 16 ;
- aligne aussi le checksum historique Lot 17 sur la meme logique de perimetre borne ;
- confirme que l'archive V1 gelee reste intacte et que le Lot 23 n'a pas ete commence.

## Lot 23 — Technical Indicators Pack V0

Le Lot 23 enrichit la V2 Market Analysis avec un premier pack d'indicateurs techniques strictement local, offline, audit-only et non executable.

Il :

- relit les bougies 5m et 15m deja validees localement ;
- calcule un ensemble descriptif d'indicateurs techniques par timeframe ;
- produit un `indicator_context_score` borne entre `0.0` et `1.0` uniquement comme score descriptif ;
- ecrit des artefacts JSON, JSONL et Markdown auditables ;
- conserve `trade_allowed = false`, `execution_allowed = false` et `external_connectivity_allowed = false`.

Les indicateurs ne produisent aucune instruction executable, les etats techniques restent non directionnels du point de vue execution et l'archive V1 gelee reste intouchable.

## Lot 23-bis — Lot7 Market State JSONL Robustness Before Lot24

Le Lot 23-bis existe parce que la preparation obligatoire du Lot 24 a expose une fragilite intermittente sur la reconstruction Lot 7 dans `scripts/build_lot7_market_state.py`.

La correction retenue :

- rend la lecture JSONL Lot 7 explicite avec chemin, numero de ligne et extrait si une ligne non JSON apparait ;
- ignore uniquement les lignes strictement vides, sans masquer les vrais contenus invalides ;
- remplace l'ecriture JSONL inplace par une ecriture atomique `tmp -> replace` ;
- supprime la relecture immediate fragile du fichier Lot 7 de sortie pendant l'upsert du catalogue en reutilisant les objets deja reconstruits en memoire ;
- ajoute un diagnostic cible `scripts/diagnose_lot7_market_state_jsonl.py` pour verifier les JSONL `market_state` par timeframe ;
- confirme que l'archive V1 gelee reste intacte et que le Lot 24 n'a pas ete commence.

## Lot 23-ter — Lot10 Transaction Costs Atomic Writer Robustness Before Lot24

Le Lot 23-ter existe parce que la preparation obligatoire du Lot 24 a expose une fragilite intermittente dans l'ecriture des artefacts Lot 10 sous `/mnt/hgfs`.

La correction retenue :

- remplace les noms temporaires fixes `.<target>.tmp` du writer Lot 10 par des noms uniques par ecriture ;
- ecrit chaque artefact Lot 10 dans le meme dossier via `tmp -> replace` avec `pid` et `uuid` ;
- force le flush puis `fsync` avant le `replace` ;
- nettoie uniquement le tmp de l'ecriture courante en best-effort si une erreur survient ;
- ajoute `scripts/diagnose_lot10_transaction_cost_writer.py` pour verifier les reruns Lot 10, les counts `5m` et `15m`, la lisibilite JSONL et l'absence de tmp fixe residuel ;
- confirme que l'archive V1 gelee reste intacte et que le Lot 24 n'a pas ete commence.

## Lot 18 - Final No-Trading Compliance Audit V0

Le Lot 18 certifie localement que le projet reste non executable, non connecte et strictement educatif.

Il confirme :

- `final_decision = WAIT`
- `final_system_decision = BLOCK_TRADING`
- `trade_allowed = false`
- `execution_allowed = false`
- `external_connectivity_allowed = false`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

## Lot 19 - Defensive Release Candidate & Final Acceptance Bundle V0

Le Lot 19 produit une release candidate locale defensive, sans archive et sans nouvelle logique de trading.

Il :

- confirme le manifeste de reproductibilite Lot 16 ;
- confirme le Health Monitor Lot 17 ;
- confirme la conformite no-trading Lot 18 ;
- confirme les comptages critiques des Lots 12 a 15 ;
- produit un rapport local de release candidate ;
- produit un acceptance bundle local ;
- laisse `trade_allowed = false`, `live_execution = DISABLED` et `leverage = FORBIDDEN`.

Les entrees audit-only du Lot 19 sont ignorees par les checksums de catalogue des Lots 16 a 18 afin que les reruns locaux restent stables apres production de cette release candidate.

Toute phase suivante devra etre decidee apres audit du chef de projet.

Le Health Monitor :

- vérifie uniquement des artefacts locaux explicites ;
- lit le catalogue dataset et le manifeste Lot 16 ;
- vérifie les checksums et les comptages critiques des Lots 12 à 16 ;
- ne produit aucune décision exécutable ;
- ne fait aucun appel réseau ;
- conserve `live_execution = DISABLED`, `leverage = FORBIDDEN` et `trade_allowed = false`.

## Lot 18 — Final No-Trading Compliance Audit V0

Le Lot 18 ajoute une certification locale finale qui confirme que le projet reste éducatif, non connecté et non exécutable.

Le lot :

- relit explicitement les artefacts Lots 10 à 17 ;
- relit le manifeste Lot 16 et le Health Monitor Lot 17 ;
- confirme l'absence de connecteur exchange ;
- confirme l'absence de routeur d'ordre ;
- confirme l'absence de clé API et de WebSocket ;
- confirme que `final_decision = WAIT`, `final_system_decision = BLOCK_TRADING`, `trade_allowed = false`, `execution_allowed = false` et `external_connectivity_allowed = false`.


## Lot 4-sexies — CI pytest orchestrator test included

Lot 4-sexies removes the remaining pytest deselection filter from `pyproject.toml`. The orchestrator test is now part of the default `python -m pytest -q` run. The validation orchestrator remains fast by default and prints `LOT 4-sexies VALIDATION: PASS`.

Lot 4-sexies final behavior: fast orchestrator validation does not run nested pytest; the default `python -m pytest -q` run executes the orchestrator test directly, with 0 skipped and 0 deselected tests.

Lot 4-sexies CI detail: `pyproject.toml` has no `-k` deselection filter. It keeps `-s` to avoid capture-related hangs while still executing the orchestrator test by default.

Lot 4-sexies pytest exit stabilization: pytest records the real exit status and forces process termination after unconfigure to avoid post-summary hangs in the audit environment.


## Lot 4-septies — Suppression des validations imbriquées

Lot 4-septies corrige le dernier blocage CI : les validations individuelles ne doivent plus s'appeler entre elles. `scripts/validate_lot2.py` ne relance plus `validate_lot0.py` ni `validate_lot1.py`, et aucun `validate_lot1.py` / `validate_lot2.py` / `validate_lot3.py` / `validate_lot4.py` ne contient `capture_output=True` ni d'appel à un autre script de validation de lot.

L'orchestrateur `validate_all_until_lot4.py` / `.sh` est désormais le seul responsable de l'enchaînement complet multi-lots. Le message final attendu est `LOT 4-septies VALIDATION: PASS`.

## Lot 5 — Volatility, ATR, Range & Compression Engine V1

Lot 5 adds realized volatility, True Range, ATR, rolling range state, compression and expansion features. It remains analysis-only: no trading, no strategy, no backtest, no WebSocket, no API, no ML, no IA/news and no live execution.

Validation:

```bash
python scripts/build_lot5_volatility.py
python scripts/validate_lot5.py
python scripts/validate_all_until_lot5.py
```

## Lot 5-bis — Robustesse CI finale

Lot 5-bis ne change pas le moteur Volatility / ATR / Range. Il corrige uniquement la robustesse de validation :

- `validate_lot1.py` ne relance plus l’ingestion via subprocess ;
- `validate_lot1.py` à `validate_lot5.py` sont des validateurs directs ;
- l’orchestrateur Lot 5 reste le seul responsable de l’enchaînement multi-lots ;
- le test orchestrateur Lot 5 exécute réellement `scripts/validate_all_until_lot5.py` en mode fast ;
- la chaîne complète jusqu’au Lot 5 passe sans timeout.

Commande de validation complète :

```bash
timeout 300s bash -lc '
python scripts/validate_lot0.py &&
python scripts/ingest_ohlcvt_fixture.py &&
python scripts/validate_lot1.py &&
python scripts/build_lot2_datasets.py &&
python scripts/validate_lot2.py &&
python scripts/build_lot3_pivots.py &&
python scripts/validate_lot3.py &&
python scripts/build_lot4_volume_vwap.py &&
python scripts/validate_lot4.py &&
python scripts/build_lot5_volatility.py &&
python scripts/validate_lot5.py &&
python -m pytest -q
'
```

## Lot 5-ter

Lot 5-ter stabilizes CI by adding `CQB_ORCHESTRATOR_MODE=smoke` for pytest. The full validation remains available outside pytest through `scripts/validate_all_until_lot5.py` in fast/full mode. Pytest now checks the orchestrator through a quick smoke path and does not rerun heavy validations.

Expected outputs:

```text
LOT 5-ter ORCHESTRATED VALIDATION: PASS
LOT 5-ter ORCHESTRATOR SMOKE: PASS
```


## Lot 6 — Market Regime Engine V1

Lot 6 adds deterministic regime analysis objects based on already validated candles, VWAP, volatility and range-state datasets.

Outputs:

```text
data/gold/btc_eur_5m_regime_lot6.jsonl
data/gold/btc_eur_15m_regime_lot6.jsonl
```

Validation:

```bash
python scripts/build_lot6_regime.py
python scripts/validate_lot6.py
python scripts/validate_all_until_lot6.py
```

Lot 6 remains analysis-only: no strategy, no backtest, no API, no WebSocket, no paper trading, no live execution and no LONG/SHORT signal.

## Lot 7 — Market State Engine V1

Lot 7 adds deterministic MarketStatePoint objects for 5m and 15m timeframes. These objects aggregate validated candles, features, pivots, zones, VWAP, Anchored VWAP, volatility/range state and market regime.

Lot 7 does not generate trading signals, targets, labels, strategy, backtest, WebSocket, API calls, paper trading or live execution. `used_for_decision` remains false.

## Lot 8 — Feature Registry Hardening & Anti-Lookahead Audit V1

Le Lot 8 renforce la gouvernance de la couche feature/data sans ajouter de stratégie de trading.

Ajouts principaux :

```text
src/crypto_quant_bot/contracts/audit.py
src/crypto_quant_bot/audit/
scripts/audit_lot8_feature_registry.py
scripts/audit_lot8_no_lookahead.py
scripts/validate_lot8.py
scripts/validate_all_until_lot8.py
scripts/validate_all_until_lot8.sh
data/audit/feature_registry_audit_lot8.json
data/audit/no_lookahead_audit_lot8.json
reports/lot_08_feature_registry_audit_report.md
reports/lot_08_no_lookahead_report.md
```

Commandes Lot 8 :

```bash
python scripts/audit_lot8_feature_registry.py
python scripts/audit_lot8_no_lookahead.py
python scripts/validate_lot8.py
python scripts/validate_all_until_lot8.py
CQB_ORCHESTRATOR_MODE=smoke CQB_SKIP_NESTED_PYTEST=1 python scripts/validate_all_until_lot8.py
```

Le Lot 8 maintient les invariants défensifs : `TradingDecision=WAIT`, `SystemDecision=BLOCK_TRADING`, `trade_allowed=false`, `live_execution=DISABLED` et `leverage=FORBIDDEN`.


## Lot 9 — Backtest Replay Engine V0

Le Lot 9 ajoute une infrastructure de replay/backtest V0 sans stratégie de trading. Le moteur relit les `MarketState` validés du Lot 7 et applique uniquement la policy neutre `noop_wait_policy`.

Ajouts principaux :

```text
src/crypto_quant_bot/contracts/backtest.py
src/crypto_quant_bot/backtest/
scripts/run_lot9_backtest_replay.py
scripts/validate_lot9.py
scripts/validate_all_until_lot9.py
scripts/validate_all_until_lot9.sh
data/audit/backtest_lot9_run_config.json
data/audit/backtest_lot9_run_result.json
data/audit/backtest_lot9_5m_steps.jsonl
data/audit/backtest_lot9_15m_steps.jsonl
reports/lot_09_backtest_replay_report.md
```

Commandes Lot 9 :

```bash
python scripts/run_lot9_backtest_replay.py
python scripts/validate_lot9.py
python scripts/validate_all_until_lot9.py
CQB_ORCHESTRATOR_MODE=smoke CQB_SKIP_NESTED_PYTEST=1 python scripts/validate_all_until_lot9.py
```

Résultats attendus : `5m steps=36`, `15m steps=12`, `decision_counts.WAIT=48`, `orders_created_count=0`, `fills_created_count=0`, `pnl_total=0`.

Le Lot 9 ne crée aucune stratégie, aucun ordre, aucun target, aucun label, aucun future_* et aucun signal LONG/SHORT exploitable.

## Lot 9-bis — Robustesse orchestrateur / CI finale

Le Lot 9-bis corrige uniquement la robustesse CI du Lot 9. Le Backtest Replay V0 reste inchangé côté logique : policy `noop_wait_policy`, décision `WAIT`, aucun ordre, aucun fill, aucun PnL exploitable.

Corrections principales :

```text
scripts/validate_all_until_lot5.py
scripts/validate_all_until_lot6.py
scripts/validate_all_until_lot7.py
scripts/validate_all_until_lot8.py
scripts/validate_all_until_lot9.py
scripts/validate_all_until_lot5.sh
scripts/validate_all_until_lot6.sh
scripts/validate_all_until_lot7.sh
scripts/validate_all_until_lot8.sh
scripts/validate_all_until_lot9.sh
tests/test_validation_wrappers_no_execv.py
reports/lot_09_bis_validation_report.md
```

Les wrappers Python `validate_all_until_lot5.py` à `validate_all_until_lot9.py` n'utilisent plus `os.execv`. Ils délèguent au shell avec `subprocess.run`, sans capture stdout/stderr, et les scripts shell terminent explicitement par `exit 0` après le message PASS.

Commandes de validation Lot 9-bis :

```bash
timeout 60s python scripts/run_lot9_backtest_replay.py
timeout 60s python scripts/validate_lot9.py
timeout 300s python scripts/validate_all_until_lot9.py
CQB_ORCHESTRATOR_MODE=smoke CQB_SKIP_NESTED_PYTEST=1 timeout 30s python scripts/validate_all_until_lot9.py
python -m pytest -q
```

Le Lot 9-bis ne commence pas le Lot 10 et ne crée aucune stratégie, aucun signal LONG/SHORT, aucun target, aucun label, aucun `future_*`, aucun paper trading, aucun appel API et aucun WebSocket.

## Lot 9-ter — Robustesse CI complète / chaîne obligatoire stable

Le Lot 9-ter ne démarre pas le Lot 10. Il stabilise la chaîne CI obligatoire jusqu'au Lot 9 avec `scripts/run_required_chain_until_lot9.sh`, qui applique un timeout à chaque étape. Il rend les écritures d'audit plus déterministes, stabilise `dataset_catalog.json` par upsert idempotent, et ajoute des tests rapides pour la mini-chaîne Lot 8 → Lot 9.

Commandes de référence :

```bash
timeout 300s bash scripts/run_required_chain_until_lot9.sh
timeout 300s python scripts/validate_all_until_lot9.py
CQB_ORCHESTRATOR_MODE=smoke CQB_SKIP_NESTED_PYTEST=1 timeout 30s python scripts/validate_all_until_lot9.py
python -m pytest -q
```


## Lot 9-ter — Robustesse CI complète / chaîne obligatoire stable

Le Lot 9-ter ne modifie pas la logique Backtest Replay V0. Il stabilise la chaîne CI obligatoire jusqu'au Lot 9 avec des timeouts par étape, des scripts Lot 8 terminables, des écritures atomiques simples et un `dataset_catalog.json` idempotent.

Commande de diagnostic bornée :

```bash
bash scripts/run_required_chain_until_lot9.sh
```

Résultats attendus :

```text
LOT 9-ter REQUIRED CHAIN: PASS
LOT 9 ORCHESTRATED VALIDATION: PASS
LOT 9 ORCHESTRATOR SMOKE: PASS
pytest: all tests passed
dataset_catalog stable
```

## Lot 9-quater — Chaîne CI finale sans pytest bloquant

Le Lot 9-quater ne démarre pas le Lot 10 et ne modifie pas la logique Backtest Replay V0. Il corrige la robustesse finale de la chaîne CI : `scripts/run_required_chain_until_lot9.sh` exécute désormais la chaîne fonctionnelle complète avec timeouts par étape, puis seulement un sous-ensemble smoke pytest borné. Le pytest complet reste obligatoire, mais il est lancé séparément par `python -m pytest -q`.

Nouveaux artefacts :

```text
scripts/diagnose_pytest_after_chain.py
reports/lot_09_quater_validation_report.md
tests/test_lot9_pytest_after_chain_diagnostic.py
```

Résultats attendus :

```text
LOT 9-quater REQUIRED CHAIN: PASS
DIAGNOSE PYTEST AFTER CHAIN: PASS
LOT 9 ORCHESTRATED VALIDATION: PASS
LOT 9 ORCHESTRATOR SMOKE: PASS
pytest: all tests passed
dataset_catalog stable
```

## Lot 9-quinquies — Terminaison propre pytest / CI finale

Le Lot 9-quinquies ne démarre pas le Lot 10 et ne modifie pas la logique Backtest Replay V0. Il corrige la terminaison CI finale : suppression du hack de sortie forcée pytest, suppression de la variable de contournement associée, et preuve explicite que pytest et les chaînes CI retournent réellement au shell.

Commandes de preuve :

```bash
timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'
timeout 120s bash -lc 'bash scripts/run_required_chain_until_lot9.sh; echo REQUIRED_CHAIN_DONE'
timeout 300s bash -lc '<chaîne complète obligatoire> && echo EXACT_CHAIN_DONE'
```

Résultats attendus :

```text
PYTEST_DONE
REQUIRED_CHAIN_DONE
EXACT_CHAIN_DONE
LOT 9-quinquies REQUIRED CHAIN: PASS
DIAGNOSE PYTEST AFTER CHAIN: PASS
pytest: all tests passed
dataset_catalog stable
```

## Lot 9-sexies — Terminaison réelle du process tree CI

Le Lot 9-sexies ne démarre pas le Lot 10 et ne modifie pas la logique Backtest Replay V0. Il corrige la terminaison réelle du process tree CI : le smoke subset final de `scripts/run_required_chain_until_lot9.sh` est désormais strictement passif et le script vérifie qu'aucun enfant direct ne reste vivant avant d'afficher `LOT 9-sexies REQUIRED CHAIN: PASS`.

Nouveaux artefacts :

```text
scripts/diagnose_lingering_processes.py
tests/test_lot9_dataset_catalog_static.py
tests/test_lot9_required_chain_smoke_subset_is_passive.py
tests/test_lot9_lingering_process_diagnostic.py
reports/lot_09_sexies_validation_report.md
```

Commandes de preuve :

```bash
timeout 120s bash -lc 'python -m pytest -q; echo PYTEST_DONE'
timeout 120s bash -lc 'bash scripts/run_required_chain_until_lot9.sh; echo REQUIRED_CHAIN_DONE'
timeout 60s python scripts/diagnose_lingering_processes.py
timeout 300s bash -lc '<chaîne complète obligatoire> && echo EXACT_CHAIN_DONE'
```

Résultats attendus :

```text
PYTEST_DONE
REQUIRED_CHAIN_DONE
EXACT_CHAIN_DONE
LOT 9-sexies REQUIRED CHAIN: PASS
DIAGNOSE LINGERING PROCESSES: PASS
pytest: all tests passed
dataset_catalog stable
no lingering child process
```

## Lot 10 — Transaction Costs, Spread & Slippage Model V0

Le Lot 10 ajoute une couche neutre d'estimation des coûts de transaction. Il lit les BacktestStep `WAIT` du Lot 9 et les MarketState validés du Lot 7 pour produire des estimations théoriques de frais, spread et slippage.

Artefacts principaux :

```text
config/transaction_costs.yaml
src/crypto_quant_bot/contracts/costs.py
src/crypto_quant_bot/costs/
scripts/run_lot10_transaction_costs.py
scripts/validate_lot10.py
data/audit/transaction_cost_lot10_run_result.json
data/audit/transaction_cost_lot10_5m_estimates.jsonl
data/audit/transaction_cost_lot10_15m_estimates.jsonl
reports/lot_10_transaction_costs_report.md
```

Le Lot 10 ne crée aucune stratégie, aucun ordre réel, aucun ordre simulé exploitable, aucun fill, aucun PnL exploitable, aucun paper trading, aucun signal LONG/SHORT, aucun target, aucun label et aucun `future_*`.

Validation Lot 10 attendue :

```bash
python scripts/run_lot10_transaction_costs.py
python scripts/validate_lot10.py
python scripts/validate_all_until_lot10.py
python -m pytest -q
```

Résultat :

```text
LOT 10 TRANSACTION COSTS: PASS
LOT 10 VALIDATION: PASS
LOT 10 ORCHESTRATED VALIDATION: PASS
LOT 10 ORCHESTRATOR SMOKE: PASS
```

### Lot 10-bis — CI termination correction

Lot 10-bis keeps Transaction Costs V0 unchanged and fixes CI termination only. The Lot 10 wrapper now exits naturally without `os._exit`, the required Lot 0 to Lot 10 chain is available through `scripts/run_required_chain_until_lot10.sh`, and `scripts/diagnose_lot10_chain.py` verifies the bounded Lot 8 to Lot 10 critical path.

Expected shell-return proofs: `LOT10_WRAPPER_DONE`, `REQUIRED_CHAIN_LOT10_DONE`, `DIAGNOSE LOT10 CHAIN: PASS`, `PYTEST_DONE`, and `EXACT_CHAIN_DONE`.

Lot 10-bis finalizes CI termination for the Transaction Costs V0 lot. `validate_all_until_lot10.py` exits naturally, `run_required_chain_until_lot10.sh` performs a bounded Lot 0 to Lot 10 chain with passive final smoke checks, and `diagnose_lot10_chain.py` verifies the critical Lot 8 to Lot 10 sequence.

### Lot 10-ter — Terminaison réelle process tree CI Lot 10

Lot 10-ter keeps Transaction Costs V0 unchanged and hardens the CI process-tree termination. The required Lot 10 chain now uses a passive smoke subset and verifies that no direct child process remains before printing PASS. A dedicated diagnostic script, `scripts/diagnose_lot10_lingering_processes.py`, checks the critical Lot 8 → Lot 10 sequence.

## Lot 10-quater — CI propre finale

Le Lot 10-quater corrige la robustesse CI finale du Lot 10 : suppression du shadowing local de pytest, suppression des hacks `os._exit`, ajout d'un diagnostic de résolution pytest et conservation d'une chaîne Lot 10 terminable. Le modèle Transaction Costs V0 reste neutre et non décisionnel.

### Lot 10-quinquies — Correction finale no-lingering check Lot 10

Le Lot 10-quinquies corrige le dernier point CI du Lot 10 : le check shell final basé sur `pgrep/ps` dans la chaîne requise Lot 10 a été supprimé car il pouvait rester instable dans l'environnement d'audit. La chaîne `scripts/run_required_chain_until_lot10.sh` reste bornée, passive en fin de parcours, et affiche `LOT 10-quinquies REQUIRED CHAIN: PASS` avant de retourner au shell.

La vérification des processus persistants reste disponible via `scripts/diagnose_lot10_lingering_processes.py`, exécuté séparément dans les commandes d'audit.


Note CI Lot 10-quinquies: `python -m pytest -q` continue de résoudre vers le package pytest installé. La configuration pytest évite le cache pytest et la sortie terminale verbeuse afin de limiter les problèmes de descripteurs dans les chaînes longues, sans fichier local `pytest.py`, sans `os._exit` et sans wrapper pytest custom.

## Lot 10-sexies — Suppression pytest imbriqué orchestrateur Lot 10

Le Lot 10-sexies retire tout appel pytest imbriqué de `scripts/validate_all_until_lot10.sh`. L’orchestrateur fast/full ne lance plus pytest ; le mode smoke reste shell-only et vérifie uniquement les artefacts Lot 10. Le pytest complet reste exécuté séparément par la chaîne CI exacte via `python -m pytest -q`.


### Lot 10-septies — Chaîne requise Lot 10 rapide et terminable

Lot 10-septies corrige la chaîne requise Lot 10 pour tenir sous le timeout de 120 secondes. Le script `scripts/run_required_chain_until_lot10.sh` devient rapide et passif : il ne relance plus les rebuilds historiques, ne relance plus les audits Lot 8 et ne lance pas pytest. La chaîne exacte complète reste séparée et conserve les builds/audits/pytest requis par la CI complète.

### Lot 10-octies — CI rapide/passive Lot 10

Le Lot 10-octies corrige la terminaison des chaînes rapides Lot 10 :

- `scripts/validate_all_until_lot10.sh` ne dépend plus des validations historiques Lots 0 à 9 en mode fast ;
- `scripts/run_required_chain_until_lot10.sh` vérifie passivement les artefacts Lots 0 à 9 ;
- le lot courant reste exécuté par `run_lot10_transaction_costs.py` puis `validate_lot10.py` ;
- aucun test global n'est imbriqué dans ces chaînes rapides ;
- la chaîne exacte complète reste exécutée séparément par la CI.

## Lot 10-nonies — Exact Chain Termination

Lot 10-nonies closes the remaining Lot 10 CI rejection: the fast/passive wrappers were already fixed in Lot 10-octies, but the exact Lot 0 → Lot 10 command still had to terminate naturally and print `EXACT_CHAIN_DONE`.

Added diagnostic:

```bash
python scripts/diagnose_exact_chain_until_lot10.py
```

Expected markers:

```text
DIAGNOSE EXACT CHAIN LOT10: PASS
EXACT_CHAIN_DONE
PYTEST_DONE
```

The correction is non-functional: no strategy, no live execution, no order, no exploitable paper order, no exploitable PnL, no LONG/SHORT signal, no target/label/future_* field, no API call and no WebSocket were added.

## Lot 10-decies — Stabilisation audit_lot8_no_lookahead dans la chaîne exacte

Lot 10-decies ne commence pas le Lot 11. Il stabilise le point de blocage localisé par l'audit chef de projet autour de `scripts/audit_lot8_no_lookahead.py`, après la séquence historique jusqu'au Lot 7.

L'audit no-lookahead est maintenant borné à la liste explicite de datasets Lot 8. Il ne scanne pas récursivement le dépôt, ne lance aucun subprocess, ne capture aucun PIPE et écrit ses artefacts de façon idempotente.

Commandes de preuve :

```bash
python scripts/audit_lot8_no_lookahead.py
python scripts/diagnose_lot8_no_lookahead_after_chain.py
python scripts/diagnose_exact_chain_until_lot10.py
```

Marqueurs attendus :

```text
LOT 8 NO-LOOKAHEAD AUDIT: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
EXACT_CHAIN_DONE
```

## Lot 10-undecies status

Lot 10-undecies corrects the remaining exact-chain termination issue localized by audit around `scripts/build_lot7_market_state.py` after the historical Lot 0 to Lot 6 sequence. The Lot 7 build script now ends with a normal `main()` return, `print("LOT 7 MARKET STATE BUILD: PASS", flush=True)`, and `raise SystemExit(main())`.

Acceptance evidence is stored in `reports/lot_10_undecies_validation_report.md` and command logs under `reports/lot_10_undecies_command_logs/`. Expected markers are `DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS`, `DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS`, `DIAGNOSE EXACT CHAIN LOT10: PASS`, and `EXACT_CHAIN_DONE`.


### Lot 10-duodecies status

Lot 10-duodecies addresses the final process-tree issue where the exact Lot 0 to Lot 10 chain could print `EXACT_CHAIN_DONE` but not reliably return to the shell afterward.

Added diagnostics:

```bash
python scripts/diagnose_after_pytest_lingering.py
python scripts/diagnose_exact_chain_return_shell.py
```

The pytest suite remains passive/static for long-chain behavior. The project keeps normal `raise SystemExit(main())` exits and does not use `pytest.py`, `os._exit`, `signal.alarm`, or `CQB_DISABLE_PYTEST_FORCE_EXIT`.


### Lot 10-terdecies status

Lot 10-terdecies removes the artificial stdout/stderr detach workarounds introduced while debugging exact-chain termination. Active build, validation and audit scripts no longer close or redirect stdout/stderr to `/dev/null` after PASS. They terminate naturally through `raise SystemExit(main())`. The global `sitecustomize.py` pytest workaround has also been removed.

Added validation:

```bash
python scripts/diagnose_after_pytest_lingering.py
python scripts/diagnose_exact_chain_return_shell.py
python -m pytest -q
```

Expected evidence:

```text
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
```

### Lot 10-quaterdecies status

Lot 10-quaterdecies fixes the remaining long-chain termination issue localized at `scripts/validate_lot5.py` after the historical sequence up to `scripts/build_lot5_volatility.py`. The script now validates `dataset_catalog.json` with bounded structured JSON parsing and checks only the four Lot 5 dataset IDs.

Added validation:

```bash
python scripts/diagnose_lot5_validate_after_chain.py
python scripts/diagnose_exact_chain_return_shell.py
python -m pytest -q
```

Expected evidence:

```text
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
VALIDATE_LOT5_CHAIN_DONE
PYTEST_DONE
EXACT_CHAIN_DONE
```


### Lot 10-quindecies status

Lot 10-quindecies fixes the remaining long-chain termination issue localized at `scripts/validate_lot4.py` after the historical sequence up to `scripts/build_lot4_volume_vwap.py`. The script passed in isolation but could be fragile in a long chain because the dataset catalog check used raw text scanning.

`validate_lot4.py` now validates `data/audit/dataset_catalog.json` with bounded structured JSON parsing and checks only the expected Lot 4 dataset IDs. It keeps a natural exit pattern with `print("LOT 4 VALIDATION: PASS", flush=True)` and `raise SystemExit(main())`.

Added validation:

```bash
python scripts/diagnose_lot4_validate_after_chain.py
python scripts/diagnose_exact_chain_return_shell.py
python -m pytest -q
```

Expected evidence:

```text
DIAGNOSE LOT4 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
VALIDATE_LOT4_CHAIN_DONE
PYTEST_DONE
EXACT_CHAIN_DONE
```


### Lot 10-sexdecies status

Lot 10-sexdecies fixes the diagnostics themselves. After Lot 10-quindecies, the project logic was passing, but a diagnostic could print `PASS` and still not return naturally because it used manual process-tree management.

The active chain diagnostics now use only simple `subprocess.run(..., timeout=..., check=False)` execution. They no longer use `subprocess.Popen`, `start_new_session=True`, `os.killpg`, manual SIGTERM/SIGKILL handling, `process.wait()`, PIPE capture or DEVNULL redirection.

Added validation:

```bash
python scripts/diagnose_lot5_validate_after_chain.py
python scripts/diagnose_exact_chain_return_shell.py
python -m pytest -q
```

Expected evidence:

```text
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
```


### Lot 10-septendecies status

Lot 10-septendecies adds a targeted `/proc` diagnostic for the Lot 0 → Lot 5 diagnostic path. It checks, after each step, whether a project-related descendant process or inherited stdout/stderr fd remains alive.

The final local validation reports no lingering owner after any Lot 0 → Lot 5 step. The shell wrapper also returns naturally after:

```text
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAG5_DONE
```

Added validation:

```bash
python scripts/diagnose_lot5_fd_lingering_owner.py
bash -lc 'python scripts/diagnose_lot5_validate_after_chain.py; echo DIAG5_DONE'
python scripts/diagnose_exact_chain_return_shell.py
python -m pytest -q
```

Expected evidence:

```text
DIAGNOSE LOT5 FD LINGERING OWNER: PASS
DIAG5_DONE
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
```


### Lot 10-octodecies status

Lot 10-octodecies targets the Lot 4 exact-chain blocking point observed after `scripts/build_lot4_volume_vwap.py` and before/narrowly inside `scripts/validate_lot4.py`.

The lot adds `scripts/diagnose_lot4_fd_lingering_owner.py`, a bounded `/proc` diagnostic that checks descendants, project-related Python processes, and inherited stdout/stderr fds after each Lot 0 → Lot 4 step. The audit owner is documented as `scripts/validate_lot4.py`; the correction is a non-business hardening of its bounded forbidden-field traversal while keeping natural process termination.

Added validation:

```bash
python scripts/diagnose_lot4_fd_lingering_owner.py
bash -lc 'python scripts/validate_lot0.py && python scripts/ingest_ohlcvt_fixture.py && python scripts/validate_lot1.py && python scripts/build_lot2_datasets.py && python scripts/validate_lot2.py && python scripts/build_lot3_pivots.py && python scripts/validate_lot3.py && python scripts/build_lot4_volume_vwap.py && python scripts/validate_lot4.py && echo VALIDATE_LOT4_CHAIN_DONE'
python scripts/diagnose_exact_chain_return_shell.py
python -m pytest -q
```

Expected evidence:

```text
DIAGNOSE LOT4 FD LINGERING OWNER: PASS
VALIDATE_LOT4_CHAIN_DONE
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
```


### Lot 10-novemdecies status

Lot 10-novemdecies targets the remaining exact-chain blocking point localized by the chef de projet audit around `scripts/build_lot6_regime.py` and `scripts/validate_lot6.py`.

The lot adds `scripts/diagnose_lot6_validate_after_chain.py`, a bounded `/proc` diagnostic that checks descendants, project-related Python processes, and inherited stdout/stderr fds after every Lot 0 → Lot 6 step. The real faulty script identified for the residual risk is `scripts/validate_lot6.py`; its raw text scan of `data/audit/dataset_catalog.json` has been replaced by a structured, bounded lookup limited to `btc_eur_5m_regime_lot6` and `btc_eur_15m_regime_lot6`.

Added validation:

```bash
python scripts/diagnose_lot6_validate_after_chain.py
bash -lc 'python scripts/validate_lot0.py && python scripts/ingest_ohlcvt_fixture.py && python scripts/validate_lot1.py && python scripts/build_lot2_datasets.py && python scripts/validate_lot2.py && python scripts/build_lot3_pivots.py && python scripts/validate_lot3.py && python scripts/build_lot4_volume_vwap.py && python scripts/validate_lot4.py && python scripts/build_lot5_volatility.py && python scripts/validate_lot5.py && python scripts/build_lot6_regime.py && python scripts/validate_lot6.py && echo VALIDATE_LOT6_CHAIN_DONE'
python scripts/diagnose_exact_chain_return_shell.py
python -m pytest -q
```

Expected evidence:

```text
DIAGNOSE LOT6 VALIDATE AFTER CHAIN: PASS
VALIDATE_LOT6_CHAIN_DONE
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
```


### Lot 11 status

Lot 11 adds a defensive Risk Engine & Decision Firewall V0. It consumes the existing Lot 10 transaction cost outputs as documentary context only and generates 36 blocked 5m snapshots plus 12 blocked 15m snapshots.

The Lot 11 outputs remain strictly non executable:

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `used_for_decision = false`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

No strategy, order, fill, exploitable PnL, paper trading, API call, exchange connector or WebSocket is introduced.


### Lot 12 status

Lot 12 adds an Exposure Guard & Capital Safety Snapshot V0. It consumes Lot 7 Market State, Lot 10 Transaction Costs and Lot 11 Risk Engine outputs as documentary context only and generates 36 blocked 5m exposure snapshots plus 12 blocked 15m exposure snapshots.

The Lot 12 outputs remain strictly non executable:

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `used_for_decision = false`
- `exposure_allowed = false`
- `allocation_allowed = false`
- `rebalance_allowed = false`
- `current_exposure_units = 0`
- `max_exposure_units = 0`
- `capital_at_risk = 0`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

Lot 12 uses Lot 7 Market State, Lot 10 Transaction Costs and Lot 11 Risk Engine as documentary context only. It keeps the project educational, non connected to any exchange, and never authorizes allocation, rebalancing or active exposure.


### Lot 13 status

Lot 13 adds a Portfolio Freeze & Allocation Firewall V0. It consumes Lot 10 Transaction Costs, Lot 11 Risk Engine and Lot 12 Exposure Guard outputs as documentary context only and generates 36 blocked 5m portfolio freeze snapshots plus 12 blocked 15m snapshots.

The Lot 13 outputs remain strictly non executable:

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `trade_allowed = false`
- `used_for_decision = false`
- `portfolio_state = FROZEN`
- `allocation_state = DISABLED`
- `rebalance_state = DISABLED`
- `portfolio_change_allowed = false`
- `allocation_change_allowed = false`
- `allocation_allowed = false`
- `rebalance_allowed = false`
- `new_exposure_allowed = false`
- `exposure_allowed = false`
- `current_exposure_units = 0`
- `max_exposure_units = 0`
- `capital_at_risk = 0`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

Lot 13 uses Lot 10 Transaction Costs, Lot 11 Risk Engine and Lot 12 Exposure Guard as documentary context only. It keeps the project educational, non connected to any exchange, and never authorizes any portfolio change, allocation change, rebalancing or new exposure.


### Lot 14 status

Lot 14 adds a Final Decision Firewall & Audit Trail V0. It consumes Lot 7 Market State, Lot 10 Transaction Costs, Lot 11 Risk Engine, Lot 12 Exposure Guard and Lot 13 Portfolio Freeze outputs as documentary context only and generates 36 blocked 5m final decision snapshots plus 12 blocked 15m snapshots.

The Lot 14 outputs remain strictly non executable:

- `TradingDecision = WAIT`
- `SystemDecision = BLOCK_TRADING`
- `final_decision = WAIT`
- `final_system_decision = BLOCK_TRADING`
- `decision_firewall_state = ACTIVE`
- `execution_allowed = false`
- `trade_allowed = false`
- `used_for_decision = false`
- `risk_allowed = false`
- `exposure_allowed = false`
- `portfolio_state = FROZEN`
- `portfolio_change_allowed = false`
- `allocation_change_allowed = false`
- `rebalance_allowed = false`
- `order_routing_allowed = false`
- `external_connectivity_allowed = false`
- `human_review_required = true`
- `capital_at_risk = 0`
- `live_execution = DISABLED`
- `leverage = FORBIDDEN`

Lot 14 uses Lot 7, Lot 10, Lot 11, Lot 12 and Lot 13 as documentary context only. It keeps the project educational, non connected to any exchange, and never authorizes any executable decision.

### Lot 23-quater status

Lot 23-quater exists because the Lot 24 preparation could still fail intermittently in `scripts/diagnose_exact_chain_return_shell.py` with `source_catalog_checksum mismatch` during `validate_lot16.py`.

The Lot 16 historical checksum is now derived from one canonical function: `compute_lot16_source_catalog_checksum(...)` in [src/crypto_quant_bot/lineage/manifest.py](/mnt/hgfs/Forensic/Bot-crypto/crypto_quant_bot/src/crypto_quant_bot/lineage/manifest.py). That function normalizes the dataset catalog deterministically, deduplicates by `dataset_id` with the same last-write-wins rule as the catalog writer, filters the source scope to Lots 0 through 15, excludes Lot 16 self-produced records plus all later lots, keeps only stable fields, and hashes the canonical JSON.

`scripts/run_lot16_reproducibility_manifest.py`, `scripts/validate_lot16.py`, `scripts/diagnose_lot16_source_catalog_checksum.py`, and the Lot 16 checksum tests now all use this same source of truth. The Lot 16 manifest records `reproducibility_scope_lot16`, `source_catalog_scope`, and `source_catalog_entry_count` for auditability. The frozen V1 archive remains unchanged, and Lot 24 has not been started by this corrective lot.

## Roadmap canonique V1–V21

La source de vérité documentaire est [`docs/ROADMAP_V1_TO_V21.md`](docs/ROADMAP_V1_TO_V21.md). Le cahier des charges maître, la chaîne d’exécution, les contrats, les state machines et les Lots 0–177 sont liés depuis ce document.

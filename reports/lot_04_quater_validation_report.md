# Lot 4-quater Validation Report

## Scope

Correction définitive de l’orchestrateur de validation jusqu’au Lot 4.
Aucune modification fonctionnelle des moteurs Volume Profile, VWAP, Anchored VWAP, pivots, features ou trading.

## Ancienne cause du timeout

L’orchestrateur Python complet pouvait encore bloquer pendant la chaîne globale de validation.
Le projet avait besoin d’un orchestrateur simple, déterministe et auditable.

## Correction appliquée

- Ajout de `scripts/validate_all_until_lot4.sh` avec `timeout` explicites.
- Remplacement de `scripts/validate_all_until_lot4.py` par un wrapper Python minimal.
- Suppression de toute logique Python complexe d’orchestration.
- Suppression de `capture_output=True`, `Popen` complexe, `os.exec*`, boucles Python et logique spéciale.
- Suppression du faux test orchestrateur skippé.
- Test orchestrateur réel avec `CQB_SKIP_NESTED_PYTEST=1`.

## Commandes validées

```bash
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py
timeout 300s python scripts/validate_all_until_lot4.py
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
python -m pytest -q
'
python -m pytest -q
```

## Résultats attendus

- `LOT 4-quater VALIDATION: PASS`
- `pytest: all tests passed`
- aucun timeout de validation
- aucun test orchestrateur skippé

## Invariants

- TradingDecision = WAIT
- SystemDecision = BLOCK_TRADING
- trade_allowed = false
- Risk Engine blocks by default
- live_execution = DISABLED
- leverage = FORBIDDEN

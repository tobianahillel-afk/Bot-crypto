# Lot 10-sexies — Suppression pytest imbriqué orchestrateur Lot 10

Le Lot 10-quinquies avait corrigé le shadowing `pytest.py`, supprimé les sorties forcées `os._exit` et retiré le check shell instable `pgrep/ps` de la chaîne requise Lot 10.

Le rejet restant venait du fait que `scripts/validate_all_until_lot10.sh` lançait encore un pytest smoke subset imbriqué en mode fast. Même si ce subset passait, il rendait la terminaison du process tree instable dans l'environnement d'audit.

## Corrections Lot 10-sexies

- Suppression complète de tout appel `python -m pytest` dans `scripts/validate_all_until_lot10.sh`.
- Suppression de tout pytest imbriqué en mode fast.
- Mode smoke Lot 10 maintenu en vérification shell-only des artefacts.
- Mode full conservé pour rebuild/audit/run, sans pytest imbriqué.
- `python -m pytest -q` reste exécuté séparément par la chaîne CI exacte.
- `pyproject.toml` n'utilise pas `-p no:terminal` et conserve une sortie pytest normale lisible.
- Ajout de tests statiques empêchant le retour d'un pytest imbriqué dans l'orchestrateur Lot 10.

## Preuves attendues

- `LOT10_WRAPPER_DONE` prouve que le wrapper Lot 10 retourne au shell.
- `REQUIRED_CHAIN_LOT10_DONE` prouve que la chaîne requise Lot 10 retourne au shell.
- `PYTEST_DONE` prouve que pytest termine naturellement.
- `EXACT_CHAIN_DONE` prouve que la chaîne exacte atteint sa fin.

## Invariants métier

Le Lot 10-sexies ne modifie pas Transaction Costs V0 :

```text
5m estimates = 36
15m estimates = 12
estimate_count = 48
orders_created_count = 0
fills_created_count = 0
pnl_total = 0
trade_allowed = false
used_for_decision = false
```

Aucune stratégie, aucun ordre réel, aucun ordre simulé exploitable, aucun PnL exploitable, aucun signal LONG/SHORT, aucun `target`, aucun `label`, aucun `future_*`, aucun appel API et aucun WebSocket n'ont été ajoutés.

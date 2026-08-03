# Lot 10-bis — Terminaison CI propre et chaîne exacte stable

## Contexte

Le Lot 10 était fonctionnel côté Transaction Costs V0 : les estimations 5m/15m étaient générées, `validate_lot10.py` passait, aucun ordre, fill, signal ou PnL exploitable n’était créé.

Le rejet portait uniquement sur la terminaison CI : le wrapper `validate_all_until_lot10.py` utilisait encore `os._exit(code)` et pouvait afficher un PASS sans rendre proprement la main au shell.

## Corrections

- Suppression de `os._exit` dans `scripts/validate_all_until_lot10.py`.
- Alignement du wrapper Lot 10 sur les wrappers propres : `subprocess.run(...)`, `timeout=300`, `check=False`, retour du `returncode`, `raise SystemExit(main())`.
- Extension du test anti-wrapper à `os._exit` et au wrapper Lot 10.
- Ajout de `scripts/run_required_chain_until_lot10.sh` avec timeout par étape et smoke subset passif.
- Ajout de `scripts/diagnose_lot10_chain.py` pour diagnostiquer la mini-chaîne critique Lot 8 → Lot 10.

## Preuves attendues

- `LOT10_WRAPPER_DONE` prouve que `validate_all_until_lot10.py` rend la main.
- `REQUIRED_CHAIN_LOT10_DONE` prouve que la chaîne bornée Lot 10 rend la main.
- `DIAGNOSE LOT10 CHAIN: PASS` prouve que la mini-chaîne critique est terminable.
- `PYTEST_DONE` prouve que pytest retourne au shell.
- `EXACT_CHAIN_DONE` prouve que la chaîne exacte Lot 0 → Lot 10 retourne au shell.

## Invariants

Les invariants défensifs restent inchangés : `TradingDecision = WAIT`, `SystemDecision = BLOCK_TRADING`, `trade_allowed = false`, Risk Engine bloque par défaut, `live_execution = DISABLED`, `leverage = FORBIDDEN`.

Ce lot bis ne crée aucune stratégie, aucun ordre, aucun fill, aucun PnL exploitable, aucun signal LONG/SHORT, aucun target, label ou future_*.

## Final Lot 10-bis execution notes

The required Lot 10 wrapper proof returned to the shell with `LOT10_WRAPPER_DONE`.

The required Lot 10 bounded chain returned to the shell with `REQUIRED_CHAIN_LOT10_DONE`. The smoke section in `run_required_chain_until_lot10.sh` is now a passive shell smoke verifier to avoid reintroducing a pytest/fd retention problem inside the required chain. The full pytest run remains executed separately and returns with `PYTEST_DONE`.

The exact Lot 0 to Lot 10 command was executed with `timeout 300s` and produced `EXACT_CHAIN_DONE` with rc=0 in log-captured CI execution.

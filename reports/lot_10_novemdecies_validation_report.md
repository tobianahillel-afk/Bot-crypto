# Lot 10-novemdecies Validation Report

## Scope

Lot 10-novemdecies is limited to the exact-chain termination issue around `build_lot6_regime.py` and `validate_lot6.py`. It does not change Transaction Costs V0, strategy behavior, order creation, fills, PnL, or any defensive trading invariant.

## Problem localization

The previous chef de projet audit validated the Lot 10 Transaction Costs outputs and the earlier Lot 10-octodecies correction on `validate_lot4.py`, but the remaining blocking point moved later in the exact chain:

```text
build_lot6_regime.py -> validate_lot6.py
```

The risk pattern still present in the archive was in `scripts/validate_lot6.py`: the Lot 6 catalog check used a raw text scan of `data/audit/dataset_catalog.json` instead of a structured, bounded JSON read limited to the expected Lot 6 dataset identifiers.

## Changes applied

1. Added `scripts/diagnose_lot6_validate_after_chain.py`.
2. Reworked `scripts/validate_lot6.py` to use `DatasetCatalog.load()` and a bounded lookup limited to:
   - `btc_eur_5m_regime_lot6`
   - `btc_eur_15m_regime_lot6`
3. Normalized Lot 6 file reads to explicit context-managed reads in:
   - `scripts/validate_lot6.py`
   - `scripts/build_lot6_regime.py`
4. Added `tests/test_lot6_validate_after_chain_static.py`.

## Root cause statement

```text
script fautif identifié = scripts/validate_lot6.py
cause = lecture brute non bornée de dataset_catalog.json par recherche texte au lieu d'une lecture JSON structurée et bornée limitée aux dataset_id Lot 6 attendus
correction = remplacement par DatasetCatalog.load() avec borne sur le nombre d'enregistrements et contrôle ciblé des dataset_id btc_eur_5m_regime_lot6 / btc_eur_15m_regime_lot6
```

## Expected proofs

The validation for this lot is complete only when the mandatory commands provide:

```text
DIAGNOSE LOT6 VALIDATE AFTER CHAIN: PASS
VALIDATE_LOT6_CHAIN_DONE
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
rc=0
```

## Observed proofs

The mandatory validation run in the local environment produced:

```text
DIAGNOSE PYTEST RESOLUTION: PASS
DIAGNOSE LOT6 VALIDATE AFTER CHAIN: PASS
VALIDATE_LOT6_CHAIN_DONE
DIAGNOSE LOT4 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT5 VALIDATE AFTER CHAIN: PASS
DIAGNOSE LOT7 BUILD AFTER CHAIN: PASS
DIAGNOSE LOT8 NO-LOOKAHEAD AFTER CHAIN: PASS
DIAGNOSE EXACT CHAIN LOT10: PASS
DIAGNOSE AFTER PYTEST LINGERING: PASS
DIAGNOSE EXACT CHAIN RETURN SHELL: PASS
PYTEST_DONE
EXACT_CHAIN_DONE
174 passed
rc=0
```

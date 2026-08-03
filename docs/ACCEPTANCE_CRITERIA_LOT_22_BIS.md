# Acceptance Criteria - Lot 22-bis

Le Lot 22-bis est accepte si :

- `scripts/run_lot16_reproducibility_manifest.py` produit toujours `LOT 16 REPRODUCIBILITY MANIFEST: PASS`.
- `scripts/validate_lot16.py` produit toujours `LOT 16 VALIDATION: PASS`.
- `source_catalog_checksum` est calcule sur un perimetre historique reproductible borne au catalogue jusqu'au Lot 15 inclus.
- les entrees post-Lot 16, en particulier Lots 17 a 22 et futures entrees audit-only ou planning-only, n'invalident plus le checksum historique Lot 16.
- `scripts/diagnose_exact_chain_return_shell.py` repasse sans relancer `scripts/run_lot20_v1_closure.py`.
- `scripts/diagnose_exact_chain_until_lot22.py` repasse avec `EXACT_CHAIN_LOT22_DONE`.
- l'archive V1 gelee conserve le meme SHA256 et le meme sidecar `.sha256`.
- aucun artefact Lot 23 n'est cree.
- aucun module trading actif, aucune connectivite externe et aucun ordre executable ne sont ajoutes.

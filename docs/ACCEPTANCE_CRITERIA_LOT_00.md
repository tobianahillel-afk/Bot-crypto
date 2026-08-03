# Acceptance Criteria — Lot 0

Le Lot 0 est terminé si :

- l’arborescence obligatoire existe ;
- les configurations YAML existent ;
- `trade_allowed_default` vaut `false` ;
- les modules interdits sont `FORBIDDEN` ou `DISABLED` ;
- le risk engine bloque par défaut ;
- le decision engine retourne `WAIT` ;
- la matrice veto contient les veto essentiels ;
- un replay minimal JSON peut être généré ;
- un rapport `reports/lot_00_validation_report.md` est produit ;
- `scripts/validate_lot0.py` affiche `LOT 0 VALIDATION: PASS`.

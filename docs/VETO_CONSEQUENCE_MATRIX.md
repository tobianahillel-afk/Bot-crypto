# Veto Consequence Matrix

La matrice officielle est dans `config/veto_consequence_matrix.yaml`.

Le Lot 0 impose notamment :

- `book_health_veto -> WAIT`
- `data_quality_veto -> BLOCK_TRADING`
- `security_veto_high -> KILL_SWITCH`
- `reconciliation_veto_critical -> KILL_SWITCH`
- `incident_veto_unresolved -> BLOCK_TRADING`
- `negative_ev_veto -> WAIT`

# Failure, Degraded Mode and Recovery Policy

## Principes

- Une panne d’observabilité n’est pas ignorée : elle dégrade ou pause le runtime.
- Une issue de données bloque l’analyse/action concernée.
- Une issue d’ordre inconnu bloque toute nouvelle exposition avant reconciliation.
- Un recovery ne supprime ni ne réécrit l’historique.

## Matrice de recovery

| Incident | Action immédiate | Recovery requis |
|---|---|---|
| data stale/gap | BLOCK_ANALYSIS/WAIT | resync + quality PASS |
| WS disconnect | WAIT/PAUSE | snapshot+delta resync |
| submit timeout | PAUSE intent | query order/fills, no blind retry |
| ledger mismatch | PAUSE | rebuild + reconcile |
| position inconnue | KILL_SWITCH | venue snapshot + human review |
| secret compromise | KILL_SWITCH | revoke/rotate + audit |
| process crash | LIVE_PAUSED | durable replay + reconciliation |
| corrupted state | LIVE_DISABLED | restore signed backup + replay |

Chaque drill produit timeline, automatic action, operator action, recovery checksum, residual risk et sign-off.

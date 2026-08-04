# Security Policy

## État de sécurité

Le projet est local/offline et le trading est désactivé. Aucune clé réelle, aucun secret,
aucun endpoint exchange et aucun mécanisme de retrait ne doivent être présents.

## Signaler un problème

Ne publiez jamais un secret dans une issue. Décrivez le problème sans donnée sensible et
révoquez immédiatement toute clé potentiellement exposée.

## Règles obligatoires

- secrets référencés, jamais stockés ;
- permissions minimales ;
- withdrawals et leverage interdits ;
- logs et rapports sans secrets ;
- données invalides ou ambiguës → `BLOCKED` / `UNKNOWN` ;
- aucune connectivité externe cachée ;
- dépendances auditées par `pip-audit` ;
- code audité par Bandit ;
- toute future capacité live reste `LIVE_DISABLED_BY_DEFAULT`.

## Réponse

Une faille critique impose gel des promotions, préservation des preuves, analyse de cause,
correctif isolé, test de non-régression et rapport d’incident.

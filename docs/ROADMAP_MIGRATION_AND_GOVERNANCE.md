# Migration et gouvernance de la roadmap

## But

Normaliser l’ancienne roadmap V2+ limitée à V11 / Lot 147 en une roadmap canonique **V1 à V21 / Lots 0 à 177**, sans perdre l’historique d’audit.

## Règles de migration

- Les Lots 0 à 25 conservent leurs numéros, statuts et artefacts existants.
- Le Lot 26 reste le prochain lot réel.
- Les anciens work packages génériques Lots 26 à 147 sont remplacés par des spécifications fonctionnelles détaillées.
- Les suffixes `bis`, `ter`, `quater`, etc. restent des correctifs historiques et ne sont pas convertis en lots principaux.
- Les anciens documents ne sont pas supprimés s’ils constituent une preuve d’audit ; ils sont marqués comme historiques lorsque nécessaire.
- La roadmap canonique est `docs/ROADMAP_V1_TO_V21.md`.
- Les documents `docs/roadmap/Vxx_*.md` sont les spécifications détaillées.
- Le registre JSONL est généré depuis la même structure logique.

## Corrections architecturales intégrées

1. **Data Governance** devient une version complète avant la microstructure.
2. **Signal / Trade Intent / Order Intent** devient une frontière explicite.
3. **TCA** est intégrée au backtesting avant l’EV finale.
4. **Model Risk, Sizing et Risk Approval** précèdent le paper trading.
5. **PnL Core** est unique et réutilisé par paper, sandbox et live.
6. **OMS / EMS** précède le sandbox.
7. **Exchange Risk** est séparé du simple connecteur read-only.
8. **Observability / Incident Response / Disaster Recovery** devient une version dédiée.
9. **HFT** reste research-only.
10. **Options et On-chain** sont des extensions contextuelles optionnelles.

## Synchronisation obligatoire

Toute modification future doit mettre à jour :

- le document de version ;
- le registre machine-readable ;
- le registre fonctionnel ;
- le document d’acceptation du lot concerné ;
- le rapport de validation lors de l’implémentation.

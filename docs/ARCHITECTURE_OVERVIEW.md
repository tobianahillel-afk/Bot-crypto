# Architecture Overview — Lot 0

Le Lot 0 fournit la fondation défensive du projet : configuration, contrats minimaux, logger JSON, risk engine bloquant, decision engine `WAIT`, replay minimal et validation.

Modules inclus :

- `core/` : configuration, horloge, enums, logger JSON.
- `contracts/` : objets minimaux sérialisables.
- `risk/` : blocage par défaut.
- `decision/` : décision défensive par défaut.
- `replay/` : registre JSON minimal.
- `security/` : squelette de politique sécurité.

Modules explicitement exclus du Lot 0 : données marché, Kraken, WebSocket, stratégie, backtest, ML, IA/news, paper trading réel, live execution.

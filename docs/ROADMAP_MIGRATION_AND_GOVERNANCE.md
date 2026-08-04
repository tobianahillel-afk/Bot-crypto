# Migration et gouvernance de la roadmap

## But

Normaliser l’ancienne projection V2→V11 / Lots 22→147 en V1→V21 / Lots 0→177 tout en préservant les contrats historiques du projet.

## Préservation

- Lots 0–25, correctifs bis/ter/quater, rapports et archives restent des preuves primaires.
- Lot 25 reste dernier lot validé ; Lot 26 reste prochain lot.
- Le périmètre initial BTC/EUR spot, Kraken de référence, no leverage, no withdrawal et live disabled est conservé.
- Les anciens contrats décision, veto, ledger/reconciliation, exchange constraints, incident response et seuils historiques sont réintégrés dans les documents canoniques.

## Correspondance des anciennes phases

| Ancienne projection | Nouvelle architecture |
|---|---|
| V2 Market Analysis 22–30 | V2 21–30 |
| V3 Microstructure/Scenarios 31–55 | V3 Data Governance 31–36 + V4 37–52 + V5 53–59 |
| V4 EV/Backtesting 56–66 | V6 60–71 avec TCA intégrée |
| V5 Paper 67–76 | V8 81–87 + V9 Portfolio/PnL 88–95 |
| V6 Research OS 77–87 | V10 96–102 |
| V7 News/AI 88–101 | V11 103–110 |
| V8 UI 102–114 | V12 111–118 |
| V9 Account read-only 115–124 | V13 119–125 |
| V10 Sandbox 125–135 | V15 OMS/EMS 133–141 puis V16 Sandbox 142–149 |
| V11 Live Governance 136–147 | V17 150–157 + V18 158–165 |

## Corrections architecturales

Data governance avant microstructure ; Signal/TradeIntent/OrderIntent séparés ; TCA au cœur du backtest ; OMS/EMS avant sandbox ; PnL Core unique ; risk/strategy promotion gates ; runtime/config/release/rollback/DR explicites ; HFT research-only ; options/on-chain optionnels.

## Synchronisation

Toute évolution met à jour document de version, registre JSONL, functional registry, contrats transverses, acceptance criteria et rapport de validation.

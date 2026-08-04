# Configuration, Environment, CI/CD and Release Governance

## Configuration

Chaque config possède schema version, config_id, content hash, owner, approver, effective_from, expiry, environment et rollback target. Les secrets sont référencés, jamais stockés.

Profils minimaux : `dev`, `test`, `offline_research`, `backtest`, `paper`, `read_only`, `sandbox`, `live_disabled`, `live_manual_approval`.

Les différences entre backtest, paper et sandbox sont exportées dans un `ConfigurationDiffReportV1`. Toute différence non approuvée bloque la promotion.

## CI obligatoire

- unit tests ;
- integration/contract tests ;
- deterministic replay ;
- anti-lookahead/future-state tests ;
- architecture dependency tests ;
- forbidden capabilities / no-live scans ;
- secret/dependency/security scans ;
- schema and registry consistency ;
- report/checksum generation.

## Release

Une release contient source commit, dependency lock, configs, schemas, model/data IDs, test evidence, artifact hashes, migration plan, rollback plan et operator sign-off. Aucun artefact mutable n’est promu.

## Rollback

Le rollback doit restaurer code/config/schema compatibles, passer en mode PAUSED/LIVE_DISABLED, réconcilier ordres/positions avant reprise et conserver l’historique de l’incident.

# Acceptance Criteria - Lot 25

Le Lot 25 est accepte si :

```text
src/crypto_quant_bot/market_analysis/volatility_regime_confluence.py existe.
src/crypto_quant_bot/market_analysis/confluence_models.py existe.
scripts/run_lot25_volatility_regime_confluence.py existe.
scripts/validate_lot25.py existe.
scripts/validate_all_until_lot25.py existe.
scripts/run_required_chain_until_lot25.sh existe.
scripts/diagnose_lot25_required_chain_timing.py existe.
scripts/diagnose_exact_chain_until_lot25.py existe.
data/audit/volatility_regime_confluence_lot25.json existe.
data/audit/volatility_regime_confluence_timeframes_lot25.jsonl existe.
reports/lot_25_volatility_regime_confluence_report.md existe.
reports/lot_25_validation_report.md existe.
docs/LOT_25_VOLATILITY_REGIME_CONFLUENCE.md existe.
docs/ACCEPTANCE_CRITERIA_LOT_25.md existe.
project_name = Crypto Quant Bot V3.1-Ops.
project_mode = EDUCATIONAL_AUDIT_ONLY.
vrc_engine_mode = LOCAL_OFFLINE_VOLATILITY_REGIME_CONFLUENCE_ONLY.
analysis_mode = LOCAL_OFFLINE_ANALYSIS_ONLY.
indicator_mode = LOCAL_OFFLINE_INDICATORS_ONLY.
trend_engine_mode = LOCAL_OFFLINE_TREND_RANGE_MOMENTUM_ONLY.
source_v1_archive_frozen = true.
v2_scope_state = OPENED_AS_PLANNING_ONLY.
execution_allowed = false.
trade_allowed = false.
external_connectivity_allowed = false.
live_execution = DISABLED.
leverage = FORBIDDEN.
dataset_timeframes contient 5m et 15m.
vrc_timeframes contient 5m et 15m.
combined_context_score reste borne entre 0.0 et 1.0.
Les etats de contexte restent descriptifs et non executables.
LOT 25 VOLATILITY REGIME CONFLUENCE: PASS.
LOT 25 VALIDATION: PASS.
LOT 25 ORCHESTRATED VALIDATION: PASS.
LOT 25 REQUIRED CHAIN: PASS.
DIAGNOSE LOT25 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT25: PASS.
EXACT_CHAIN_LOT25_DONE.
rc=0.
```

Le Lot 25 reste un bloc local uniquement, sans ordre, sans execution, sans serveur et sans connectivite externe.

combined_context_state: VRC_CONTEXT_ALIGNED_RANGE

combined_context_score: 0.604791

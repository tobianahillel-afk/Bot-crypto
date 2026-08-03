# Acceptance Criteria - Lot 23

Le Lot 23 est accepte si :

```text
src/crypto_quant_bot/market_analysis/technical_indicators.py existe.
src/crypto_quant_bot/market_analysis/indicator_models.py existe.
scripts/run_lot23_technical_indicators.py existe.
scripts/validate_lot23.py existe.
scripts/validate_all_until_lot23.py existe.
scripts/run_required_chain_until_lot23.sh existe.
scripts/diagnose_lot23_required_chain_timing.py existe.
scripts/diagnose_exact_chain_until_lot23.py existe.
data/audit/technical_indicators_lot23.json existe.
data/audit/technical_indicators_timeframes_lot23.jsonl existe.
reports/lot_23_technical_indicators_report.md existe.
reports/lot_23_validation_report.md existe.
docs/LOT_23_TECHNICAL_INDICATORS.md existe.
docs/ACCEPTANCE_CRITERIA_LOT_23.md existe.
project_name = Crypto Quant Bot V3.1-Ops.
project_mode = EDUCATIONAL_AUDIT_ONLY.
indicator_mode = LOCAL_OFFLINE_INDICATORS_ONLY.
analysis_mode = LOCAL_OFFLINE_ANALYSIS_ONLY.
source_v1_archive_frozen = true.
v2_scope_state = OPENED_AS_PLANNING_ONLY.
execution_allowed = false.
trade_allowed = false.
external_connectivity_allowed = false.
live_execution = DISABLED.
leverage = FORBIDDEN.
dataset_timeframes contient 5m et 15m.
indicator_timeframes contient 5m et 15m.
indicator_context_score reste borne entre 0.0 et 1.0.
Les etats techniques restent descriptifs et non executables.
LOT 23 TECHNICAL INDICATORS: PASS.
LOT 23 VALIDATION: PASS.
LOT 23 ORCHESTRATED VALIDATION: PASS.
LOT 23 REQUIRED CHAIN: PASS.
DIAGNOSE LOT23 REQUIRED CHAIN TIMING: PASS.
DIAGNOSE EXACT CHAIN LOT23: PASS.
EXACT_CHAIN_LOT23_DONE.
rc=0.
```

Indicator set:
- sma_3
- sma_5
- ema_3
- ema_5
- rolling_high_5
- rolling_low_5
- rolling_range_5
- close_vs_sma_5_percent
- close_vs_ema_5_percent
- rsi_5
- macd_fast_3_slow_6
- macd_signal_3
- macd_histogram
- bollinger_mid_5
- bollinger_upper_5
- bollinger_lower_5
- bollinger_width_5
- true_range
- atr_5
- momentum_3
- rate_of_change_3

Le Lot 23 reste un bloc d'indicateurs locaux uniquement, sans ordre, sans execution, sans serveur et sans connectivite externe.

indicator_state: INDICATOR_MIXED

indicator_context_score: 0.337561

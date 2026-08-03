#!/usr/bin/env bash
set -euo pipefail

MODE="${CQB_ORCHESTRATOR_MODE:-fast}"

require_file() {
  test -f "$1"
}

require_lines() {
  local expected="$1"
  local path="$2"
  local actual
  actual="$(wc -l < "$path" | tr -d ' ')"
  test "${actual}" = "${expected}"
}

check_required_artifacts() {
  require_file scripts/validate_lot0.py
  require_file scripts/validate_lot1.py
  require_file scripts/validate_lot2.py
  require_file scripts/validate_lot3.py
  require_file scripts/validate_lot4.py
  require_file scripts/validate_lot5.py
  require_file scripts/validate_lot6.py
  require_file scripts/validate_lot7.py
  require_file scripts/validate_lot8.py
  require_file scripts/validate_lot9.py
  require_file scripts/run_lot9_backtest_replay.py
  require_file scripts/audit_lot8_feature_registry.py
  require_file scripts/audit_lot8_no_lookahead.py
  require_file scripts/build_lot2_datasets.py
  require_file scripts/build_lot3_pivots.py
  require_file scripts/build_lot4_volume_vwap.py
  require_file scripts/build_lot5_volatility.py
  require_file scripts/build_lot6_regime.py
  require_file scripts/build_lot7_market_state.py
  require_file src/crypto_quant_bot/contracts/backtest.py
  require_file src/crypto_quant_bot/backtest/replay.py
  require_file src/crypto_quant_bot/backtest/noop_policy.py
  require_file src/crypto_quant_bot/backtest/lookahead_guard.py
  require_file data/gold/btc_eur_5m_market_state_lot7.jsonl
  require_file data/gold/btc_eur_15m_market_state_lot7.jsonl
  require_file data/audit/feature_registry_audit_lot8.json
  require_file data/audit/no_lookahead_audit_lot8.json
  require_file data/audit/backtest_lot9_run_config.json
  require_file data/audit/backtest_lot9_run_result.json
  require_file data/audit/backtest_lot9_5m_steps.jsonl
  require_file data/audit/backtest_lot9_15m_steps.jsonl
  require_file reports/lot_09_backtest_replay_report.md
  require_file docs/BACKTEST_REPLAY_ENGINE_POLICY.md
  require_file docs/BACKTEST_NOOP_POLICY.md
  require_file docs/BACKTEST_ANTI_LOOKAHEAD_POLICY.md
  require_file docs/ACCEPTANCE_CRITERIA_LOT_09.md
  require_file docs/LOT_09_REPORT.md
  require_file pyproject.toml
  require_lines 36 data/audit/backtest_lot9_5m_steps.jsonl
  require_lines 12 data/audit/backtest_lot9_15m_steps.jsonl
}

echo "=== Crypto Quant Bot validation until Lot 9 ==="
echo "mode=${MODE}"
echo "=== CHECK required artifacts ==="
check_required_artifacts

if [[ "${MODE}" == "smoke" ]]; then
  echo "=== SMOKE mode: artifact checks only ==="
  echo "LOT 9 ORCHESTRATOR SMOKE: PASS"
  exit 0
fi

if [[ "${MODE}" == "full" ]]; then
  echo "=== FULL rebuild and validation mode ==="
  python scripts/ingest_ohlcvt_fixture.py
  python scripts/build_lot2_datasets.py
  python scripts/build_lot3_pivots.py
  python scripts/build_lot4_volume_vwap.py
  python scripts/build_lot5_volatility.py
  python scripts/build_lot6_regime.py
  python scripts/build_lot7_market_state.py
  python scripts/audit_lot8_feature_registry.py
  python scripts/audit_lot8_no_lookahead.py
  python scripts/run_lot9_backtest_replay.py
else
  echo "=== FAST mode: direct validation without rebuild ==="
fi

python scripts/validate_lot0.py
python scripts/validate_lot1.py
python scripts/validate_lot2.py
python scripts/validate_lot3.py
python scripts/validate_lot4.py
python scripts/validate_lot5.py
python scripts/validate_lot6.py
python scripts/validate_lot7.py
python scripts/validate_lot8.py
python scripts/validate_lot9.py

echo "=== SKIP pytest in orchestrator; run python -m pytest -q separately in CI ==="
echo "LOT 9 ORCHESTRATED VALIDATION: PASS"
exit 0

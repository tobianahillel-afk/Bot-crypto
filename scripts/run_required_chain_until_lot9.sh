#!/usr/bin/env bash
set -euo pipefail

run_step() {
  local label="$1"
  shift
  echo "=== RUN ${label} ==="
  timeout 60s "$@"
  echo "=== DONE ${label} ==="
}

run_step "validate_lot0" python scripts/validate_lot0.py
run_step "ingest_ohlcvt_fixture" python scripts/ingest_ohlcvt_fixture.py
run_step "validate_lot1" python scripts/validate_lot1.py
run_step "build_lot2_datasets" python scripts/build_lot2_datasets.py
run_step "validate_lot2" python scripts/validate_lot2.py
run_step "build_lot3_pivots" python scripts/build_lot3_pivots.py
run_step "validate_lot3" python scripts/validate_lot3.py
run_step "build_lot4_volume_vwap" python scripts/build_lot4_volume_vwap.py
run_step "validate_lot4" python scripts/validate_lot4.py
run_step "build_lot5_volatility" python scripts/build_lot5_volatility.py
run_step "validate_lot5" python scripts/validate_lot5.py
run_step "build_lot6_regime" python scripts/build_lot6_regime.py
run_step "validate_lot6" python scripts/validate_lot6.py
run_step "build_lot7_market_state" python scripts/build_lot7_market_state.py
run_step "validate_lot7" python scripts/validate_lot7.py
run_step "audit_lot8_feature_registry" python scripts/audit_lot8_feature_registry.py
run_step "audit_lot8_no_lookahead" python scripts/audit_lot8_no_lookahead.py
run_step "validate_lot8" python scripts/validate_lot8.py
run_step "run_lot9_backtest_replay" python scripts/run_lot9_backtest_replay.py
run_step "validate_lot9" python scripts/validate_lot9.py

echo "=== RUN pytest smoke subset ==="
timeout 60s python -m pytest -q \
  tests/test_lot9_run_outputs.py \
  tests/test_lot9_invariants.py \
  tests/test_lot9_dataset_catalog_static.py

echo "=== CHECK no lingering direct children ==="
children="$(ps -o pid= --ppid "$$" | tr -d ' ' || true)"
if [ -n "$children" ]; then
  echo "Lingering child processes detected:"
  ps -o pid,ppid,stat,cmd -p $children || true
  exit 1
fi

echo "LOT 9-sexies REQUIRED CHAIN: PASS"
exit 0

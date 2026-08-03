#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

require_absent() {
  test ! -e "$1"
}

require_lines() {
  local expected="$1"
  local path="$2"
  local actual
  actual="$(wc -l < "$path" | tr -d ' ')"
  test "${actual}" = "${expected}"
}

require_json_field() {
  local path="$1"
  local pattern="$2"
  grep -q "$pattern" "$path"
}

run_current_lot_step() {
  local label="$1"
  shift
  echo "=== RUN ${label} ==="
  timeout 60s "$@"
  echo "=== DONE ${label} ==="
}

echo "=== Crypto Quant Bot Lot 10 required chain, octies fast passive ==="

require_absent py"test.py"
require_absent py"test"
require_absent unittest.py
require_absent subprocess.py
require_absent signal.py
require_absent os.py

require_file README.md
require_file config/feature_registry.yaml
require_file config/transaction_costs.yaml
require_file src/crypto_quant_bot/contracts/audit.py
require_file src/crypto_quant_bot/contracts/backtest.py
require_file src/crypto_quant_bot/contracts/costs.py
require_file docs/LOT_08_REPORT.md
require_file docs/LOT_09_REPORT.md
require_file docs/LOT_10_REPORT.md
require_file reports/lot_08_feature_registry_audit_report.md
require_file reports/lot_08_no_lookahead_report.md
require_file reports/lot_09_backtest_replay_report.md
require_file reports/lot_10_transaction_costs_report.md

require_file data/audit/feature_registry_audit_lot8.json
require_file data/audit/no_lookahead_audit_lot8.json
require_json_field data/audit/feature_registry_audit_lot8.json '"forbidden_feature_names": \[\]'
require_json_field data/audit/feature_registry_audit_lot8.json '"lookahead_violations": \[\]'
require_json_field data/audit/feature_registry_audit_lot8.json '"available_at_violations": \[\]'
require_json_field data/audit/feature_registry_audit_lot8.json '"used_for_decision_violations": \[\]'
require_json_field data/audit/no_lookahead_audit_lot8.json '"forbidden_feature_names": \[\]'
require_json_field data/audit/no_lookahead_audit_lot8.json '"lookahead_violations": \[\]'
require_json_field data/audit/no_lookahead_audit_lot8.json '"available_at_violations": \[\]'

require_file data/audit/backtest_lot9_run_result.json
require_file data/audit/backtest_lot9_5m_steps.jsonl
require_file data/audit/backtest_lot9_15m_steps.jsonl
require_lines 36 data/audit/backtest_lot9_5m_steps.jsonl
require_lines 12 data/audit/backtest_lot9_15m_steps.jsonl
require_json_field data/audit/backtest_lot9_run_result.json '"orders_created_count": 0'
require_json_field data/audit/backtest_lot9_run_result.json '"fills_created_count": 0'
require_json_field data/audit/backtest_lot9_run_result.json '"pnl_total": 0'
require_json_field data/audit/backtest_lot9_run_result.json '"WAIT": 48'

run_current_lot_step "run_lot10_transaction_costs" python scripts/run_lot10_transaction_costs.py
run_current_lot_step "validate_lot10" python scripts/validate_lot10.py

echo "=== RUN passive smoke subset ==="
require_file data/audit/transaction_cost_lot10_run_result.json
require_file data/audit/transaction_cost_lot10_5m_estimates.jsonl
require_file data/audit/transaction_cost_lot10_15m_estimates.jsonl
require_lines 36 data/audit/transaction_cost_lot10_5m_estimates.jsonl
require_lines 12 data/audit/transaction_cost_lot10_15m_estimates.jsonl
require_json_field data/audit/transaction_cost_lot10_run_result.json '"estimate_count": 48'
require_json_field data/audit/transaction_cost_lot10_run_result.json '"orders_created_count": 0'
require_json_field data/audit/transaction_cost_lot10_run_result.json '"fills_created_count": 0'
require_json_field data/audit/transaction_cost_lot10_run_result.json '"pnl_total": 0'
require_json_field data/audit/transaction_cost_lot10_run_result.json '"trade_allowed": false'
require_json_field data/audit/transaction_cost_lot10_run_result.json '"used_for_decision": false'
echo "LOT 10 PASSIVE SMOKE SUBSET: PASS"
echo "=== DONE passive smoke subset ==="

echo "LOT 10-octies REQUIRED CHAIN: PASS"
exit 0

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

require_json_field() {
  local path="$1"
  local pattern="$2"
  grep -q "$pattern" "$path"
}

check_common_artifacts() {
  require_file README.md
  require_file config/feature_registry.yaml
  require_file config/transaction_costs.yaml
  require_file src/crypto_quant_bot/contracts/audit.py
  require_file src/crypto_quant_bot/contracts/backtest.py
  require_file src/crypto_quant_bot/contracts/costs.py
  require_file src/crypto_quant_bot/costs/estimator.py
  require_file docs/LOT_08_REPORT.md
  require_file docs/LOT_09_REPORT.md
  require_file docs/LOT_10_REPORT.md
  require_file data/audit/feature_registry_audit_lot8.json
  require_file data/audit/no_lookahead_audit_lot8.json
  require_file data/audit/backtest_lot9_run_result.json
  require_file data/audit/backtest_lot9_5m_steps.jsonl
  require_file data/audit/backtest_lot9_15m_steps.jsonl
  require_file data/audit/transaction_cost_lot10_run_result.json
  require_file data/audit/transaction_cost_lot10_5m_estimates.jsonl
  require_file data/audit/transaction_cost_lot10_15m_estimates.jsonl
  require_file reports/lot_08_feature_registry_audit_report.md
  require_file reports/lot_08_no_lookahead_report.md
  require_file reports/lot_09_backtest_replay_report.md
  require_file reports/lot_10_transaction_costs_report.md
  require_lines 36 data/audit/backtest_lot9_5m_steps.jsonl
  require_lines 12 data/audit/backtest_lot9_15m_steps.jsonl
  require_lines 36 data/audit/transaction_cost_lot10_5m_estimates.jsonl
  require_lines 12 data/audit/transaction_cost_lot10_15m_estimates.jsonl
  require_json_field data/audit/feature_registry_audit_lot8.json '"forbidden_feature_names": \[\]'
  require_json_field data/audit/feature_registry_audit_lot8.json '"lookahead_violations": \[\]'
  require_json_field data/audit/feature_registry_audit_lot8.json '"available_at_violations": \[\]'
  require_json_field data/audit/feature_registry_audit_lot8.json '"used_for_decision_violations": \[\]'
  require_json_field data/audit/no_lookahead_audit_lot8.json '"lookahead_violations": \[\]'
  require_json_field data/audit/backtest_lot9_run_result.json '"orders_created_count": 0'
  require_json_field data/audit/backtest_lot9_run_result.json '"fills_created_count": 0'
  require_json_field data/audit/backtest_lot9_run_result.json '"pnl_total": 0'
  require_json_field data/audit/backtest_lot9_run_result.json '"WAIT": 48'
  require_json_field data/audit/transaction_cost_lot10_run_result.json '"estimate_count": 48'
  require_json_field data/audit/transaction_cost_lot10_run_result.json '"orders_created_count": 0'
  require_json_field data/audit/transaction_cost_lot10_run_result.json '"fills_created_count": 0'
  require_json_field data/audit/transaction_cost_lot10_run_result.json '"pnl_total": 0'
  require_json_field data/audit/transaction_cost_lot10_run_result.json '"trade_allowed": false'
  require_json_field data/audit/transaction_cost_lot10_run_result.json '"used_for_decision": false'
}

run_current_lot() {
  timeout 60s python scripts/run_lot10_transaction_costs.py
  timeout 60s python scripts/validate_lot10.py
}

echo "=== Crypto Quant Bot validation until Lot 10 ==="
echo "mode=${MODE}"
echo "=== CHECK passive artifacts ==="
check_common_artifacts

if [[ "${MODE}" == "smoke" ]]; then
  echo "LOT 10 ORCHESTRATOR SMOKE: PASS"
  exit 0
fi

if [[ "${MODE}" == "full" ]]; then
  echo "=== FULL mode: current lot refresh with passive historical checks ==="
else
  echo "=== FAST mode: passive historical checks and current lot validation ==="
fi

run_current_lot

echo "LOT 10 ORCHESTRATED VALIDATION: PASS"
exit 0

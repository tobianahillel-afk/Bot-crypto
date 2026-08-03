#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 11 required chain ==="
require_file scripts/run_required_chain_until_lot10.sh
require_file scripts/run_lot11_risk_engine.py
require_file scripts/validate_lot11.py

timeout 120s bash scripts/run_required_chain_until_lot10.sh
timeout 60s python scripts/run_lot11_risk_engine.py
timeout 60s python scripts/validate_lot11.py

echo "LOT 11 REQUIRED CHAIN: PASS"
exit 0

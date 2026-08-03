#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 13 required chain ==="
require_file scripts/run_required_chain_until_lot12.sh
require_file scripts/run_lot13_portfolio_freeze.py
require_file scripts/validate_lot13.py

timeout 180s bash scripts/run_required_chain_until_lot12.sh
timeout 60s python scripts/run_lot13_portfolio_freeze.py
timeout 60s python scripts/validate_lot13.py

echo "LOT 13 REQUIRED CHAIN: PASS"
exit 0

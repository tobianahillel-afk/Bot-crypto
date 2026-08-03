#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 18 required chain ==="
require_file scripts/run_required_chain_until_lot17.sh
require_file scripts/run_lot18_no_trading_compliance.py
require_file scripts/validate_lot18.py

timeout 240s bash scripts/run_required_chain_until_lot17.sh
timeout 60s python scripts/run_lot18_no_trading_compliance.py
timeout 60s python scripts/validate_lot18.py

echo "LOT 18 REQUIRED CHAIN: PASS"
exit 0

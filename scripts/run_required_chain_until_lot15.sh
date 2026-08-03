#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 15 required chain ==="
require_file scripts/run_required_chain_until_lot14.sh
require_file scripts/run_lot15_decision_ledger.py
require_file scripts/validate_lot15.py

timeout 240s bash scripts/run_required_chain_until_lot14.sh
timeout 60s python scripts/run_lot15_decision_ledger.py
timeout 60s python scripts/validate_lot15.py

echo "LOT 15 REQUIRED CHAIN: PASS"
exit 0

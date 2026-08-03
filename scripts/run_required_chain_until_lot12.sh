#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 12 required chain ==="
require_file scripts/run_required_chain_until_lot11.sh
require_file scripts/run_lot12_exposure_guard.py
require_file scripts/validate_lot12.py

timeout 120s bash scripts/run_required_chain_until_lot11.sh
timeout 60s python scripts/run_lot12_exposure_guard.py
timeout 60s python scripts/validate_lot12.py

echo "LOT 12 REQUIRED CHAIN: PASS"
exit 0

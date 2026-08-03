#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 14 required chain ==="
require_file scripts/run_required_chain_until_lot13.sh
require_file scripts/run_lot14_decision_firewall.py
require_file scripts/validate_lot14.py

timeout 240s bash scripts/run_required_chain_until_lot13.sh
timeout 60s python scripts/run_lot14_decision_firewall.py
timeout 60s python scripts/validate_lot14.py

echo "LOT 14 REQUIRED CHAIN: PASS"
exit 0

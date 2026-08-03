#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 17 required chain ==="
require_file scripts/run_required_chain_until_lot16.sh
require_file scripts/run_lot17_health_monitor.py
require_file scripts/validate_lot17.py

timeout 240s bash scripts/run_required_chain_until_lot16.sh
timeout 60s python scripts/run_lot17_health_monitor.py
timeout 60s python scripts/validate_lot17.py

echo "LOT 17 REQUIRED CHAIN: PASS"
exit 0

#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 22 required chain ==="
require_file scripts/run_required_chain_until_lot21.sh
require_file scripts/validate_v1_archive_frozen.py
require_file scripts/run_lot22_market_analysis.py
require_file scripts/validate_lot22.py

timeout 240s bash scripts/run_required_chain_until_lot21.sh
timeout 120s python scripts/validate_v1_archive_frozen.py
timeout 60s python scripts/run_lot22_market_analysis.py
timeout 60s python scripts/validate_lot22.py

echo "LOT 22 REQUIRED CHAIN: PASS"
exit 0

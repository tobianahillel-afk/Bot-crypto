#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 23 required chain ==="
require_file scripts/run_required_chain_until_lot22.sh
require_file scripts/validate_v1_archive_frozen.py
require_file scripts/run_lot23_technical_indicators.py
require_file scripts/validate_lot23.py

timeout 240s bash scripts/run_required_chain_until_lot22.sh
timeout 120s python scripts/validate_v1_archive_frozen.py
timeout 60s python scripts/run_lot23_technical_indicators.py
timeout 60s python scripts/validate_lot23.py

echo "LOT 23 REQUIRED CHAIN: PASS"
exit 0

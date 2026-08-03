#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 20 required chain ==="
require_file scripts/run_required_chain_until_lot19.sh
require_file scripts/run_lot20_v1_closure.py
require_file scripts/validate_lot20.py
require_file scripts/validate_lot20_archive_extracted.py

timeout 240s bash scripts/run_required_chain_until_lot19.sh
timeout 60s python scripts/run_lot20_v1_closure.py
timeout 60s python scripts/validate_lot20.py
timeout 180s python scripts/validate_lot20_archive_extracted.py

echo "LOT 20 REQUIRED CHAIN: PASS"
exit 0

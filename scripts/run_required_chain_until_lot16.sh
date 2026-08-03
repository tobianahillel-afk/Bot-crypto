#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 16 required chain ==="
require_file scripts/run_required_chain_until_lot15.sh
require_file scripts/run_lot16_reproducibility_manifest.py
require_file scripts/validate_lot16.py

timeout 240s bash scripts/run_required_chain_until_lot15.sh
timeout 60s python scripts/run_lot16_reproducibility_manifest.py
timeout 60s python scripts/validate_lot16.py

echo "LOT 16 REQUIRED CHAIN: PASS"
exit 0

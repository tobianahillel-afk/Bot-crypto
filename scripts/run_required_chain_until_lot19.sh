#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 19 required chain ==="
require_file scripts/run_required_chain_until_lot18.sh
require_file scripts/run_lot19_release_candidate.py
require_file scripts/validate_lot19.py

timeout 240s bash scripts/run_required_chain_until_lot18.sh
timeout 60s python scripts/run_lot19_release_candidate.py
timeout 60s python scripts/validate_lot19.py

echo "LOT 19 REQUIRED CHAIN: PASS"
exit 0

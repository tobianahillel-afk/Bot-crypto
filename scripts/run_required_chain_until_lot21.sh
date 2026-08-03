#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 21 required chain ==="
require_file scripts/run_required_chain_until_lot19.sh
require_file scripts/validate_lot20.py
require_file scripts/validate_lot20_archive_extracted.py
require_file scripts/validate_v1_archive_frozen.py
require_file scripts/run_lot21_product_scope.py
require_file scripts/validate_lot21.py

timeout 240s bash scripts/run_required_chain_until_lot19.sh
timeout 60s python scripts/validate_lot20.py
timeout 180s python scripts/validate_lot20_archive_extracted.py
timeout 120s python scripts/validate_v1_archive_frozen.py
timeout 60s python scripts/run_lot21_product_scope.py
timeout 60s python scripts/validate_lot21.py

echo "LOT 21 REQUIRED CHAIN: PASS"
exit 0

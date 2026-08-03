#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot validation until Lot 12 ==="
require_file scripts/validate_all_until_lot11.py
require_file scripts/run_lot12_exposure_guard.py
require_file scripts/validate_lot12.py

timeout 300s python scripts/validate_all_until_lot11.py
timeout 60s python scripts/run_lot12_exposure_guard.py
timeout 60s python scripts/validate_lot12.py

echo "LOT 12 ORCHESTRATED VALIDATION: PASS"
exit 0

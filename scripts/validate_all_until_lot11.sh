#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot validation until Lot 11 ==="
require_file scripts/validate_all_until_lot10.py
require_file scripts/run_lot11_risk_engine.py
require_file scripts/validate_lot11.py

timeout 300s python scripts/validate_all_until_lot10.py
timeout 60s python scripts/run_lot11_risk_engine.py
timeout 60s python scripts/validate_lot11.py

echo "LOT 11 ORCHESTRATED VALIDATION: PASS"
exit 0

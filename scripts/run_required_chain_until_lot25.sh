#!/usr/bin/env bash
set -euo pipefail

require_file() {
  test -f "$1"
}

echo "=== Crypto Quant Bot Lot 25 required chain ==="
require_file scripts/run_required_chain_until_lot24.sh
require_file scripts/diagnose_lot7_market_state_jsonl.py
require_file scripts/diagnose_lot10_transaction_cost_writer.py
require_file scripts/diagnose_lot16_source_catalog_checksum.py
require_file scripts/validate_v1_archive_frozen.py
require_file scripts/run_lot25_volatility_regime_confluence.py
require_file scripts/validate_lot25.py

timeout 240s bash scripts/run_required_chain_until_lot24.sh
timeout 60s python scripts/diagnose_lot7_market_state_jsonl.py
timeout 60s python scripts/diagnose_lot10_transaction_cost_writer.py
timeout 60s python scripts/diagnose_lot16_source_catalog_checksum.py
timeout 120s python scripts/validate_v1_archive_frozen.py
timeout 60s python scripts/run_lot25_volatility_regime_confluence.py
timeout 60s python scripts/validate_lot25.py

echo "LOT 25 REQUIRED CHAIN: PASS"
exit 0

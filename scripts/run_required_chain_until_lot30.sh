#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python scripts/run_lot30_v2_market_analysis_closure.py "$@"
python scripts/validate_lot30.py

echo "LOT 30 REQUIRED CHAIN: PASS"

#!/usr/bin/env bash
set -euo pipefail

MODE="${CQB_ORCHESTRATOR_MODE:-fast}"

require_file() {
  test -f "$1"
}

require_lines() {
  local expected="$1"
  local path="$2"
  local actual
  actual="$(wc -l < "$path" | tr -d ' ')"
  test "${actual}" = "${expected}"
}

check_required_artifacts() {
  require_file scripts/validate_lot0.py
  require_file scripts/validate_lot1.py
  require_file scripts/validate_lot2.py
  require_file scripts/validate_lot3.py
  require_file scripts/validate_lot4.py
  require_file scripts/validate_lot5.py
  require_file scripts/validate_lot6.py
  require_file scripts/build_lot2_datasets.py
  require_file scripts/build_lot3_pivots.py
  require_file scripts/build_lot4_volume_vwap.py
  require_file scripts/build_lot5_volatility.py
  require_file scripts/build_lot6_regime.py
  require_file data/gold/btc_eur_5m_regime_lot6.jsonl
  require_file data/gold/btc_eur_15m_regime_lot6.jsonl
  require_file reports/lot_06_regime_report.md
  require_file config/regime.yaml
  require_file pyproject.toml
  require_lines 36 data/gold/btc_eur_5m_regime_lot6.jsonl
  require_lines 12 data/gold/btc_eur_15m_regime_lot6.jsonl
}

echo "=== Crypto Quant Bot validation until Lot 6 ==="
echo "mode=${MODE}"
echo "=== CHECK required artifacts ==="
check_required_artifacts

if [[ "${MODE}" == "smoke" ]]; then
  echo "=== SMOKE mode: artifact checks only ==="
  echo "LOT 6 ORCHESTRATOR SMOKE: PASS"
  exit 0
fi

if [[ "${MODE}" == "full" ]]; then
  echo "=== FULL rebuild and validation mode ==="
  python scripts/ingest_ohlcvt_fixture.py
  python scripts/build_lot2_datasets.py
  python scripts/build_lot3_pivots.py
  python scripts/build_lot4_volume_vwap.py
  python scripts/build_lot5_volatility.py
  python scripts/build_lot6_regime.py
else
  echo "=== FAST mode: direct validation without rebuild ==="
fi

python scripts/validate_lot0.py
python scripts/validate_lot1.py
python scripts/validate_lot2.py
python scripts/validate_lot3.py
python scripts/validate_lot4.py
python scripts/validate_lot5.py
python scripts/validate_lot6.py

echo "=== SKIP pytest in orchestrator; run python -m pytest -q separately in CI ==="
echo "LOT 6 ORCHESTRATED VALIDATION: PASS"

exit 0

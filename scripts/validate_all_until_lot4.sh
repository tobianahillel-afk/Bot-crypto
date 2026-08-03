#!/usr/bin/env bash
set -euo pipefail

MODE="${CQB_ORCHESTRATOR_MODE:-fast}"

echo "=== Crypto Quant Bot validation until Lot 4 ==="
echo "mode=${MODE}"

echo "=== CHECK required artifacts ==="
test -f scripts/validate_lot0.py
test -f scripts/validate_lot1.py
test -f scripts/validate_lot2.py
test -f scripts/validate_lot3.py
test -f scripts/validate_lot4.py
test -f data/gold/btc_eur_5m_volume_profile_lot4.jsonl
test -f data/gold/btc_eur_15m_volume_profile_lot4.jsonl
test -f data/gold/btc_eur_5m_vwap_lot4.jsonl
test -f data/gold/btc_eur_15m_vwap_lot4.jsonl
test -f data/gold/btc_eur_5m_anchored_vwap_lot4.jsonl
test -f data/gold/btc_eur_15m_anchored_vwap_lot4.jsonl

if [[ "${MODE}" == "full" ]]; then
  echo "=== FULL rebuild mode ==="
  timeout 60s python scripts/ingest_ohlcvt_fixture.py
  timeout 60s python scripts/build_lot2_datasets.py
  timeout 60s python scripts/build_lot3_pivots.py
  timeout 60s python scripts/build_lot4_volume_vwap.py
else
  echo "=== FAST mode: skip rebuild steps ==="
fi

echo "=== RUN validations ==="
timeout 60s python scripts/validate_lot0.py
timeout 60s python scripts/validate_lot1.py
timeout 60s python scripts/validate_lot2.py
timeout 60s python scripts/validate_lot3.py
timeout 60s python scripts/validate_lot4.py

if [[ "${MODE}" == "full" && "${CQB_SKIP_NESTED_PYTEST:-0}" != "1" ]]; then
  echo "=== RUN pytest in full mode ==="
  rm -f data/audit/replay_validation/latest_validation_replay.json
  timeout 180s python -m pytest -q
else
  echo "=== SKIP pytest in fast/nested mode ==="
fi

echo "LOT 4-septies VALIDATION: PASS"

exit 0

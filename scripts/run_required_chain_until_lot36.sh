#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

for lot in 31 32 33 34 35 36; do
  python "scripts/validate_lot${lot}.py"
done

python scripts/validate_lot36_no_connectivity.py
python scripts/validate_all_until_lot36.py

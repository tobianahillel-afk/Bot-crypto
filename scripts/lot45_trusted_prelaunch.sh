#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <code_commit> <command> [args...]" >&2
  exit 64
fi

code_commit="$1"
shift

if [[ ! "$code_commit" =~ ^[0-9a-f]{40}$ ]]; then
  echo "LOT45_PRELAUNCH_INVALID_CODE_COMMIT" >&2
  exit 65
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
cd "$repo_root"

resolved="$(git rev-parse --verify "${code_commit}^{commit}" 2>/dev/null || true)"
if [[ "$resolved" != "$code_commit" ]]; then
  echo "LOT45_PRELAUNCH_CODE_COMMIT_UNRESOLVED" >&2
  exit 66
fi

bound_paths=(
  src/crypto_quant_bot
  scripts/lot45_trusted_prelaunch.sh
  scripts/run_lot45_order_flow_delta_and_cvd_engine.py
  scripts/validate_lot45.py
  config/microstructure/order_flow_delta_and_cvd_engine_v1.json
  contracts/schemas/order_flow_delta_cvd_engine_state_v1.schema.json
  contracts/schemas/order_flow_delta_cvd_engine_audit_v1.schema.json
  contracts/schemas/order_flow_state_v1.schema.json
  contracts/schemas/cvd_series_v1.schema.json
)

if ! git diff --quiet "$code_commit" -- "${bound_paths[@]}"; then
  echo "LOT45_PRELAUNCH_COMMITTED_TREE_DRIFT" >&2
  exit 67
fi
if ! git diff --quiet -- "${bound_paths[@]}"; then
  echo "LOT45_PRELAUNCH_WORKING_TREE_DRIFT" >&2
  exit 68
fi
if ! git diff --cached --quiet -- "${bound_paths[@]}"; then
  echo "LOT45_PRELAUNCH_STAGED_TREE_DRIFT" >&2
  exit 69
fi

# This check intentionally includes ignored and untracked paths. It runs in
# trusted shell before Python can import sitecustomize/usercustomize or any
# sourceless/native module placed below the repository source root.
source_status="$(git status --porcelain=v1 --untracked-files=all --ignored -- src)"
if [[ -n "$source_status" ]]; then
  echo "LOT45_PRELAUNCH_UNBOUND_EXECUTABLE_TREE" >&2
  printf '%s\n' "$source_status" >&2
  exit 70
fi

exec env \
  -u PYTHONSTARTUP \
  -u PYTHONINSPECT \
  PYTHONPATH="$repo_root/src" \
  PYTHONSAFEPATH=1 \
  PYTHONNOUSERSITE=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONHASHSEED=0 \
  "$@"

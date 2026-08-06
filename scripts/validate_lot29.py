from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crypto_quant_bot.market_analysis.alignment_io import load_json  # noqa: E402
from crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit import (  # noqa: E402
    validate_persisted_state,
)

CONFIG_PATH = "config/replay/v2_deterministic_replay_audit_v1.json"
OUTPUT_PATH = "data/audit/v2_deterministic_replay_and_audit_lot29.json"
AUDIT_PATH = "data/audit/v2_deterministic_replay_and_audit_audit_lot29.json"
CLOSURE_PATH = "data/audit/v2_replay_closure_manifest_lot29.json"


def validate(root: Path) -> dict[str, Any]:
    config = load_json(root / CONFIG_PATH)
    state = load_json(root / OUTPUT_PATH)
    audit = load_json(root / AUDIT_PATH)
    closure = load_json(root / CLOSURE_PATH)
    if not all(isinstance(item, dict) for item in (config, state, audit, closure)):
        raise TypeError("Lot29 persisted documents must be JSON objects")
    return validate_persisted_state(root, config, state, audit, closure)


def main() -> int:
    result = validate(REPOSITORY_ROOT)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

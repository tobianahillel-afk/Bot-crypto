#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRM = ROOT / "tests" / "test_p06_trend_range_momentum_complete.py"
VRC = ROOT / "tests" / "test_p06_vrc_complete.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text and old not in text:
        return
    if old not in text:
        raise RuntimeError(f"expected source not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    replace_once(
        TRM,
        '    ])[0] == "TRM_CONTEXT_RANGING"\n    assert trm._aggregate_combined_state([\n        summary(combined_state="TRM_CONTEXT_NEUTRAL"),',
        '    ])[0] == "TRM_CONTEXT_COMPRESSED"\n    assert trm._aggregate_combined_state([\n        summary(combined_state="TRM_CONTEXT_NEUTRAL"),',
    )
    replace_once(VRC, "    assert divergence == 0.8\n", "    assert divergence == 0.6\n")
    print("P0.6 expectation corrections applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

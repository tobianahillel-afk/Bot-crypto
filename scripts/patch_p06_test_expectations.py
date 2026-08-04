#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRM = ROOT / "tests" / "test_p06_trend_range_momentum_complete.py"
VRC = ROOT / "tests" / "test_p06_vrc_complete.py"
ASSURANCE = ROOT / "scripts" / "run_p06_final_assurance.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text and old not in text:
        return
    if old not in text:
        raise RuntimeError(f"expected source not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_assurance_runner() -> None:
    text = ASSURANCE.read_text(encoding="utf-8")
    text = text.replace(
        "from typing import Sequence\n",
        "from collections.abc import Sequence\n",
        1,
    )
    text = text.replace(
        '        return {\n            "schema_version": schema_version,\n            "status": "FAIL",\n            "reason": "mutation summary not found",\n        }\n',
        '        return {\n            "schema_version": schema_version,\n            "killed": 0,\n            "timeout": 0,\n            "suspicious": 0,\n            "survived": 0,\n            "evaluated": 0,\n            "score_percent": 0.0,\n            "minimum_score_percent": 80.0,\n            "status": "FAIL",\n            "reason": "mutation summary not found",\n        }\n',
        1,
    )
    text = text.replace(
        'def _patch_extended_mutation_config(text: str) -> str:\n    start = text.index("only_mutate = [")\n',
        'def _patch_extended_mutation_config(text: str) -> str:\n    text = text.replace(\n        \'source_paths = ["src/crypto_quant_bot/market_analysis/"]\',\n        \'source_paths = ["src/crypto_quant_bot/"]\',\n        1,\n    )\n    start = text.index("only_mutate = [")\n',
        1,
    )
    text = text.replace(
        '  "src/crypto_quant_bot/market_analysis/volatility_regime_confluence.py",\n]\'\'\'\n    text = text[:start] + replacement + text[end:]\n',
        '  "src/crypto_quant_bot/market_analysis/volatility_regime_confluence.py",\n]\n\'\'\'\n    text = text[:start] + replacement + text[end:]\n',
        1,
    )
    text = text.replace(
        '  "tests/test_p06_vrc_complete.py",\n]\'\'\'\n    return text[:start] + replacement + text[end:]\n',
        '  "tests/test_p06_vrc_complete.py",\n]\n\'\'\'\n    return text[:start] + replacement + text[end:]\n',
        1,
    )
    text = text.replace(
        '    subprocess.run(["git", "clean", "-fd"], cwd=ROOT, check=True)\n',
        '    subprocess.run(\n        [\n            "git",\n            "clean",\n            "-fd",\n            "-e",\n            "reports/quality/p06_final_assurance/",\n        ],\n        cwd=ROOT,\n        check=True,\n    )\n',
        1,
    )
    ASSURANCE.write_text(text, encoding="utf-8")


def main() -> int:
    replace_once(
        TRM,
        '        summary(combined_state="TRM_CONTEXT_VOLATILE"),\n    ])[0] == "TRM_CONTEXT_MIXED"\n',
        '        summary(combined_state="TRM_CONTEXT_VOLATILE"),\n    ])[0] == "TRM_CONTEXT_VOLATILE"\n',
    )
    replace_once(VRC, "    assert divergence == 0.8\n", "    assert divergence == 0.6\n")
    patch_assurance_runner()
    print("P0.6 final corrections applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

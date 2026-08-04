#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VRC = ROOT / "src" / "crypto_quant_bot" / "market_analysis" / "volatility_regime_confluence.py"
READINESS = ROOT / "scripts" / "validate_pre_lot26_readiness.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text and old not in text:
        return
    if old not in text:
        raise RuntimeError(f"expected source not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def normalize_allowlist() -> None:
    text = READINESS.read_text(encoding="utf-8")
    duplicate = (
        '        "src/crypto_quant_bot/market_analysis/trend_range_momentum.py",\n'
        '        "src/crypto_quant_bot/market_analysis/trend_range_momentum.py",\n'
    )
    text = text.replace(
        duplicate,
        '        "src/crypto_quant_bot/market_analysis/trend_range_momentum.py",\n',
    )
    vrc_line = '        "src/crypto_quant_bot/market_analysis/volatility_regime_confluence.py",\n'
    if vrc_line not in text:
        anchor = '        "src/crypto_quant_bot/market_analysis/trend_range_momentum.py",\n'
        if anchor not in text:
            raise RuntimeError("TRM allowlist anchor missing")
        text = text.replace(anchor, anchor + vrc_line, 1)
    READINESS.write_text(text, encoding="utf-8")


def main() -> int:
    replace_once(
        VRC,
        '    if agreement_score <= 0.25:\n'
        '        return "CONFLUENCE_CONTEXT_WEAK"\n'
        '    if agreement_score <= 0.2 and divergence_score <= 0.2:\n'
        '        return "CONFLUENCE_CONTEXT_NEUTRAL"\n',
        '    if agreement_score <= 0.2 and divergence_score <= 0.2:\n'
        '        return "CONFLUENCE_CONTEXT_NEUTRAL"\n'
        '    if agreement_score <= 0.25:\n'
        '        return "CONFLUENCE_CONTEXT_WEAK"\n',
    )
    replace_once(
        VRC,
        '    if "INSUFFICIENT_DATA" in {volatility_state, regime_state, confluence_state}:\n',
        '    if any(\n'
        '        "INSUFFICIENT_DATA" in state\n'
        '        for state in (volatility_state, regime_state, confluence_state)\n'
        '    ):\n',
    )
    normalize_allowlist()
    print("P0.6 VRC state fixes applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

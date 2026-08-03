#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.market_state.loader import InvalidJsonlError, read_jsonl

FILES = {
    "5m": ROOT / "data" / "gold" / "btc_eur_5m_market_state_lot7.jsonl",
    "15m": ROOT / "data" / "gold" / "btc_eur_15m_market_state_lot7.jsonl",
}


def main() -> int:
    try:
        for timeframe, path in FILES.items():
            rows = read_jsonl(path)
            print(f"timeframe={timeframe} rows={len(rows)} path={path}", flush=True)
    except InvalidJsonlError as exc:
        print("DIAGNOSE LOT7 MARKET STATE JSONL: FAIL", flush=True)
        print(str(exc), flush=True)
        return 1
    print("DIAGNOSE LOT7 MARKET STATE JSONL: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.replay.replay_registry import ReplayRegistry


def main() -> int:
    decision = DecisionEngine().decide_default()
    record = ReplayRegistry(ROOT / "reports").save_decision(decision)
    print("SMOKE TEST: PASS")
    print(f"trading_decision={decision.trading_decision}")
    print(f"system_decision={decision.system_decision}")
    print(f"trade_allowed={decision.trade_allowed}")
    print(f"replay_id={record.replay_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

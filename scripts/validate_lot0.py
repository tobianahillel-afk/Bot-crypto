#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.core.config_loader import ConfigLoader
from crypto_quant_bot.decision.decision_engine import DecisionEngine
from crypto_quant_bot.replay.replay_registry import ReplayRegistry
from crypto_quant_bot.risk.risk_engine import RiskEngine

REQUIRED_FILES = [
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    ".gitignore",
    "config/markets.yaml",
    "config/timeframes.yaml",
    "config/operational_thresholds.yaml",
    "config/module_status_matrix.yaml",
    "config/veto_consequence_matrix.yaml",
    "config/risk.yaml",
    "docs/PROJECT_IDENTITY.md",
    "docs/ARCHITECTURE_OVERVIEW.md",
    "docs/SECURITY_POLICY.md",
    "docs/OPERATIONAL_THRESHOLDS.md",
    "docs/VETO_CONSEQUENCE_MATRIX.md",
    "docs/MODULE_STATUS_MATRIX.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_00.md",
    "docs/LOT_00_REPORT.md",
    "scripts/validate_lot0.py",
    "scripts/run_smoke_test.py",
    "src/crypto_quant_bot/__init__.py",
    "src/crypto_quant_bot/core/config_loader.py",
    "src/crypto_quant_bot/core/logger.py",
    "src/crypto_quant_bot/core/enums.py",
    "src/crypto_quant_bot/core/clock.py",
    "src/crypto_quant_bot/contracts/base.py",
    "src/crypto_quant_bot/contracts/market_data.py",
    "src/crypto_quant_bot/contracts/decision.py",
    "src/crypto_quant_bot/contracts/risk.py",
    "src/crypto_quant_bot/contracts/replay.py",
    "src/crypto_quant_bot/contracts/security.py",
    "src/crypto_quant_bot/decision/decision_engine.py",
    "src/crypto_quant_bot/risk/risk_engine.py",
    "src/crypto_quant_bot/replay/replay_registry.py",
    "src/crypto_quant_bot/security/security_policy.py",
    "tests/test_config_loader.py",
    "tests/test_decision_default_wait.py",
    "tests/test_risk_default_block.py",
    "tests/test_veto_matrix.py",
]



def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    loader = ConfigLoader(ROOT / "config")

    for rel in REQUIRED_FILES:
        check((ROOT / rel).exists(), f"missing required file: {rel}", errors)

    thresholds = loader.load("operational_thresholds")
    modules = loader.load("module_status_matrix")
    vetoes = loader.load("veto_consequence_matrix")
    risk_cfg = loader.load("risk")

    check(thresholds.get("trade_allowed_default") is False, "trade_allowed_default must be false", errors)
    check(risk_cfg.get("trade_allowed_default") is False, "risk trade_allowed_default must be false", errors)
    check(modules.get("leverage") == "FORBIDDEN", "leverage must be FORBIDDEN", errors)
    check(modules.get("withdrawals") == "FORBIDDEN", "withdrawals must be FORBIDDEN", errors)
    check(modules.get("api_withdrawal_permission") == "FORBIDDEN", "api withdrawal permission must be FORBIDDEN", errors)
    check(modules.get("live_execution") == "DISABLED", "live execution must be DISABLED", errors)

    required_vetoes = {
        "book_health_veto": "WAIT",
        "data_quality_veto": "BLOCK_TRADING",
        "risk_veto": "BLOCK_TRADING",
        "security_veto_high": "KILL_SWITCH",
        "reconciliation_veto_critical": "KILL_SWITCH",
        "incident_veto_unresolved": "BLOCK_TRADING",
        "negative_ev_veto": "WAIT",
    }
    for name, consequence in required_vetoes.items():
        value = vetoes.get(name)
        check(isinstance(value, dict), f"{name} must be a mapping", errors)
        if isinstance(value, dict):
            check(value.get("consequence") == consequence, f"{name} must consequence {consequence}", errors)

    risk_decision = RiskEngine().evaluate_default()
    check(risk_decision.trade_allowed is False, "risk engine must block by default", errors)
    check(risk_decision.reason == "default_block_until_validated", "risk default reason mismatch", errors)

    decision = DecisionEngine().decide_default()
    check(decision.trading_decision == "WAIT", "decision engine must return WAIT", errors)
    check(decision.system_decision == "BLOCK_TRADING", "decision engine must return BLOCK_TRADING", errors)
    check(decision.trade_allowed is False, "decision trade_allowed must be false", errors)
    check(bool(decision.replay_id), "decision replay_id missing", errors)

    record = ReplayRegistry(ROOT / "reports").save_decision(decision)
    replay_path = (ROOT / record.path) if not Path(record.path).is_absolute() else Path(record.path)
    check(replay_path.exists(), "replay file missing", errors)

    report = ROOT / "reports" / "lot_00_validation_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    if errors:
        status = "FAIL"
        content = "# Lot 0 Validation Report\n\nStatus: FAIL\n\nErrors:\n" + "\n".join(f"- {e}" for e in errors) + "\n"
    else:
        status = "PASS"
        content = "# Lot 0 Validation Report\n\nStatus: PASS\n\nChecks:\n- Required files exist\n- Configs load\n- trade_allowed_default is false\n- Forbidden modules are locked\n- Veto matrix contains core vetoes\n- Risk engine blocks by default\n- Decision engine returns WAIT and BLOCK_TRADING\n- Replay JSON generated\n"
    report.write_text(content, encoding="utf-8")

    print(f"LOT 0 VALIDATION: {status}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

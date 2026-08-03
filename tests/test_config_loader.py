from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.core.config_loader import ConfigLoader


def test_config_loader_loads_operational_thresholds():
    cfg = ConfigLoader(ROOT / "config").load("operational_thresholds")
    assert cfg["trade_allowed_default"] is False
    assert cfg["book_health_min_trade"] == 0.80

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.core.config_loader import ConfigLoader


def test_veto_matrix_contains_security_kill_switch():
    vetoes = ConfigLoader(ROOT / "config").load("veto_consequence_matrix")
    assert vetoes["security_veto_high"]["consequence"] == "KILL_SWITCH"


def test_module_status_leverage_forbidden():
    modules = ConfigLoader(ROOT / "config").load("module_status_matrix")
    assert modules["leverage"] == "FORBIDDEN"

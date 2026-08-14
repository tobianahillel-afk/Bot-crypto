from __future__ import annotations

from pathlib import Path

from crypto_quant_bot.compliance import no_trading_audit
from scripts.run_lot18_no_trading_compliance import _configure_network_scan_policy

ROOT = Path(__file__).resolve().parents[1]


def test_security_deny_lists_do_not_self_trigger_lot18_network_scan() -> None:
    original_fragments = list(no_trading_audit.NETWORK_FORBIDDEN_FRAGMENTS)
    try:
        _configure_network_scan_policy()
        hits = no_trading_audit._network_surface_hits(ROOT)
    finally:
        no_trading_audit.NETWORK_FORBIDDEN_FRAGMENTS[:] = original_fragments

    assert "scripts/validate_lot42_no_connectivity.py:urllib.request" not in hits
    assert "scripts/validate_lot43_no_connectivity.py:urllib.request" not in hits


def test_real_network_import_remains_detected(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "network_client.py").write_text("import requests\n", encoding="utf-8")

    hits = no_trading_audit._network_surface_hits(tmp_path)

    assert "scripts/network_client.py:import requests" in hits

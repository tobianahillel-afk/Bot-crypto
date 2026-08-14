from __future__ import annotations

from pathlib import Path

from crypto_quant_bot.compliance.no_trading_audit import _network_surface_hits

ROOT = Path(__file__).resolve().parents[1]


def test_security_deny_lists_do_not_self_trigger_lot18_network_scan() -> None:
    hits = _network_surface_hits(ROOT)

    assert "scripts/validate_lot42_no_connectivity.py:urllib.request" not in hits
    assert "scripts/validate_lot43_no_connectivity.py:urllib.request" not in hits


def test_real_network_import_remains_detected(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "network_client.py").write_text("import requests\n", encoding="utf-8")

    hits = _network_surface_hits(tmp_path)

    assert "scripts/network_client.py:import requests" in hits

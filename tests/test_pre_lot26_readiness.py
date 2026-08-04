from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_pre_lot26_readiness.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_pre_lot26_readiness", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pre_lot26_readiness_is_go() -> None:
    module = _load_module()
    checks = module.run_checks(ROOT)
    failures = [check for check in checks if check.status != "PASS"]
    assert not failures, failures


def test_config_rejects_non_normalized_weights() -> None:
    module = _load_module()
    payload = json.loads(
        (ROOT / "config/math/multi_timeframe_alignment_v1.json").read_text(encoding="utf-8")
    )
    payload["component_weights"]["trend"] = 0.50
    errors = module.validate_config(payload)
    assert any("sum to 1" in error for error in errors)


def test_config_rejects_permissive_promotion() -> None:
    module = _load_module()
    payload = json.loads(
        (ROOT / "config/math/multi_timeframe_alignment_v1.json").read_text(encoding="utf-8")
    )
    payload["promotion_restrictions"]["signal_generation_allowed"] = True
    errors = module.validate_config(payload)
    assert any("permissions must be false" in error for error in errors)


def test_config_rejects_asymmetric_matrix() -> None:
    module = _load_module()
    payload = json.loads(
        (ROOT / "config/math/multi_timeframe_alignment_v1.json").read_text(encoding="utf-8")
    )
    payload["categorical_compatibility"]["range"]["RANGE_CONTEXT_COMPRESSED"][
        "RANGE_CONTEXT_NEUTRAL"
    ] = 0.1
    errors = module.validate_config(payload)
    assert any("not symmetric" in error for error in errors)

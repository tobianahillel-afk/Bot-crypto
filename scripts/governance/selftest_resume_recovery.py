#!/usr/bin/env python3
"""Adversarial self-tests for deterministic resume/recovery semantics."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MAX_SELFTEST_MS = 1000.0


def _module() -> ModuleType:
    path = ROOT / "scripts/governance/resume_recovery_qualification.py"
    spec = importlib.util.spec_from_file_location("resume_recovery_selftest_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _expect(exc_type: type[Exception], fn: Any, label: str) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"resume/recovery negative scenario unexpectedly passed: {label}")


def main() -> int:
    started = time.perf_counter()
    mod = _module()
    handoff = _json(ROOT / "engineering/handoff/CURRENT.json")
    context = _json(ROOT / "engineering/CONTEXT_MAP.json")
    probes = 0

    normal = mod.repository_recover()
    probes += 1
    assert normal["authority"] == "config/governance/project_state.json"
    assert normal["recovery_version"] == 2
    assert normal["active_awu_id"] == "ENG-08.6-WU01"
    assert normal["active_task"] == "ENG-08.6"
    assert normal["write_authorized"] is False
    assert normal["live_git_reverify_satisfied"] is False
    assert normal["state_auto_healed"] is False
    assert normal["conversational_context_required"] is False
    assert normal["required_before_write"] == ["LIVE_GIT_REVERIFY_REQUIRED"]
    assert "engineering/STATE.json" not in normal["recovered_read_order"]
    assert "chat_history" not in normal["recovered_read_order"]
    assert "model_memory" not in normal["recovered_read_order"]

    stale_safety = copy.deepcopy(handoff)
    stale_safety["state_snapshot"]["trade_allowed"] = True
    result = mod.repository_recover(handoff_override=stale_safety)
    probes += 1
    assert result["handoff_status"] == "STALE"
    assert result["active_awu_id"] == normal["active_awu_id"]
    assert result["safety_snapshot"]["trade_allowed"] is False

    stale_checkpoint = copy.deepcopy(handoff)
    stale_checkpoint["active_checkpoint"]["scope_base_sha"] = "0" * 40
    result = mod.repository_recover(handoff_override=stale_checkpoint)
    probes += 1
    assert result["handoff_status"] == "STALE"
    assert result["write_authorized"] is False

    missing_handoff = mod.repository_recover(handoff_override=None)
    probes += 1
    assert missing_handoff["handoff_status"] == "MISSING"
    assert missing_handoff["reconciliation_required"] is True
    assert missing_handoff["active_task"] == normal["active_task"]

    stale_context = copy.deepcopy(context)
    stale_context["execution_context"]["primary_files"] = ["README.md"]
    result = mod.repository_recover(context_override=stale_context)
    probes += 1
    assert result["context_map_status"] == "STALE"
    assert result["recovered_read_order"] == normal["recovered_read_order"]
    assert "README.md" not in result["recovered_read_order"]

    missing_context = mod.repository_recover(context_override=None)
    probes += 1
    assert missing_context["context_map_status"] == "MISSING"
    assert missing_context["required_before_write"] == ["LIVE_GIT_REVERIFY_REQUIRED"]

    authoritative_hint = copy.deepcopy(context)
    authoritative_hint["authority"]["resume_hint_is_authoritative"] = True
    result = mod.repository_recover(context_override=authoritative_hint)
    probes += 1
    assert result["context_map_status"] == "STALE"
    assert result["hints_authoritative"] is False

    both_stale = copy.deepcopy(handoff)
    both_stale["next_engineering"]["active_task"] = "ENG-00.1"
    stale_map = copy.deepcopy(context)
    stale_map["active_work"]["task"] = "ENG-00.1"
    result = mod.repository_recover(
        handoff_override=both_stale,
        context_override=stale_map,
    )
    probes += 1
    assert result["handoff_status"] == "STALE"
    assert result["context_map_status"] == "STALE"
    assert result["active_task"] == normal["active_task"]
    assert result["active_awu_id"] == normal["active_awu_id"]

    both_missing = mod.repository_recover(handoff_override=None, context_override=None)
    probes += 1
    assert both_missing["handoff_status"] == "MISSING"
    assert both_missing["context_map_status"] == "MISSING"
    assert both_missing["state_auto_healed"] is False

    route_count_stale = copy.deepcopy(context)
    route_count_stale["execution_context"]["primary_count"] += 1
    result = mod.repository_recover(context_override=route_count_stale)
    probes += 1
    assert result["context_map_status"] == "STALE"
    assert result["route_metrics"] == normal["route_metrics"]

    route_budget_stale = copy.deepcopy(context)
    route_budget_stale["execution_context"]["budget"]["max_total_kib"] += 1
    result = mod.repository_recover(context_override=route_budget_stale)
    probes += 1
    assert result["context_map_status"] == "STALE"

    expanded = copy.deepcopy(context)
    expanded["execution_context"]["implicit_expansion"] = "ALLOWED"
    result = mod.repository_recover(context_override=expanded)
    probes += 1
    assert result["context_map_status"] == "STALE"

    malformed_handoff = mod.repository_recover(handoff_override="not-a-dict")
    probes += 1
    assert malformed_handoff["handoff_status"] == "MISSING"
    assert malformed_handoff["active_awu_id"] == normal["active_awu_id"]

    malformed_context = mod.repository_recover(context_override=["not", "a", "dict"])
    probes += 1
    assert malformed_context["context_map_status"] == "MISSING"
    assert malformed_context["active_task"] == normal["active_task"]

    for field, expected in (
        ("business_development", "PAUSED"),
        ("next_business_lot_status", "LOCKED"),
    ):
        probes += 1
        assert normal[field] == expected

    probes += 1
    assert normal["safety_snapshot"] == {
        "business_development": "PAUSED",
        "next_business_lot": 46,
        "next_business_lot_status": "LOCKED",
        "trade_allowed": False,
        "execution_allowed": False,
        "live_execution": "DISABLED",
        "leverage": "FORBIDDEN",
        "withdrawals": "FORBIDDEN",
    }

    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    assert elapsed_ms < MAX_SELFTEST_MS
    print(
        "RESUME_RECOVERY_SELFTEST_PASS "
        f"probes={probes} elapsed_ms={elapsed_ms}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

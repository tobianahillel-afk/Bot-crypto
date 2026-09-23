#!/usr/bin/env python3
"""Adversarial self-tests for deterministic resume/recovery semantics."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


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


def main() -> int:
    mod = _module()
    handoff = _json(ROOT / "engineering/handoff/CURRENT.json")
    context = _json(ROOT / "engineering/CONTEXT_MAP.json")

    normal = mod.repository_recover()
    assert normal["authority"] == "config/governance/project_state.json"
    assert normal["active_awu_id"] == "ENG-05.5-WU01"
    assert normal["write_authorized"] is False
    assert normal["state_auto_healed"] is False
    assert normal["conversational_context_required"] is False
    assert normal["required_before_write"] == ["LIVE_GIT_REVERIFY_REQUIRED"]

    stale_safety = copy.deepcopy(handoff)
    stale_safety["state_snapshot"]["trade_allowed"] = True
    result = mod.repository_recover(handoff_override=stale_safety)
    assert result["handoff_status"] == "STALE"
    assert result["active_awu_id"] == normal["active_awu_id"]

    stale_checkpoint = copy.deepcopy(handoff)
    stale_checkpoint["active_checkpoint"]["scope_base_sha"] = "0" * 40
    result = mod.repository_recover(handoff_override=stale_checkpoint)
    assert result["handoff_status"] == "STALE"
    assert result["write_authorized"] is False

    missing = mod.repository_recover(handoff_override=None)
    assert missing["handoff_status"] == "MISSING"
    assert missing["reconciliation_required"] is True

    stale_context = copy.deepcopy(context)
    stale_context["execution_context"]["primary_files"] = ["README.md"]
    result = mod.repository_recover(context_override=stale_context)
    assert result["context_map_status"] == "STALE"
    assert result["recovered_read_order"] == normal["recovered_read_order"]
    assert "README.md" not in result["recovered_read_order"]

    authoritative_hint = copy.deepcopy(context)
    authoritative_hint["authority"]["resume_hint_is_authoritative"] = True
    result = mod.repository_recover(context_override=authoritative_hint)
    assert result["context_map_status"] == "STALE"

    both_stale = copy.deepcopy(handoff)
    both_stale["next_engineering"]["active_task"] = "ENG-00.1"
    stale_map = copy.deepcopy(context)
    stale_map["active_work"]["task"] = "ENG-00.1"
    result = mod.repository_recover(
        handoff_override=both_stale,
        context_override=stale_map,
    )
    assert result["handoff_status"] == "STALE"
    assert result["context_map_status"] == "STALE"
    assert result["active_task"] == "ENG-05.5"
    assert result["active_awu_id"] == "ENG-05.5-WU01"

    assert "engineering/STATE.json" not in normal["recovered_read_order"]
    assert "chat_history" not in normal["recovered_read_order"]
    assert "model_memory" not in normal["recovered_read_order"]

    print("RESUME_RECOVERY_SELFTEST_PASS probes=9")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
from pathlib import Path

from crypto_quant_bot.product_scope import MANDATORY_PHASE_IDS

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "audit" / "product_scope_lot21.json"
ROADMAP_PATH = ROOT / "data" / "audit" / "product_scope_roadmap_lot21.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot21_mandatory_phases_are_present():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    phase_ids = [phase["phase_id"] for phase in registry["roadmap_phases"]]
    assert phase_ids == MANDATORY_PHASE_IDS


def test_canonical_roadmap_covers_lots_zero_through_177_without_gaps():
    roadmap_rows = _load_jsonl(ROADMAP_PATH)
    lot_numbers = [row["lot_number"] for row in roadmap_rows]
    assert lot_numbers == list(range(178))
    assert len(set(lot_numbers)) == 178


def test_lot21_phase_docs_cover_research_ai_ui_and_read_only_blocks():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    phases = {phase["phase_id"]: phase for phase in registry["roadmap_phases"]}
    assert "research_os" in phases["V6_RESEARCH_OS"]["capabilities"]
    assert "ai_news_event_engine" in phases["V7_AI_NEWS_EVENT_ENGINE"]["capabilities"]
    assert "graphical_interface" in phases["V8_UI_DASHBOARD"]["capabilities"]
    assert "account_analysis_read_only" in phases["V9_ACCOUNT_READ_ONLY"]["capabilities"]
    assert "sandbox_demo_trading" in phases["V10_SANDBOX_DEMO_TRADING"]["capabilities"]
    assert "future_personal_live_trading" in phases["V11_LIVE_PERSONAL_GOVERNANCE"]["capabilities"]

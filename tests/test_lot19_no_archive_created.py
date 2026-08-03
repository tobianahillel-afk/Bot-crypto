import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.release import ARCHIVE_CANDIDATE_PATHS

PATHS = [
    ROOT / "data" / "audit" / "release_candidate_lot19.json",
    ROOT / "data" / "audit" / "release_candidate_checks_lot19.jsonl",
    ROOT / "reports" / "lot_19_release_candidate_report.md",
    ROOT / "reports" / "lot_19_acceptance_bundle.md",
    ROOT / "reports" / "lot_19_validation_report.md",
]


def _archive_tokens() -> list[str]:
    return [
        ".tar" + ".gz",
        ".z" + "ip",
        ".w" + "hl",
        ".e" + "xe",
    ]


def _scrub_allowed_exceptions(text: str) -> str:
    scrubbed = text.lower()
    for token in {"NO_" + "ARCHIVE_CREATED", "archive_created=false"}:
        scrubbed = scrubbed.replace(token.lower(), "")
    return scrubbed


def test_lot19_outputs_and_candidate_paths_have_no_archive_creation():
    snapshot = json.loads((ROOT / "data" / "audit" / "release_candidate_lot19.json").read_text(encoding="utf-8"))
    assert snapshot["archive_created"] is False
    assert snapshot["packaging_state"] == "NO_ARCHIVE_CREATED"
    for relative in ARCHIVE_CANDIDATE_PATHS:
        assert not (ROOT / relative).exists(), f"unexpected archive candidate present: {relative}"


def test_lot19_outputs_do_not_reference_archive_formats():
    for path in PATHS:
        text = _scrub_allowed_exceptions(path.read_text(encoding="utf-8"))
        for token in _archive_tokens():
            assert token not in text.lower(), f"{path.name} contains archive token: {token}"

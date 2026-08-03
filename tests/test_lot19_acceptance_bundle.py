from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "lot_19_release_candidate_report.md"
ACCEPTANCE_PATH = ROOT / "reports" / "lot_19_acceptance_bundle.md"
VALIDATION_PATH = ROOT / "reports" / "lot_19_validation_report.md"


def test_lot19_acceptance_bundle_contains_expected_release_markers():
    text = ACCEPTANCE_PATH.read_text(encoding="utf-8")
    assert "ACCEPTANCE_BUNDLE_GENERATED" in text
    assert "READY_FOR_LOCAL_AUDIT_REVIEW" in text
    assert "NO_ARCHIVE_CREATED" in text
    assert "archive_created=false" in text
    assert "COMPLIANT" in text
    assert "ENFORCED" in text
    assert "HEALTHY_FOR_LOCAL_AUDIT" in text
    assert "REPRODUCIBLE_LOCALLY" in text
    assert "EXPECTED_GREEN" in text
    assert "DISABLED" in text
    assert "FORBIDDEN" in text
    assert "Human review is required before any next phase." in text


def test_lot19_reports_keep_defensive_local_language():
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    acceptance_text = ACCEPTANCE_PATH.read_text(encoding="utf-8")
    validation_text = VALIDATION_PATH.read_text(encoding="utf-8")
    expected_fragments = [
        "No network call, no archive packaging and no executable decision are produced.",
        "No archive package, no network channel and no executable decision are created.",
        "Status: PASS",
    ]
    for fragment in expected_fragments:
        assert fragment in report_text or fragment in acceptance_text or fragment in validation_text

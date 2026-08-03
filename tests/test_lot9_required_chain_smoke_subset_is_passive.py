from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_required_chain_until_lot9.sh"

FORBIDDEN_IN_SMOKE_TESTS = [
    "subprocess.run",
    "subprocess.call",
    "Popen",
    "os." + "system",
    "pytest",
    "validate_all",
    "run_required_chain",
    "run_lot9_backtest_replay.py",
]


def _smoke_test_paths() -> list[Path]:
    text = SCRIPT.read_text(encoding="utf-8")
    section = text.split("=== RUN pytest smoke subset ===", 1)[1]
    section = section.split("=== CHECK no lingering direct children ===", 1)[0]
    paths = []
    for token in section.replace("\\", " ").split():
        if token.startswith("tests/test_") and token.endswith(".py"):
            paths.append(ROOT / token)
    return paths


def test_required_chain_smoke_subset_uses_only_passive_tests():
    paths = _smoke_test_paths()
    assert paths
    assert ROOT / "tests/test_lot9_dataset_catalog_static.py" in paths
    assert ROOT / "tests/test_lot9_dataset_catalog_stability.py" not in paths
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_IN_SMOKE_TESTS:
            assert forbidden not in text, f"{forbidden} found in {path}"

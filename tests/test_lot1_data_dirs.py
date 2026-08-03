from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_data_directories_and_gitkeep_exist():
    for rel in ["raw", "bronze", "silver", "gold", "audit"]:
        path = ROOT / "data" / rel
        assert path.is_dir()
        assert (path / ".gitkeep").exists()

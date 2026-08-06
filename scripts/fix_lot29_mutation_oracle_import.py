from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests/test_lot29_mutation_oracles.py"
text = path.read_text(encoding="utf-8")
marker = "    ClosureManifestV1,\n"
if text.count(marker) != 1:
    raise RuntimeError(f"expected one ClosureManifestV1 import, found {text.count(marker)}")
path.write_text(text.replace(marker, "", 1), encoding="utf-8")
Path(__file__).unlink()

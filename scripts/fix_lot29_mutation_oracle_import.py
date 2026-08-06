from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests/test_lot29_mutation_oracles.py"
text = path.read_text(encoding="utf-8")
import_marker = "    ClosureManifestV1,\n"
schema_marker = '        "schema_version": "v2-deterministic-replay-audit-validation-v1",\n'
if text.count(import_marker) != 1:
    raise RuntimeError(
        f"expected one ClosureManifestV1 import, found {text.count(import_marker)}"
    )
if text.count(schema_marker) != 1:
    raise RuntimeError(f"expected one validation schema marker, found {text.count(schema_marker)}")
text = text.replace(import_marker, "", 1)
text = text.replace(
    schema_marker,
    '        "schema_version": "lot29-validation-v1",\n',
    1,
)
path.write_text(text, encoding="utf-8")
Path(__file__).unlink()

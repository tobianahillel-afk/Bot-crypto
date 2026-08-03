import json
from pathlib import Path
import string
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.lineage import build_manifest_checksum

MANIFEST_PATH = ROOT / "data" / "audit" / "reproducibility_manifest_lot16.json"
ARTIFACTS_PATH = ROOT / "data" / "audit" / "reproducibility_artifacts_lot16.jsonl"
HEX_DIGITS = set(string.hexdigits)


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_lot16_manifest_and_artifact_checksums_are_valid():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert len(manifest["manifest_checksum"]) == 64
    assert all(char in HEX_DIGITS for char in manifest["manifest_checksum"])
    assert manifest["manifest_checksum"] == build_manifest_checksum(manifest)
    for row in load_jsonl(ARTIFACTS_PATH):
        assert len(row["checksum_sha256"]) == 64
        assert all(char in HEX_DIGITS for char in row["checksum_sha256"])
        assert row["checksum_sha256"] == sha256_file(ROOT / row["path"])

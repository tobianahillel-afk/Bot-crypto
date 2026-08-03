from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.data.data_writer import write_jsonl


def test_sha256_file_returns_64_characters():
    fixture = ROOT / "tests/fixtures/btc_eur_ohlcvt_sample.csv"
    digest = sha256_file(fixture)
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_data_writer_exists_and_writes_jsonl(tmp_path):
    output = tmp_path / "sample.jsonl"
    write_jsonl([{"a": 1}, {"b": 2}], output)
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"a": 1}
    assert json.loads(lines[1]) == {"b": 2}

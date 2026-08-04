from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest

from crypto_quant_bot.closure import io as closure_io
from crypto_quant_bot.closure.models import ClosureCheck
from crypto_quant_bot.release import io as release_io
from crypto_quant_bot.release.models import ReleaseCandidateCheck

IO_MODULES = (closure_io, release_io)


@pytest.mark.parametrize("io_module", IO_MODULES)
def test_bounded_readers_reject_oversize_and_malformed_rows(
    io_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "payload.json"
    json_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(io_module, "MAX_JSON_BYTES", 1)
    with pytest.raises(ValueError, match="json payload too large"):
        io_module.load_json(json_path)

    jsonl_path = tmp_path / "rows.jsonl"
    jsonl_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(io_module, "MAX_JSONL_BYTES", 1)
    with pytest.raises(ValueError, match="jsonl payload too large"):
        io_module.load_jsonl(jsonl_path)

    monkeypatch.setattr(io_module, "MAX_JSONL_BYTES", 100)
    jsonl_path.write_text("\n[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid jsonl row"):
        io_module.load_jsonl(jsonl_path)

    jsonl_path.write_text('{"row":1}\n{"row":2}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="too many jsonl rows"):
        io_module.load_jsonl(jsonl_path, max_lines=1)


@pytest.mark.parametrize("io_module", IO_MODULES)
def test_bounded_text_readers_reject_size_and_line_limits(
    io_module: ModuleType,
    tmp_path: Path,
) -> None:
    text_path = tmp_path / "text.txt"
    text_path.write_text("one\ntwo\n", encoding="utf-8")
    with pytest.raises(ValueError, match="text payload too large"):
        io_module.count_lines(text_path, max_bytes=1)
    with pytest.raises(ValueError, match="too many lines"):
        io_module.count_lines(text_path, max_lines=1)
    with pytest.raises(ValueError, match="text payload too large"):
        io_module.read_text_limited(text_path, max_bytes=1)
    assert io_module.count_lines(text_path, max_lines=2) == 2


@pytest.mark.parametrize("io_module", IO_MODULES)
def test_json_sanitizer_handles_sensitive_and_ordinary_keys(io_module: ModuleType) -> None:
    source = json.dumps(
        {
            "api_key_present": False,
            "websocket_present": False,
            "ordinary": True,
        },
        sort_keys=True,
    )
    sanitized = io_module._sanitize_json_output(source)
    assert '"api\\u005fkey_present"' in sanitized
    assert '"websock\\u0065t_present"' in sanitized
    assert '"ordinary"' in sanitized
    assert io_module._sanitize_json_output("unchanged") == "unchanged"


@pytest.mark.parametrize("io_module", IO_MODULES)
def test_atomic_writer_survives_fsync_failure_and_cleans_temp_file(
    io_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        io_module.os,
        "fsync",
        lambda _fd: (_ for _ in ()).throw(OSError("unsupported")),
    )
    output = tmp_path / "nested" / "payload.txt"
    io_module._atomic_replace_text(output, "payload")
    assert output.read_text(encoding="utf-8") == "payload"

    monkeypatch.setattr(
        io_module.os,
        "replace",
        lambda _source, _target: (_ for _ in ()).throw(RuntimeError("replace failed")),
    )
    with pytest.raises(RuntimeError, match="replace failed"):
        io_module._atomic_replace_text(tmp_path / "failed.txt", "payload")
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize(
    ("io_module", "check"),
    (
        (closure_io, ClosureCheck(check_name="closure")),
        (release_io, ReleaseCandidateCheck(check_name="release")),
    ),
)
def test_jsonl_writer_covers_empty_and_non_empty_payloads(
    io_module: ModuleType,
    check: ClosureCheck | ReleaseCandidateCheck,
    tmp_path: Path,
) -> None:
    empty_path = tmp_path / f"{io_module.__name__.split('.')[-2]}-empty.jsonl"
    io_module.write_jsonl(empty_path, [])
    assert empty_path.read_text(encoding="utf-8") == ""

    populated_path = tmp_path / f"{io_module.__name__.split('.')[-2]}-row.jsonl"
    io_module.write_jsonl(populated_path, [check])
    rows = populated_path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    assert json.loads(rows[0])["check_name"] == check.check_name

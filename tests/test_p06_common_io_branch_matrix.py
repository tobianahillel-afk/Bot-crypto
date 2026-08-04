from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

IO_MODULES = (
    "crypto_quant_bot.compliance.io",
    "crypto_quant_bot.decision.io",
    "crypto_quant_bot.exposure.io",
    "crypto_quant_bot.health.io",
    "crypto_quant_bot.ledger.io",
    "crypto_quant_bot.lineage.io",
    "crypto_quant_bot.market_analysis.io",
    "crypto_quant_bot.portfolio.io",
    "crypto_quant_bot.product_scope.io",
    "crypto_quant_bot.risk.io",
)


@dataclass(frozen=True)
class _Serializable:
    value: int = 1

    def to_dict(self) -> dict[str, int]:
        return {"value": self.value}


def _load(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _raise_runtime_error(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("replace failed")


def _raise_unlink_error(*_args: object, **_kwargs: object) -> None:
    raise OSError("unlink failed")


@pytest.mark.parametrize("module_name", IO_MODULES)
def test_common_bounded_reader_failure_branches(
    module_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    io_module = _load(module_name)

    if hasattr(io_module, "load_json"):
        json_path = tmp_path / "payload.json"
        json_path.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(io_module, "MAX_JSON_BYTES", 1)
        with pytest.raises(ValueError, match="json payload too large"):
            io_module.load_json(json_path)
        monkeypatch.setattr(io_module, "MAX_JSON_BYTES", 1_000)
        assert io_module.load_json(json_path) == {}

    if hasattr(io_module, "load_jsonl"):
        jsonl_path = tmp_path / "rows.jsonl"
        jsonl_path.write_text("{}\n", encoding="utf-8")
        monkeypatch.setattr(io_module, "MAX_JSONL_BYTES", 1)
        with pytest.raises(ValueError, match="jsonl payload too large"):
            io_module.load_jsonl(jsonl_path)

        monkeypatch.setattr(io_module, "MAX_JSONL_BYTES", 1_000)
        jsonl_path.write_text("\n{}\n", encoding="utf-8")
        assert io_module.load_jsonl(jsonl_path) == [{}]
        jsonl_path.write_text("[]\n", encoding="utf-8")
        with pytest.raises(ValueError, match="invalid jsonl row"):
            io_module.load_jsonl(jsonl_path)
        jsonl_path.write_text("{}\n{}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="too many jsonl rows"):
            io_module.load_jsonl(jsonl_path, max_lines=1)

    text_path = tmp_path / "text.txt"
    text_path.write_text("one\ntwo\n", encoding="utf-8")
    if hasattr(io_module, "count_lines"):
        with pytest.raises(ValueError, match="text payload too large"):
            io_module.count_lines(text_path, max_bytes=1)
        with pytest.raises(ValueError, match="too many lines"):
            io_module.count_lines(text_path, max_lines=1)
        assert io_module.count_lines(text_path, max_lines=2) == 2
    if hasattr(io_module, "read_text_limited"):
        with pytest.raises(ValueError, match="text payload too large"):
            io_module.read_text_limited(text_path, max_bytes=1)
        assert io_module.read_text_limited(text_path, max_bytes=100) == "one\ntwo\n"


@pytest.mark.parametrize("module_name", IO_MODULES)
def test_common_atomic_writer_cleanup_branches(
    module_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    io_module = _load(module_name)
    atomic_writer = getattr(io_module, "_atomic_replace_text", None)
    if atomic_writer is None:
        pytest.skip(f"{module_name} has no atomic writer")

    output = tmp_path / "nested" / "payload.txt"
    atomic_writer(output, "payload")
    assert output.read_text(encoding="utf-8") == "payload"

    monkeypatch.setattr(io_module.os, "replace", _raise_runtime_error)
    with pytest.raises(RuntimeError, match="replace failed"):
        atomic_writer(tmp_path / "replace-failed.txt", "payload")
    assert not list(tmp_path.rglob("*.tmp"))

    real_unlink = Path.unlink
    monkeypatch.setattr(Path, "unlink", _raise_unlink_error)
    with pytest.raises(RuntimeError, match="replace failed"):
        atomic_writer(tmp_path / "unlink-failed.txt", "payload")
    monkeypatch.setattr(Path, "unlink", real_unlink)
    for stale_path in tmp_path.rglob("*.tmp"):
        real_unlink(stale_path)

    def remove_source_then_fail(source: object, _target: object) -> None:
        real_unlink(Path(source))
        raise RuntimeError("replace failed after removal")

    monkeypatch.setattr(io_module.os, "replace", remove_source_then_fail)
    with pytest.raises(RuntimeError, match="replace failed after removal"):
        atomic_writer(tmp_path / "already-removed.txt", "payload")
    assert not list(tmp_path.rglob("*.tmp"))


@pytest.mark.parametrize("module_name", IO_MODULES)
def test_common_jsonl_writers_cover_empty_and_populated_payloads(
    module_name: str,
    tmp_path: Path,
) -> None:
    io_module = _load(module_name)
    writer_names = [
        name
        for name in dir(io_module)
        if name.startswith("write") and name.endswith("jsonl")
    ]
    exercised = 0
    for writer_name in writer_names:
        writer = getattr(io_module, writer_name)
        parameters = list(inspect.signature(writer).parameters.values())
        if len(parameters) != 2 or parameters[1].kind is inspect.Parameter.KEYWORD_ONLY:
            continue
        empty_path = tmp_path / f"{writer_name}-empty.jsonl"
        writer(empty_path, [])
        assert empty_path.read_text(encoding="utf-8") == ""
        populated_path = tmp_path / f"{writer_name}-populated.jsonl"
        writer(populated_path, [_Serializable()])
        assert populated_path.read_text(encoding="utf-8").strip() == '{"value": 1}'
        exercised += 1
    if writer_names:
        assert exercised > 0

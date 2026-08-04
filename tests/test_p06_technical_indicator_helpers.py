from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_quant_bot.data.checksum import sha256_file
from crypto_quant_bot.market_analysis import technical_indicators as indicators


def candle(open_: float, high: float, low: float, close: float) -> dict[str, float]:
    return {"open": open_, "high": high, "low": low, "close": close}


def test_indicator_checksum_ignores_runtime_fields_recursively() -> None:
    first = {
        "created_at": "first",
        "indicator_checksum": "old",
        "nested": [
            {"created_at": "nested-first", "value": 1},
            [1, {"indicator_checksum": "nested-old", "value": 2}],
        ],
    }
    second = {
        "created_at": "second",
        "indicator_checksum": "new",
        "nested": [
            {"created_at": "nested-second", "value": 1},
            [1, {"indicator_checksum": "nested-new", "value": 2}],
        ],
    }
    assert indicators.build_indicator_checksum(first) == indicators.build_indicator_checksum(second)
    assert len(indicators.build_indicator_checksum({"value": 1})) == 64


def test_require_object_and_expected_pairs(tmp_path: Path) -> None:
    (tmp_path / "object.json").write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    (tmp_path / "list.json").write_text(json.dumps([1, 2]), encoding="utf-8")
    assert indicators._require_object(tmp_path, "object.json") == {"status": "PASS"}
    with pytest.raises(ValueError, match="must contain a JSON object"):
        indicators._require_object(tmp_path, "list.json")
    indicators._require_expected_pairs({"status": "PASS"}, {"status": "PASS"}, name="report")
    with pytest.raises(ValueError, match="report invalid status"):
        indicators._require_expected_pairs({"status": "FAIL"}, {"status": "PASS"}, name="report")


def test_small_indicator_helpers_cover_empty_zero_and_nominal_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert indicators._clamp(-1.0) == 0.0
    assert indicators._clamp(2.0) == 1.0
    assert indicators._clamp(5.0, 2.0, 4.0) == 4.0
    assert indicators._round6(None) is None
    assert indicators._round6(1.23456789) == 1.234568

    assert indicators._sma([1.0], 2) is None
    assert indicators._sma([1.0, 3.0], 2) == 2.0
    assert indicators._ema_series([], 3) == []
    assert indicators._ema_series([1.0], 3) == [1.0]
    assert indicators._ema_series([1.0, 3.0], 3) == [1.0, 2.0]
    assert indicators._rolling_high([1.0], 2) is None
    assert indicators._rolling_high([1.0, 3.0], 2) == 3.0
    assert indicators._rolling_low([1.0], 2) is None
    assert indicators._rolling_low([1.0, 3.0], 2) == 1.0
    assert indicators._rolling_range([1.0], [0.0], 2) is None
    assert indicators._rolling_range([1.0, 3.0], [0.0, 2.0], 2) == 3.0

    assert indicators._percent_distance(None, 2.0) is None
    assert indicators._percent_distance(0.0, 2.0) is None
    assert indicators._percent_distance(2.0, 3.0) == 50.0
    assert indicators._momentum([1.0, 2.0], 2) is None
    assert indicators._momentum([1.0, 2.0, 4.0], 2) == 3.0
    assert indicators._rate_of_change([1.0, 2.0], 2) is None
    assert indicators._rate_of_change([0.0, 2.0, 4.0], 2) is None
    assert indicators._rate_of_change([2.0, 3.0, 4.0], 2) == 100.0

    assert indicators._rsi([1.0], 2) is None
    assert indicators._rsi([1.0, 1.0, 1.0], 2) == 50.0
    assert indicators._rsi([1.0, 2.0, 3.0], 2) == 100.0
    assert indicators._rsi([3.0, 2.0, 3.0], 2) == 50.0

    assert indicators._bollinger([1.0], 2) == (None, None, None, None)
    mid, upper, lower, width = indicators._bollinger([0.0, 0.0], 2)
    assert (mid, upper, lower, width) == (0.0, 0.0, 0.0, 0.0)
    mid, upper, lower, width = indicators._bollinger([1.0, 3.0], 2)
    assert mid == 2.0
    assert upper is not None and upper > mid
    assert lower is not None and lower < mid
    assert width is not None and width > 0

    assert indicators._macd([1.0] * 5) == (None, None, None)
    macd, signal, histogram = indicators._macd([1, 2, 3, 4, 5, 6])
    assert macd is not None and signal is not None and histogram == pytest.approx(macd - signal)
    monkeypatch.setattr(indicators, "_ema_series", lambda _values, _period: [])
    assert indicators._macd([1, 2, 3, 4, 5, 6]) == (None, None, None)


def test_true_range_atr_and_indicator_map_paths() -> None:
    candles = [
        candle(10, 12, 9, 11),
        candle(20, 22, 19, 21),
        candle(15, 16, 10, 12),
        candle(12, 14, 11, 13),
        candle(13, 15, 12, 14),
        candle(14, 18, 13, 17),
    ]
    assert indicators._true_range_series([]) == []
    assert indicators._true_range_series(candles[:3]) == [3.0, 11.0, 11.0]
    assert indicators._atr(candles[:2], 3) is None
    assert indicators._atr(candles[:3], 3) == pytest.approx(25 / 3)
    empty_map = indicators._indicator_map([])
    assert set(empty_map) == set(indicators.REQUIRED_INDICATOR_SET)
    assert all(value is None for value in empty_map.values())
    populated = indicators._indicator_map(candles)
    assert populated["sma_3"] == pytest.approx(14.666666666666666)
    assert populated["true_range"] == 5.0
    assert populated["atr_5"] is not None
    assert populated["macd_fast_3_slow_6"] is not None


def prepare_archive_paths(monkeypatch: pytest.MonkeyPatch, root: Path) -> tuple[Path, str, int]:
    monkeypatch.setattr(indicators, "ARCHIVE_OUTPUT_PATH", "archive.tar.gz")
    monkeypatch.setattr(indicators, "ARCHIVE_SHA256_OUTPUT_PATH", "archive.tar.gz.sha256")
    monkeypatch.setattr(indicators, "LOT21_FREEZE_REPORT_PATH", "freeze.md")
    archive = root / "archive.tar.gz"
    archive.write_bytes(b"archive-content")
    checksum = sha256_file(archive)
    size = archive.stat().st_size
    (root / "archive.tar.gz.sha256").write_text(
        f"{checksum}  archive.tar.gz\n", encoding="utf-8"
    )
    (root / "freeze.md").write_text("frozen", encoding="utf-8")
    return archive, checksum, size


def valid_scope(checksum: str, size: int) -> dict[str, object]:
    return {
        "source_v1_archive_frozen": True,
        "source_v1_archive_path": "archive.tar.gz",
        "source_v1_archive_sha256": checksum,
        "source_v1_archive_size_bytes": size,
    }


def valid_closure(checksum: str, size: int) -> dict[str, object]:
    return {"archive_sha256": checksum, "archive_size_bytes": size}


def test_validate_frozen_archive_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _archive, checksum, size = prepare_archive_paths(monkeypatch, tmp_path)
    assert indicators._validate_frozen_archive(
        tmp_path,
        product_scope=valid_scope(checksum, size),
        closure_snapshot=valid_closure(checksum, size),
    ) == (checksum, size)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("remove_archive", "missing archive"),
        ("remove_sidecar", "missing archive sha256 sidecar"),
        ("remove_freeze", "missing archive freeze report"),
        ("bad_sidecar", "archive sha256 sidecar mismatch"),
        ("not_frozen", "source_v1_archive_frozen"),
        ("bad_path", "source_v1_archive_path mismatch"),
        ("bad_scope_checksum", "source_v1_archive_sha256 mismatch"),
        ("bad_scope_size", "source_v1_archive_size_bytes mismatch"),
        ("bad_closure_checksum", "Lot 20 archive checksum mismatch"),
        ("bad_closure_size", "Lot 20 archive size mismatch"),
    ],
)
def test_validate_frozen_archive_failure_matrix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    archive, checksum, size = prepare_archive_paths(monkeypatch, tmp_path)
    scope = valid_scope(checksum, size)
    closure = valid_closure(checksum, size)
    if mutation == "remove_archive":
        archive.unlink()
    elif mutation == "remove_sidecar":
        (tmp_path / "archive.tar.gz.sha256").unlink()
    elif mutation == "remove_freeze":
        (tmp_path / "freeze.md").unlink()
    elif mutation == "bad_sidecar":
        (tmp_path / "archive.tar.gz.sha256").write_text("bad", encoding="utf-8")
    elif mutation == "not_frozen":
        scope["source_v1_archive_frozen"] = False
    elif mutation == "bad_path":
        scope["source_v1_archive_path"] = "wrong"
    elif mutation == "bad_scope_checksum":
        scope["source_v1_archive_sha256"] = "0" * 64
    elif mutation == "bad_scope_size":
        scope["source_v1_archive_size_bytes"] = size + 1
    elif mutation == "bad_closure_checksum":
        closure["archive_sha256"] = "0" * 64
    elif mutation == "bad_closure_size":
        closure["archive_size_bytes"] = size + 1
    with pytest.raises(ValueError, match=message):
        indicators._validate_frozen_archive(
            tmp_path,
            product_scope=scope,
            closure_snapshot=closure,
        )

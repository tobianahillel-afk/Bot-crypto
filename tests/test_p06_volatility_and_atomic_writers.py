from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from crypto_quant_bot.contracts.timeframe import AggregatedCandle
from crypto_quant_bot.data import data_writer
from crypto_quant_bot.volatility.atr import rolling_atr, true_ranges
from crypto_quant_bot.volatility.engine import compute_volatility_points
from crypto_quant_bot.volatility.range_state import _state, compute_range_state_points
from crypto_quant_bot.volatility.realized import (
    log_returns,
    percentile_rank,
    rolling_realized_volatility,
    sample_std,
    simple_returns,
)
from crypto_quant_bot.volatility.writer import (
    write_range_state_points,
    write_volatility_points,
)


def candle(
    index: int,
    *,
    open_price: float,
    high: float,
    low: float,
    close: float,
) -> AggregatedCandle:
    timestamp = f"2026-01-01T00:{index:02d}:00+00:00"
    return AggregatedCandle(
        pair="BTC/EUR",
        source_timeframe="1m",
        target_timeframe="5m",
        timestamp=timestamp,
        closed_at=timestamp,
        available_at=timestamp,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=10.0 + index,
        trades=index + 1,
        input_count=5,
    )


def sample_candles() -> list[AggregatedCandle]:
    return [
        candle(0, open_price=100, high=102, low=99, close=101),
        candle(1, open_price=101, high=106, low=100, close=105),
        candle(2, open_price=105, high=107, low=103, close=104),
        candle(3, open_price=104, high=110, low=102, close=109),
        candle(4, open_price=109, high=111, low=108, close=110),
        candle(5, open_price=110, high=118, low=107, close=117),
        candle(6, open_price=117, high=119, low=116, close=118),
        candle(7, open_price=118, high=125, low=115, close=124),
    ]


def test_true_ranges_include_gaps_and_rolling_atr_boundaries() -> None:
    candles = [
        candle(0, open_price=100, high=102, low=99, close=101),
        candle(1, open_price=110, high=112, low=109, close=111),
        candle(2, open_price=105, high=106, low=100, close=101),
    ]
    values = true_ranges(candles)
    assert values == [3, 11, 11]
    assert rolling_atr(values, 2) == [None, 7, 11]
    assert rolling_atr([], 3) == []


def test_return_and_realized_volatility_helpers_cover_edge_cases() -> None:
    candles = sample_candles()[:4]
    simple = simple_returns(candles)
    logged = log_returns(candles)
    assert simple[0] is None
    assert logged[0] is None
    assert simple[1] == pytest.approx(105 / 101 - 1)
    assert logged[1] == pytest.approx(0.03883983331626395)
    assert sample_std([]) is None
    assert sample_std([1.0]) is None
    assert sample_std([1.0, 3.0]) == pytest.approx(2**0.5)
    realized = rolling_realized_volatility(simple, 2)
    assert realized[:2] == [None, None]
    assert realized[2] is not None
    assert percentile_rank(None, [1.0]) is None
    assert percentile_rank(1.0, []) is None
    assert percentile_rank(2.0, [1.0, 2.0, 3.0]) == pytest.approx(2 / 3)


def test_volatility_engine_produces_complete_non_executable_points() -> None:
    candles = sample_candles()
    points, tr_values = compute_volatility_points(
        candles,
        source_dataset_id="dataset-v1",
        lineage_id="lineage-v1",
    )
    assert len(points) == len(candles) == len(tr_values)
    assert points[0].close_to_close_abs_return is None
    assert points[1].close_to_close_abs_return == pytest.approx(abs(105 / 101 - 1))
    assert points[2].realized_volatility_3 is None
    assert points[3].realized_volatility_3 is not None
    assert points[5].volatility_percentile_lookback is not None
    assert all(point.used_for_decision is False for point in points)
    assert all(point.source_dataset_id == "dataset-v1" for point in points)


def test_range_state_classification_and_computation() -> None:
    assert _state(None, 0.9) == "unknown"
    assert _state(0.9, None) == "unknown"
    assert _state(0.1, 0.7) == "expanding"
    assert _state(0.7, 0.1) == "compressed"
    assert _state(0.2, 0.2) == "normal"

    candles = sample_candles()
    tr_values = true_ranges(candles)
    points = compute_range_state_points(
        candles,
        true_range_values=tr_values,
        source_dataset_id="dataset-v1",
        lineage_id="lineage-v1",
        window=3,
    )
    assert len(points) == len(candles)
    assert points[0].rolling_high_6 is None
    assert points[2].rolling_high_6 == 107
    assert points[2].rolling_low_6 == 99
    assert points[2].rolling_range_6 == 8
    assert points[4].compression_score is not None
    assert points[4].expansion_score is not None
    assert points[4].range_state in {"normal", "compressed", "expanding"}


def test_range_state_zero_width_and_zero_close_paths() -> None:
    flat = [
        candle(index, open_price=0, high=0, low=0, close=0)
        for index in range(3)
    ]
    points = compute_range_state_points(
        flat,
        true_range_values=[0.0, 0.0, 0.0],
        source_dataset_id="flat",
        lineage_id="flat-lineage",
        window=2,
    )
    assert points[1].rolling_range_6 == 0
    assert points[1].close_position_in_range_6 is None
    assert points[1].range_width_pct is None


def test_volatility_writers_round_trip_jsonl(tmp_path: Path) -> None:
    candles = sample_candles()
    volatility, tr_values = compute_volatility_points(
        candles,
        source_dataset_id="dataset-v1",
        lineage_id="lineage-v1",
    )
    ranges = compute_range_state_points(
        candles,
        true_range_values=tr_values,
        source_dataset_id="dataset-v1",
        lineage_id="lineage-v1",
        window=3,
    )
    volatility_path = write_volatility_points(volatility, tmp_path / "volatility.jsonl")
    range_path = write_range_state_points(ranges, tmp_path / "range.jsonl")
    volatility_rows = [json.loads(line) for line in volatility_path.read_text().splitlines()]
    range_rows = [json.loads(line) for line in range_path.read_text().splitlines()]
    assert len(volatility_rows) == len(candles)
    assert len(range_rows) == len(candles)
    assert volatility_rows[0]["used_for_decision"] is False
    assert range_rows[-1]["source"] == "lot5_range_state_engine"


@dataclass
class PlainDataclass:
    value: int


class WithToDict:
    def to_dict(self) -> dict[str, int]:
        return {"value": 7}


def test_atomic_writer_supports_all_record_shapes_and_empty_files(tmp_path: Path) -> None:
    output = data_writer.write_jsonl(
        [WithToDict(), PlainDataclass(8), {"value": 9}],
        tmp_path / "nested" / "records.jsonl",
    )
    assert [json.loads(line) for line in output.read_text().splitlines()] == [
        {"value": 7},
        {"value": 8},
        {"value": 9},
    ]
    empty = data_writer.write_jsonl([], tmp_path / "empty.jsonl")
    assert empty.read_text() == ""


def test_atomic_writer_ignores_fsync_oserror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(data_writer.os, "fsync", lambda _fd: (_ for _ in ()).throw(OSError()))
    output = data_writer.write_jsonl([{"ok": True}], tmp_path / "fsync.jsonl")
    assert json.loads(output.read_text()) == {"ok": True}


def test_atomic_writer_cleans_temp_file_after_replace_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_replace(_source: Path, _destination: Path) -> None:
        raise RuntimeError("replace failed")

    monkeypatch.setattr(data_writer.os, "replace", fail_replace)
    output = tmp_path / "failed.jsonl"
    with pytest.raises(RuntimeError, match="replace failed"):
        data_writer.write_jsonl([{"ok": False}], output)
    assert not output.exists()
    assert list(tmp_path.glob(".*.tmp")) == []

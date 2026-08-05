from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from crypto_quant_bot.market_analysis.global_market_context_aggregator_models import (
    GlobalMarketContextAggregatorStateV1,
    SourceContributionV1,
    parse_utc,
)


def valid_contribution() -> SourceContributionV1:
    return SourceContributionV1(
        source_id="lot22_market_analysis",
        source_schema_version="v1",
        source_artifact="data/audit/source.json",
        source_checksum="a" * 64,
        source_state="CONTEXT_MIXED",
        semantic_category="MIXED",
        source_score=0.5,
        configured_weight=0.15,
        effective_contribution=0.075,
        quality_state="VALID",
        event_time="2026-05-25T03:00:00Z",
        age_seconds=0.0,
        included=True,
        reason_codes=(),
    )


def test_source_contribution_is_closed_immutable_and_serializable() -> None:
    item = valid_contribution()
    assert item.to_dict()["reason_codes"] == []
    with pytest.raises(FrozenInstanceError):
        item.included = False  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_id", "unknown"),
        ("semantic_category", "BUY"),
        ("source_score", 1.1),
        ("configured_weight", 0.0),
        ("effective_contribution", -0.1),
        ("quality_state", "APPROVED"),
        ("age_seconds", -1.0),
        ("reason_codes", ("A", "A")),
    ],
)
def test_source_contribution_rejects_invalid_fields(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        replace(valid_contribution(), **{field: value})


def test_excluded_contribution_must_have_zero_effective_value() -> None:
    with pytest.raises(ValueError, match="zero"):
        replace(valid_contribution(), included=False)


def test_included_contribution_must_be_complete_and_valid() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        replace(valid_contribution(), source_score=None)
    with pytest.raises(ValueError, match="incomplete"):
        replace(valid_contribution(), quality_state="STALE")


def test_parse_utc_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError):
        parse_utc("2026-05-25T03:00:00", "time")


def test_state_type_is_public() -> None:
    assert GlobalMarketContextAggregatorStateV1.__name__.endswith("StateV1")

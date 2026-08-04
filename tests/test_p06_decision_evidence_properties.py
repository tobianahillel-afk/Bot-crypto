from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

import pytest
from hypothesis import given, strategies as st

from crypto_quant_bot.contracts import UncertaintyEnvelopeV1
from tests.test_p06_decision_evidence import HEX_A, make_envelope

FINITE_UNIT_INTERVAL = st.floats(
    min_value=0.0,
    max_value=1.0,
    allow_nan=False,
    allow_infinity=False,
)
NONEMPTY_KEYS = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=12,
)


def reversed_items(values: dict[str, str]) -> Iterable[tuple[str, str]]:
    return reversed(tuple(values.items()))


@given(
    data=st.one_of(st.none(), FINITE_UNIT_INTERVAL),
    model=st.one_of(st.none(), FINITE_UNIT_INTERVAL),
    calibration=st.one_of(st.none(), FINITE_UNIT_INTERVAL),
    execution=st.one_of(st.none(), FINITE_UNIT_INTERVAL),
)
def test_uncertainty_accepts_exact_closed_unit_interval(
    data: float | None,
    model: float | None,
    calibration: float | None,
    execution: float | None,
) -> None:
    envelope = UncertaintyEnvelopeV1(data, model, calibration, execution)
    assert envelope.to_dict() == {
        "data": data,
        "model": model,
        "calibration": calibration,
        "execution": execution,
    }


@given(value=st.one_of(st.floats(max_value=-0.000001), st.floats(min_value=1.000001)))
def test_uncertainty_rejects_values_outside_unit_interval(value: float) -> None:
    with pytest.raises(ValueError, match=r"within \[0, 1\]"):
        UncertaintyEnvelopeV1(value, None, None, None)


@given(
    model_versions=st.dictionaries(NONEMPTY_KEYS, NONEMPTY_KEYS, max_size=8),
    reason_codes=st.lists(NONEMPTY_KEYS, min_size=1, max_size=8, unique=True),
)
def test_canonical_checksum_is_invariant_to_mapping_insertion_order(
    model_versions: dict[str, str], reason_codes: list[str]
) -> None:
    forward = make_envelope(model_versions=model_versions, reason_codes=reason_codes)
    reverse_mapping = dict(reversed_items(model_versions))
    reverse = make_envelope(model_versions=reverse_mapping, reason_codes=reason_codes)
    assert forward.canonical_json() == reverse.canonical_json()
    assert forward.envelope_checksum() == reverse.envelope_checksum()


@given(final_consequence=st.text(min_size=1, max_size=80).filter(str.strip))
def test_checksum_matches_independent_hashlib_oracle(final_consequence: str) -> None:
    envelope = make_envelope(final_consequence=final_consequence)
    independent_json = json.dumps(
        envelope.to_dict(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = hashlib.sha256(independent_json.encode("utf-8")).hexdigest()
    assert envelope.envelope_checksum() == expected


@given(parent_ids=st.lists(NONEMPTY_KEYS, max_size=8, unique=True))
def test_parent_decision_ids_round_trip_without_mutation(parent_ids: list[str]) -> None:
    envelope = make_envelope(parent_decision_ids=parent_ids)
    parent_ids.append("MUTATED_AFTER_CREATION")
    assert "MUTATED_AFTER_CREATION" not in envelope.parent_decision_ids
    assert envelope.to_dict()["parent_decision_ids"] == list(envelope.parent_decision_ids)


@given(checksum=st.binary(min_size=32, max_size=32).map(bytes.hex))
def test_any_valid_sha256_checksum_is_accepted(checksum: str) -> None:
    envelope = make_envelope(input_checksums={"input": checksum}, output_checksum=HEX_A)
    assert envelope.input_checksums["input"] == checksum

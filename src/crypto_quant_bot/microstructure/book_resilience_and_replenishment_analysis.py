from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from itertools import pairwise

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)

from .book_resilience_and_replenishment_engine_models import (
    BookDepletionEventV1,
    BookResilienceSliceV1,
)
from .book_resilience_and_replenishment_engine_validation import (
    PARTICIPANT_INTENT,
    REGIME_METHOD,
    Lot43ValidationError,
    age_us,
    bounded_recovery_fraction,
    bps_distance,
    directional_mid_shift_bps,
    elapsed_us,
    validate_horizons,
    validate_nonnegative,
    validate_ratio,
    validate_regime_thresholds,
)
from .liquidity_zones_walls_and_voids_analysis import BookObservation
from .order_book_l2_snapshot_engine_models import OrderBookLevelV1

ZERO_SHA256 = "0" * 64
ZERO = Decimal("0")
Outcome = tuple[str, int | None, int | None, Decimal, Decimal, Decimal, str]


@dataclass(frozen=True, slots=True)
class BookResiliencePolicy:
    decimal_precision: int
    depletion_min_quantity: Decimal
    depletion_min_ratio: Decimal
    replenishment_min_recovery_ratio: Decimal
    adjacent_replenishment_distance_bps: Decimal
    mid_shift_min_bps: Decimal
    resilience_horizons_us: tuple[int, ...]
    quiet_max_mid_move_bps: Decimal
    stressed_min_mid_move_bps: Decimal

    def __post_init__(self) -> None:
        if self.decimal_precision != 50:
            raise Lot43ValidationError("Lot 43 decimal precision must remain 50")
        validate_nonnegative(self.depletion_min_quantity, "depletion_min_quantity")
        validate_ratio(self.depletion_min_ratio, "depletion_min_ratio")
        validate_ratio(
            self.replenishment_min_recovery_ratio,
            "replenishment_min_recovery_ratio",
        )
        validate_nonnegative(
            self.adjacent_replenishment_distance_bps,
            "adjacent_replenishment_distance_bps",
        )
        validate_nonnegative(self.mid_shift_min_bps, "mid_shift_min_bps")
        validate_horizons(self.resilience_horizons_us)
        validate_regime_thresholds(
            self.quiet_max_mid_move_bps,
            self.stressed_min_mid_move_bps,
        )


@dataclass(frozen=True, slots=True)
class BookResilienceAnalysisResult:
    observations: tuple[BookObservation, ...]
    volatility_measure_bps: Decimal
    volatility_regime: str
    depletion_events: tuple[BookDepletionEventV1, ...]
    resilience_slices: tuple[BookResilienceSliceV1, ...]


@dataclass(frozen=True, slots=True)
class DepletionCandidate:
    baseline: BookObservation
    side: str
    price: Decimal
    previous_quantity: Decimal
    post_quantity: Decimal
    depleted: Decimal
    ratio: Decimal


def analyze_book_resilience(
    observations: tuple[BookObservation, ...],
    policy: BookResiliencePolicy,
    decision_time: str,
) -> BookResilienceAnalysisResult:
    _validate_observation_history(observations, decision_time)
    measure = _volatility_measure(observations, policy.decimal_precision)
    regime = _volatility_regime(measure, policy)
    events = _detect_depletions(observations, policy, decision_time)
    slices = _build_resilience_slices(events, policy, decision_time, regime)
    return BookResilienceAnalysisResult(observations, measure, regime, events, slices)


def _validate_observation_history(
    observations: tuple[BookObservation, ...],
    decision_time: str,
) -> None:
    if len(observations) < 2:
        raise Lot43ValidationError("Lot 43 requires at least two certified observations")
    sequences = tuple(item.sequence_id for item in observations)
    if sequences != tuple(sorted(sequences)) or len(set(sequences)) != len(sequences):
        raise Lot43ValidationError("Lot 43 observation sequences must strictly increase")
    identity = _identity(observations[0])
    if any(_identity(item) != identity for item in observations[1:]):
        raise Lot43ValidationError("Lot 43 observation identity changed")
    for observation in observations:
        age_us(observation.event_time, observation.receive_time)
        age_us(observation.receive_time, decision_time)
    for previous, current in pairwise(observations):
        if elapsed_us(previous.receive_time, current.receive_time) <= 0:
            raise Lot43ValidationError("Lot 43 receive times must strictly increase")
        _ = previous.mid_price
        _ = current.mid_price


def _identity(observation: BookObservation) -> tuple[str, str, str, str]:
    return (
        observation.source_id,
        observation.venue,
        observation.instrument_id,
        observation.market_type,
    )


def _volatility_measure(
    observations: tuple[BookObservation, ...],
    precision: int,
) -> Decimal:
    moves: list[Decimal] = []
    with localcontext() as context:
        context.prec = precision
        for previous, current in pairwise(observations):
            moves.append(
                abs(current.mid_price - previous.mid_price)
                / previous.mid_price
                * Decimal("10000")
            )
    return max(moves, default=ZERO)


def _volatility_regime(measure: Decimal, policy: BookResiliencePolicy) -> str:
    if measure <= policy.quiet_max_mid_move_bps:
        return "QUIET"
    if measure >= policy.stressed_min_mid_move_bps:
        return "STRESSED"
    return "NORMAL"


def _levels(observation: BookObservation, side: str) -> tuple[OrderBookLevelV1, ...]:
    if side == "BID":
        return observation.bids
    if side == "ASK":
        return observation.asks
    raise Lot43ValidationError("unknown Lot 43 book side")


def _quantity_at(observation: BookObservation, side: str, price: Decimal) -> Decimal:
    for level in _levels(observation, side):
        if level.price == price:
            return level.quantity
    return ZERO


def _quantity_gain(
    baseline: BookObservation,
    future: BookObservation,
    side: str,
    price: Decimal,
    precision: int,
) -> Decimal:
    with localcontext() as context:
        context.prec = precision
        return max(
            _quantity_at(future, side, price) - _quantity_at(baseline, side, price),
            ZERO,
        )


def _detect_depletions(
    observations: tuple[BookObservation, ...],
    policy: BookResiliencePolicy,
    decision_time: str,
) -> tuple[BookDepletionEventV1, ...]:
    output: list[BookDepletionEventV1] = []
    for index, (previous, current) in enumerate(pairwise(observations), start=1):
        for side in ("BID", "ASK"):
            output.extend(
                _pair_depletions(
                    observations,
                    index,
                    previous,
                    current,
                    side,
                    policy,
                    decision_time,
                )
            )
    return tuple(output)


def _pair_depletions(
    observations: tuple[BookObservation, ...],
    current_index: int,
    previous: BookObservation,
    current: BookObservation,
    side: str,
    policy: BookResiliencePolicy,
    decision_time: str,
) -> tuple[BookDepletionEventV1, ...]:
    output: list[BookDepletionEventV1] = []
    for level in _levels(previous, side):
        post_quantity = _quantity_at(current, side, level.price)
        with localcontext() as context:
            context.prec = policy.decimal_precision
            depleted = max(level.quantity - post_quantity, ZERO)
            if depleted <= 0:
                continue
            ratio = depleted / level.quantity
        if depleted < policy.depletion_min_quantity or ratio < policy.depletion_min_ratio:
            continue
        candidate = DepletionCandidate(
            current,
            side,
            level.price,
            level.quantity,
            post_quantity,
            depleted,
            ratio,
        )
        output.append(
            _build_depletion_event(
                observations,
                current_index,
                candidate,
                policy,
                decision_time,
            )
        )
    return tuple(output)


def _build_depletion_event(
    observations: tuple[BookObservation, ...],
    current_index: int,
    candidate: DepletionCandidate,
    policy: BookResiliencePolicy,
    decision_time: str,
) -> BookDepletionEventV1:
    baseline = candidate.baseline
    outcome: Outcome | None = _find_first_outcome(
        observations[current_index + 1 :],
        baseline,
        candidate.side,
        candidate.price,
        candidate.depleted,
        policy,
    )
    if outcome is None:
        outcome = _no_outcome(baseline, policy, decision_time)
    kind, sequence_id, time_us, replenished, recovered, shift, status = outcome
    event = BookDepletionEventV1(
        f"lot43-{baseline.sequence_id}-{candidate.side.lower()}-{candidate.price}",
        candidate.side,
        candidate.price,
        candidate.previous_quantity,
        candidate.post_quantity,
        candidate.depleted,
        candidate.ratio,
        baseline.sequence_id,
        baseline.event_time,
        baseline.receive_time,
        kind,
        sequence_id,
        time_us,
        replenished,
        recovered,
        shift,
        status,
        PARTICIPANT_INTENT,
        _event_reason_codes(kind, status),
        ZERO_SHA256,
    )
    return replace(event, event_checksum=canonical_checksum(event.payload_without_checksum()))


def _quantity_replenishment_outcome(
    kind: str,
    observation: BookObservation,
    duration: int,
    gain: Decimal,
    depleted: Decimal,
    policy: BookResiliencePolicy,
) -> Outcome | None:
    fraction = bounded_recovery_fraction(gain, depleted)
    if fraction < policy.replenishment_min_recovery_ratio:
        return None
    return kind, observation.sequence_id, duration, gain, fraction, ZERO, "REPLENISHED"


def _mid_shift_outcome(
    observation: BookObservation,
    baseline: BookObservation,
    side: str,
    duration: int,
    policy: BookResiliencePolicy,
) -> Outcome | None:
    with localcontext() as context:
        context.prec = policy.decimal_precision
        baseline_mid = baseline.mid_price
        future_mid = observation.mid_price
    shift = directional_mid_shift_bps(side, baseline_mid, future_mid)
    if shift < policy.mid_shift_min_bps:
        return None
    return "MID_SHIFT", observation.sequence_id, duration, ZERO, ZERO, shift, "MID_SHIFTED"


def _observation_outcome(
    observation: BookObservation,
    baseline: BookObservation,
    side: str,
    price: Decimal,
    depleted: Decimal,
    policy: BookResiliencePolicy,
    duration: int,
) -> Outcome | None:
    same_gain = _quantity_gain(
        baseline,
        observation,
        side,
        price,
        policy.decimal_precision,
    )
    same = _quantity_replenishment_outcome(
        "SAME_PRICE", observation, duration, same_gain, depleted, policy
    )
    if same is not None:
        return same
    adjacent = _quantity_replenishment_outcome(
        "ADJACENT_PRICE",
        observation,
        duration,
        _adjacent_gain(baseline, observation, side, price, policy),
        depleted,
        policy,
    )
    if adjacent is not None:
        return adjacent
    return _mid_shift_outcome(observation, baseline, side, duration, policy)


def _find_first_outcome(
    future: tuple[BookObservation, ...],
    baseline: BookObservation,
    side: str,
    price: Decimal,
    depleted: Decimal,
    policy: BookResiliencePolicy,
) -> Outcome | None:
    maximum = policy.resilience_horizons_us[-1]
    for observation in future:
        duration = elapsed_us(baseline.receive_time, observation.receive_time)
        if duration > maximum:
            break
        outcome = _observation_outcome(
            observation,
            baseline,
            side,
            price,
            depleted,
            policy,
            duration,
        )
        if outcome is not None:
            return outcome
    return None


def _adjacent_gain(
    baseline: BookObservation,
    future: BookObservation,
    side: str,
    depleted_price: Decimal,
    policy: BookResiliencePolicy,
) -> Decimal:
    prices = {level.price for level in _levels(baseline, side)}
    prices.update(level.price for level in _levels(future, side))
    with localcontext() as context:
        context.prec = policy.decimal_precision
        gain = ZERO
        for price in sorted(prices):
            if price == depleted_price:
                continue
            if (
                bps_distance(price, depleted_price, depleted_price)
                > policy.adjacent_replenishment_distance_bps
            ):
                continue
            gain += _quantity_gain(
                baseline,
                future,
                side,
                price,
                policy.decimal_precision,
            )
        return gain


def _no_outcome(
    baseline: BookObservation,
    policy: BookResiliencePolicy,
    decision_time: str,
) -> Outcome:
    status = (
        "EXPIRED_NO_REPLENISHMENT"
        if age_us(baseline.receive_time, decision_time) >= policy.resilience_horizons_us[-1]
        else "PENDING_WINDOW"
    )
    return "NONE", None, None, ZERO, ZERO, ZERO, status


def _event_reason_codes(kind: str, status: str) -> tuple[str, ...]:
    reasons = ["LOT43_DEPLETION_OBSERVED", "LOT43_PARTICIPANT_INTENT_NOT_INFERRED"]
    mapping = {
        "SAME_PRICE": "LOT43_SAME_PRICE_REPLENISHMENT",
        "ADJACENT_PRICE": "LOT43_ADJACENT_PRICE_REPLENISHMENT",
        "MID_SHIFT": "LOT43_DIRECTIONAL_MID_SHIFT",
    }
    if kind in mapping:
        reasons.append(mapping[kind])
    if status == "EXPIRED_NO_REPLENISHMENT":
        reasons.append("LOT43_NO_REPLENISHMENT_WITHIN_MAX_WINDOW")
    if status == "PENDING_WINDOW":
        reasons.append("LOT43_MAX_WINDOW_PENDING")
    return tuple(reasons)


def _build_resilience_slices(
    events: tuple[BookDepletionEventV1, ...],
    policy: BookResiliencePolicy,
    decision_time: str,
    regime: str,
) -> tuple[BookResilienceSliceV1, ...]:
    output: list[BookResilienceSliceV1] = []
    for side in ("BID", "ASK"):
        side_events = tuple(item for item in events if item.side == side)
        for horizon in policy.resilience_horizons_us:
            output.append(
                _build_slice(side_events, side, horizon, decision_time, regime, policy)
            )
    return tuple(output)


def _build_slice(
    events: tuple[BookDepletionEventV1, ...],
    side: str,
    horizon: int,
    decision_time: str,
    regime: str,
    policy: BookResiliencePolicy,
) -> BookResilienceSliceV1:
    outcomes = tuple(_horizon_outcome(item, horizon, decision_time) for item in events)
    recovered = sum(item == "RECOVERED" for item in outcomes)
    shifted = sum(item == "SHIFTED" for item in outcomes)
    expired = sum(item == "EXPIRED" for item in outcomes)
    pending = sum(item == "PENDING" for item in outcomes)
    mean_fraction = _mean_recovered_fraction(events, horizon, policy.decimal_precision)
    mean_time = _mean_replenishment_time(events, horizon, policy.decimal_precision)
    status = _resilience_status(
        len(events), recovered, shifted, expired, pending, mean_fraction, policy
    )
    resilience_slice = BookResilienceSliceV1(
        side,
        horizon,
        regime,
        REGIME_METHOD,
        len(events),
        recovered,
        shifted,
        expired,
        pending,
        mean_fraction,
        mean_time,
        status,
        ("LOT43_RESILIENCE_SLICE_COMPUTED", f"LOT43_VOLATILITY_REGIME_{regime}"),
        ZERO_SHA256,
        replenishment_min_recovery_ratio=policy.replenishment_min_recovery_ratio,
    )
    return replace(
        resilience_slice,
        slice_checksum=canonical_checksum(resilience_slice.payload_without_checksum()),
    )


def _horizon_outcome(event: BookDepletionEventV1, horizon: int, decision_time: str) -> str:
    if event.replenishment_time_us is not None and event.replenishment_time_us <= horizon:
        if event.replenishment_kind in {"SAME_PRICE", "ADJACENT_PRICE"}:
            return "RECOVERED"
        if event.replenishment_kind == "MID_SHIFT":
            return "SHIFTED"
    return "EXPIRED" if age_us(event.depletion_receive_time, decision_time) >= horizon else "PENDING"


def _mean_recovered_fraction(
    events: tuple[BookDepletionEventV1, ...],
    horizon: int,
    precision: int,
) -> Decimal | None:
    if not events:
        return None
    with localcontext() as context:
        context.prec = precision
        total = ZERO
        for event in events:
            if (
                event.replenishment_kind in {"SAME_PRICE", "ADJACENT_PRICE"}
                and event.replenishment_time_us is not None
                and event.replenishment_time_us <= horizon
            ):
                total += event.recovered_fraction
        return total / Decimal(len(events))


def _mean_replenishment_time(
    events: tuple[BookDepletionEventV1, ...],
    horizon: int,
    precision: int,
) -> Decimal | None:
    times = tuple(
        item.replenishment_time_us
        for item in events
        if item.replenishment_kind in {"SAME_PRICE", "ADJACENT_PRICE"}
        and item.replenishment_time_us is not None
        and item.replenishment_time_us <= horizon
    )
    if not times:
        return None
    with localcontext() as context:
        context.prec = precision
        return Decimal(sum(times)) / Decimal(len(times))


def _resilience_status(
    events: int,
    recovered: int,
    shifted: int,
    expired: int,
    pending: int,
    mean_fraction: Decimal | None,
    policy: BookResiliencePolicy,
) -> str:
    if events == 0:
        return "NO_EVENTS"
    if (
        recovered == events
        and mean_fraction is not None
        and mean_fraction >= policy.replenishment_min_recovery_ratio
    ):
        return "RESILIENT"
    if expired == events:
        return "FRAGILE"
    if shifted == events and recovered == 0 and expired == 0 and pending == 0:
        return "SHIFTED"
    if pending == events:
        return "PENDING"
    return "PARTIAL"

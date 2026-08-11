from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from itertools import pairwise
from typing import Iterable

from crypto_quant_bot.data_governance.market_data_governance_scope_and_source_registry import (
    canonical_checksum,
)

from .liquidity_zones_walls_and_voids_engine_models import LiquidityVoidV1, LiquidityZoneV1
from .liquidity_zones_walls_and_voids_engine_validation import (
    ACTIVE,
    DISPLAYED_WALL,
    HIGH_CONFIDENCE,
    LIQUIDITY_VOID,
    LOW_CONFIDENCE,
    NOT_APPLICABLE,
    PARTICIPANT_INTENT,
    PERSISTENT_ZONE,
    Lot42ValidationError,
    bps_distance,
)
from .order_book_delta_and_sequence_reconstructor import reconstruct_sequence
from .order_book_delta_and_sequence_reconstructor_models import OrderBookDeltaV1
from .order_book_l2_snapshot_engine_models import OrderBookLevelV1, OrderBookSnapshotV1

ZERO_SHA256 = "0" * 64


@dataclass(frozen=True, slots=True)
class LiquidityAnalysisPolicy:
    decimal_precision: int
    cluster_distance_bps: Decimal
    history_match_distance_bps: Decimal
    wall_min_notional: Decimal
    persistent_min_observations: int
    persistent_min_ratio: Decimal
    void_min_gap_bps: Decimal
    wall_high_confidence_max_cancellation_rate: Decimal


@dataclass(frozen=True, slots=True)
class BookObservation:
    source_id: str
    venue: str
    instrument_id: str
    market_type: str
    sequence_id: int
    event_time: str
    receive_time: str
    bids: tuple[OrderBookLevelV1, ...]
    asks: tuple[OrderBookLevelV1, ...]

    @property
    def mid_price(self) -> Decimal:
        if not self.bids or not self.asks:
            raise Lot42ValidationError("book observation must be bilateral")
        if self.bids[0].price >= self.asks[0].price:
            raise Lot42ValidationError("Lot 42 refuses crossed or locked observation")
        return (self.bids[0].price + self.asks[0].price) / Decimal("2")


@dataclass(frozen=True, slots=True)
class PriceCluster:
    side: str
    lower_price: Decimal
    upper_price: Decimal
    anchor_price: Decimal
    quantity: Decimal
    notional: Decimal
    level_count: int


@dataclass(frozen=True, slots=True)
class LiquidityAnalysisResult:
    observations: tuple[BookObservation, ...]
    zones: tuple[LiquidityZoneV1, ...]
    voids: tuple[LiquidityVoidV1, ...]
    expired_candidates_total: int


def reconstruct_observation_history(
    snapshot: OrderBookSnapshotV1,
    deltas: tuple[OrderBookDeltaV1, ...],
) -> tuple[BookObservation, ...]:
    observations = [_observation_from_snapshot(snapshot)]
    for index in range(1, len(deltas) + 1):
        outcome = reconstruct_sequence(snapshot, deltas[:index])
        if outcome.reconstructed_book is None or outcome.synchronization_state != "SYNCED":
            raise Lot42ValidationError("Lot 42 history reconstruction requires SYNCED prefixes")
        book = outcome.reconstructed_book
        observations.append(
            BookObservation(
                book.source_id,
                book.venue,
                book.instrument_id,
                book.market_type,
                book.sequence_id,
                book.event_time,
                book.receive_time,
                book.bids,
                book.asks,
            )
        )
    return tuple(observations)


def _observation_from_snapshot(snapshot: OrderBookSnapshotV1) -> BookObservation:
    return BookObservation(
        snapshot.source_id,
        snapshot.venue,
        snapshot.instrument_id,
        snapshot.market_type,
        snapshot.sequence_id,
        snapshot.event_time,
        snapshot.receive_time,
        snapshot.bids,
        snapshot.asks,
    )


def cluster_observation(
    observation: BookObservation,
    side: str,
    max_distance_bps: Decimal,
    precision: int,
) -> tuple[PriceCluster, ...]:
    levels = observation.bids if side == "BID" else observation.asks
    if side not in {"BID", "ASK"} or not levels:
        raise Lot42ValidationError("cluster observation requires known non-empty side")
    groups: list[list[OrderBookLevelV1]] = [[levels[0]]]
    for level in levels[1:]:
        previous = groups[-1][-1]
        if bps_distance(previous.price, level.price, observation.mid_price) <= max_distance_bps:
            groups[-1].append(level)
        else:
            groups.append([level])
    return tuple(_cluster_from_levels(group, side, precision) for group in groups)


def _cluster_from_levels(
    levels: Iterable[OrderBookLevelV1],
    side: str,
    precision: int,
) -> PriceCluster:
    values = tuple(levels)
    quantity = sum((level.quantity for level in values), Decimal("0"))
    if quantity <= 0:
        raise Lot42ValidationError("cluster quantity must be positive")
    with localcontext() as context:
        context.prec = precision
        notional = sum((level.price * level.quantity for level in values), Decimal("0"))
        anchor = notional / quantity
    prices = tuple(level.price for level in values)
    return PriceCluster(side, min(prices), max(prices), anchor, quantity, notional, len(values))


def analyze_observations(
    observations: tuple[BookObservation, ...],
    policy: LiquidityAnalysisPolicy,
) -> LiquidityAnalysisResult:
    _validate_policy_and_history(observations, policy)
    current = observations[-1]
    bid_history = _cluster_history(observations, "BID", policy)
    ask_history = _cluster_history(observations, "ASK", policy)
    bid_zones = _build_side_zones(current, bid_history, policy)
    ask_zones = _build_side_zones(current, ask_history, policy)
    voids = _detect_voids(current, policy)
    expired = _expired_wall_candidates(bid_history, current.mid_price, policy)
    expired += _expired_wall_candidates(ask_history, current.mid_price, policy)
    return LiquidityAnalysisResult(observations, bid_zones + ask_zones, voids, expired)


def _validate_policy_and_history(
    observations: tuple[BookObservation, ...],
    policy: LiquidityAnalysisPolicy,
) -> None:
    if len(observations) < policy.persistent_min_observations:
        raise Lot42ValidationError("insufficient observations for Lot 42 persistence")
    sequences = tuple(item.sequence_id for item in observations)
    if sequences != tuple(sorted(sequences)) or len(set(sequences)) != len(sequences):
        raise Lot42ValidationError("observation sequences must be strictly increasing")
    identity = _observation_identity(observations[0])
    if any(_observation_identity(item) != identity for item in observations[1:]):
        raise Lot42ValidationError("observation identity changed inside history")
    if policy.persistent_min_ratio < 0 or policy.persistent_min_ratio > 1:
        raise Lot42ValidationError("persistent ratio threshold outside [0,1]")
    if policy.wall_high_confidence_max_cancellation_rate < 0:
        raise Lot42ValidationError("wall cancellation threshold cannot be negative")


def _observation_identity(observation: BookObservation) -> tuple[str, str, str, str]:
    return (
        observation.source_id,
        observation.venue,
        observation.instrument_id,
        observation.market_type,
    )


def _cluster_history(
    observations: tuple[BookObservation, ...],
    side: str,
    policy: LiquidityAnalysisPolicy,
) -> tuple[tuple[PriceCluster, ...], ...]:
    return tuple(
        cluster_observation(item, side, policy.cluster_distance_bps, policy.decimal_precision)
        for item in observations
    )


def _build_side_zones(
    current: BookObservation,
    history: tuple[tuple[PriceCluster, ...], ...],
    policy: LiquidityAnalysisPolicy,
) -> tuple[LiquidityZoneV1, ...]:
    current_clusters = history[-1]
    assignments = _history_assignments(current_clusters, history, current.mid_price, policy)
    zones: list[LiquidityZoneV1] = []
    for index, cluster in enumerate(current_clusters):
        quantities = tuple(row[index] for row in assignments)
        zone = _build_zone(current, cluster, quantities, policy)
        if zone is not None:
            zones.append(zone)
    return tuple(zones)


def _history_assignments(
    current: tuple[PriceCluster, ...],
    history: tuple[tuple[PriceCluster, ...], ...],
    mid: Decimal,
    policy: LiquidityAnalysisPolicy,
) -> tuple[tuple[Decimal | None, ...], ...]:
    rows: list[tuple[Decimal | None, ...]] = []
    for observed in history:
        row: list[Decimal | None] = [None] * len(current)
        pairs = _candidate_pairs(current, observed, mid, policy.history_match_distance_bps)
        used_current: set[int] = set()
        used_observed: set[int] = set()
        for _, current_index, observed_index in pairs:
            if current_index in used_current or observed_index in used_observed:
                continue
            row[current_index] = observed[observed_index].quantity
            used_current.add(current_index)
            used_observed.add(observed_index)
        rows.append(tuple(row))
    return tuple(rows)


def _candidate_pairs(
    current: tuple[PriceCluster, ...],
    observed: tuple[PriceCluster, ...],
    mid: Decimal,
    max_distance: Decimal,
) -> tuple[tuple[Decimal, int, int], ...]:
    pairs = []
    for current_index, current_cluster in enumerate(current):
        for observed_index, observed_cluster in enumerate(observed):
            distance = bps_distance(
                current_cluster.anchor_price,
                observed_cluster.anchor_price,
                mid,
            )
            if distance <= max_distance:
                pairs.append((distance, current_index, observed_index))
    return tuple(sorted(pairs, key=lambda item: (item[0], item[1], item[2])))


def _build_zone(
    current: BookObservation,
    cluster: PriceCluster,
    history_quantities: tuple[Decimal | None, ...],
    policy: LiquidityAnalysisPolicy,
) -> LiquidityZoneV1 | None:
    persistence_count = sum(value is not None for value in history_quantities)
    persistence_ratio = _ratio(persistence_count, len(history_quantities), policy.decimal_precision)
    replenished, replenishment_ratio, cancelled, cancellation_rate = _flow_metrics(
        history_quantities,
        policy.decimal_precision,
    )
    classifications = _classifications(cluster, persistence_count, persistence_ratio, policy)
    if not classifications:
        return None
    confidence = _wall_confidence(classifications, persistence_ratio, cancellation_rate, policy)
    distance = bps_distance(cluster.anchor_price, current.mid_price, current.mid_price)
    reason_codes = _zone_reason_codes(classifications, confidence)
    zone = LiquidityZoneV1(
        _zone_id(current.sequence_id, cluster),
        cluster.side,
        cluster.lower_price,
        cluster.upper_price,
        cluster.anchor_price,
        cluster.level_count,
        cluster.quantity,
        cluster.notional,
        persistence_count,
        len(history_quantities),
        persistence_ratio,
        replenished,
        replenishment_ratio,
        cancelled,
        cancellation_rate,
        distance,
        classifications,
        confidence,
        ACTIVE,
        PARTICIPANT_INTENT,
        reason_codes,
        ZERO_SHA256,
    )
    return replace(zone, zone_checksum=canonical_checksum(zone.payload_without_checksum()))


def _ratio(numerator: int, denominator: int, precision: int) -> Decimal:
    if denominator <= 0:
        raise Lot42ValidationError("ratio denominator must be positive")
    with localcontext() as context:
        context.prec = precision
        return Decimal(numerator) / Decimal(denominator)


def _flow_metrics(
    values: tuple[Decimal | None, ...],
    precision: int,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    replenished = Decimal("0")
    cancelled = Decimal("0")
    base = Decimal("0")
    for previous_raw, current_raw in pairwise(values):
        previous = previous_raw or Decimal("0")
        current = current_raw or Decimal("0")
        base += max(previous, current)
        replenished += max(current - previous, Decimal("0"))
        cancelled += max(previous - current, Decimal("0"))
    if base == 0:
        return replenished, Decimal("0"), cancelled, Decimal("0")
    with localcontext() as context:
        context.prec = precision
        return replenished, replenished / base, cancelled, cancelled / base


def _classifications(
    cluster: PriceCluster,
    persistence_count: int,
    persistence_ratio: Decimal,
    policy: LiquidityAnalysisPolicy,
) -> tuple[str, ...]:
    values: list[str] = []
    if cluster.notional >= policy.wall_min_notional:
        values.append(DISPLAYED_WALL)
    if (
        persistence_count >= policy.persistent_min_observations
        and persistence_ratio >= policy.persistent_min_ratio
    ):
        values.append(PERSISTENT_ZONE)
    return tuple(values)


def _wall_confidence(
    classifications: tuple[str, ...],
    persistence_ratio: Decimal,
    cancellation_rate: Decimal,
    policy: LiquidityAnalysisPolicy,
) -> str:
    if DISPLAYED_WALL not in classifications:
        return NOT_APPLICABLE
    persistent = persistence_ratio >= policy.persistent_min_ratio
    stable = cancellation_rate <= policy.wall_high_confidence_max_cancellation_rate
    return HIGH_CONFIDENCE if persistent and stable else LOW_CONFIDENCE


def _zone_reason_codes(classifications: tuple[str, ...], confidence: str) -> tuple[str, ...]:
    reasons = ["LOT42_OBSERVED_LEVEL_CLUSTER", "LOT42_PARTICIPANT_INTENT_NOT_INFERRED"]
    if DISPLAYED_WALL in classifications:
        reasons.append("LOT42_DISPLAYED_WALL")
    if PERSISTENT_ZONE in classifications:
        reasons.append("LOT42_PERSISTENCE_CONFIRMED")
    if confidence == LOW_CONFIDENCE:
        reasons.append("LOT42_WALL_LOW_CONFIDENCE")
    return tuple(reasons)


def _zone_id(sequence_id: int, cluster: PriceCluster) -> str:
    return f"lot42-{sequence_id}-{cluster.side.lower()}-{cluster.lower_price}-{cluster.upper_price}"


def _detect_voids(
    current: BookObservation,
    policy: LiquidityAnalysisPolicy,
) -> tuple[LiquidityVoidV1, ...]:
    output: list[LiquidityVoidV1] = []
    for side, levels in (("BID", current.bids), ("ASK", current.asks)):
        for near, far in pairwise(levels):
            gap = bps_distance(near.price, far.price, current.mid_price)
            if gap >= policy.void_min_gap_bps:
                output.append(_build_void(current, side, near.price, far.price, gap))
    return tuple(output)


def _build_void(
    current: BookObservation,
    side: str,
    near_price: Decimal,
    far_price: Decimal,
    gap_bps: Decimal,
) -> LiquidityVoidV1:
    midpoint = (near_price + far_price) / Decimal("2")
    distance = bps_distance(midpoint, current.mid_price, current.mid_price)
    void = LiquidityVoidV1(
        f"lot42-{current.sequence_id}-{side.lower()}-void-{near_price}-{far_price}",
        side,
        near_price,
        far_price,
        gap_bps,
        distance,
        LIQUIDITY_VOID,
        ACTIVE,
        PARTICIPANT_INTENT,
        ("LOT42_LIQUIDITY_VOID_OBSERVED", "LOT42_PARTICIPANT_INTENT_NOT_INFERRED"),
        ZERO_SHA256,
    )
    return replace(void, void_checksum=canonical_checksum(void.payload_without_checksum()))


def _expired_wall_candidates(
    history: tuple[tuple[PriceCluster, ...], ...],
    mid: Decimal,
    policy: LiquidityAnalysisPolicy,
) -> int:
    if len(history) < 2:
        return 0
    current = history[-1]
    previous = history[-2]
    if not current or not previous:
        return sum(cluster.notional >= policy.wall_min_notional for cluster in previous)
    pairs = _candidate_pairs(current, previous, mid, policy.history_match_distance_bps)
    matched_previous = {observed_index for _, _, observed_index in pairs}
    return sum(
        index not in matched_previous and cluster.notional >= policy.wall_min_notional
        for index, cluster in enumerate(previous)
    )

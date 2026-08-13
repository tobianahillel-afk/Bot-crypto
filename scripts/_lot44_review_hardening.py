from pathlib import Path

ENGINE = Path("src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py")
MODELS = Path("src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py")
TESTS = Path("tests/test_lot44_causal_guards.py")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one patch anchor in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


replace_once(
    ENGINE,
    '    require(quote > tick > unknown == 0, "Lot 44 confidence policy ordering changed")\n',
    '''    require(\n        (quote, tick, unknown)\n        == (Decimal("1"), Decimal("0.5"), Decimal("0")),\n        "Lot 44 v1 confidence policy constants changed",\n    )\n''',
)

replace_once(
    ENGINE,
    '''    require(\n        previous_event <= trade_event and previous_receive <= trade_receive,\n        "tick-rule previous trade cannot be future",\n    )\n    if trade.price > previous_trade.price:\n''',
    '''    require(\n        previous_event <= trade_event and previous_receive <= trade_receive,\n        "tick-rule previous trade cannot be future",\n    )\n    require(\n        (\n            previous_trade.source_id,\n            previous_trade.venue,\n            previous_trade.instrument_id,\n            previous_trade.market_type,\n        )\n        == (trade.source_id, trade.venue, trade.instrument_id, trade.market_type),\n        "tick-rule previous trade identity mismatch",\n    )\n    if trade.price > previous_trade.price:\n''',
)

replace_once(
    MODELS,
    '''        if self.aggressor_classification == "UNKNOWN":\n            require(\n                self.classification_method == "NONE" or self.confidence == 0,\n                "UNKNOWN cannot carry positive inferred confidence",\n            )\n        if self.classification_method == "QUOTE_TEST":\n            require(\n                self.aggressor_classification != "UNKNOWN",\n                "quote-test method requires classified side",\n            )\n        if self.classification_method == "TICK_RULE":\n            require(\n                self.aggressor_classification != "UNKNOWN",\n                "tick-rule method requires classified side",\n            )\n''',
    '''        _validate_classification_tuple(\n            self.aggressor_classification,\n            self.classification_method,\n            self.confidence,\n        )\n''',
)

replace_once(
    MODELS,
    '''\n\n@dataclass(frozen=True, slots=True)\nclass ClassifiedTradeV1:\n''',
    '''\n\ndef _validate_classification_tuple(\n    classification: str,\n    method: str,\n    confidence: Decimal,\n) -> None:\n    allowed = {\n        "NONE": ({"UNKNOWN"}, Decimal("0")),\n        "QUOTE_TEST": ({"BUY_AGGRESSOR", "SELL_AGGRESSOR"}, Decimal("1")),\n        "TICK_RULE": ({"BUY_AGGRESSOR", "SELL_AGGRESSOR"}, Decimal("0.5")),\n    }\n    allowed_classifications, expected_confidence = allowed[method]\n    require(\n        classification in allowed_classifications and confidence == expected_confidence,\n        "classification method/class/confidence tuple invalid",\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass ClassifiedTradeV1:\n''',
)

replace_once(
    MODELS,
    '''        require(\n            self.quote_test_confidence\n            > self.tick_rule_confidence\n            > self.unknown_confidence,\n            "confidence ordering changed",\n        )\n        require(self.unknown_confidence == 0, "unknown confidence must remain zero")\n''',
    '''        require(\n            (\n                self.quote_test_confidence,\n                self.tick_rule_confidence,\n                self.unknown_confidence,\n            )\n            == (Decimal("1"), Decimal("0.5"), Decimal("0")),\n            "Lot 44 v1 confidence constants changed",\n        )\n''',
)

replace_once(
    MODELS,
    '''\n\n@dataclass(frozen=True, slots=True)\nclass TradesAggressorClassificationSchemaStateV1:\n''',
    '''\n\ndef _metrics_from_classified_trades(\n    classified_trades: tuple[ClassifiedTradeV1, ...],\n) -> Lot44MetricsV1:\n    buy = tuple(\n        item\n        for item in classified_trades\n        if item.aggressor_classification == "BUY_AGGRESSOR"\n    )\n    sell = tuple(\n        item\n        for item in classified_trades\n        if item.aggressor_classification == "SELL_AGGRESSOR"\n    )\n    unknown = tuple(\n        item for item in classified_trades if item.aggressor_classification == "UNKNOWN"\n    )\n    total_volume = sum(\n        (item.trade.quantity for item in classified_trades), Decimal("0")\n    )\n    buy_volume = sum((item.trade.quantity for item in buy), Decimal("0"))\n    sell_volume = sum((item.trade.quantity for item in sell), Decimal("0"))\n    unknown_volume = sum((item.trade.quantity for item in unknown), Decimal("0"))\n    return Lot44MetricsV1(\n        trades_total=len(classified_trades),\n        buy_trades_total=len(buy),\n        sell_trades_total=len(sell),\n        unknown_trades_total=len(unknown),\n        total_volume=total_volume,\n        buy_volume=buy_volume,\n        sell_volume=sell_volume,\n        unknown_volume=unknown_volume,\n        unknown_volume_ratio=unknown_volume / total_volume,\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass TradesAggressorClassificationSchemaStateV1:\n''',
)

replace_once(
    MODELS,
    '''        require(\n            self.metrics.trades_total == len(self.classified_trades),\n            "metrics trade count mismatch",\n        )\n        require_reason_codes(self.reason_codes)\n''',
    '''        require(\n            self.metrics == _metrics_from_classified_trades(self.classified_trades),\n            "metrics do not match classified trades",\n        )\n        require_reason_codes(self.reason_codes)\n''',
)

replace_once(
    TESTS,
    '''from __future__ import annotations\n\nfrom decimal import Decimal\n''',
    '''from __future__ import annotations\n\nfrom dataclasses import replace\nfrom decimal import Decimal\n''',
)
replace_once(
    TESTS,
    '''    CONFIG_PATH,\n    _load_snapshot,\n    build_lot44_artifacts,\n    classify_trade,\n)\nfrom crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (\n    TimestampedTradeV1,\n)\n''',
    '''    CONFIG_PATH,\n    _load_snapshot,\n    _validate_confidence_policy,\n    build_lot44_artifacts,\n    classify_trade,\n)\nfrom crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_models import (\n    AggressorConfidenceStateV1,\n    ClassifiedTradeV1,\n    Lot44MetricsV1,\n    TimestampedTradeV1,\n)\n''',
)

TESTS.write_text(
    TESTS.read_text(encoding="utf-8")
    + r'''

@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("source_id", "different-source"),
        ("venue", "OTHER-VENUE"),
        ("instrument_id", "ETH-EUR-SPOT"),
    ),
)
def test_tick_rule_rejects_previous_trade_identity_mismatch(
    field: str,
    value: str,
) -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    current = _trade(
        "identity-current",
        "101",
        "2026-08-06T19:18:40.100000Z",
        "2026-08-06T19:18:40.150000Z",
    )
    previous = _trade(
        "identity-previous",
        "100",
        "2026-08-06T19:18:40.000000Z",
        "2026-08-06T19:18:40.050000Z",
    )
    mismatched = replace(previous, **{field: value})
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="tick-rule previous trade identity mismatch",
    ):
        classify_trade(
            current,
            None,
            mismatched,
            max_quote_age_us=250000,
            confidence=state.confidence_state,
            tick_rule_fallback=True,
        )


@pytest.mark.parametrize(
    ("classification", "method", "confidence"),
    (
        ("UNKNOWN", "NONE", Decimal("0.5")),
        ("BUY_AGGRESSOR", "NONE", Decimal("0")),
        ("UNKNOWN", "QUOTE_TEST", Decimal("1")),
        ("BUY_AGGRESSOR", "QUOTE_TEST", Decimal("0")),
        ("SELL_AGGRESSOR", "TICK_RULE", Decimal("1")),
    ),
)
def test_classified_trade_rejects_schema_incompatible_tuple(
    classification: str,
    method: str,
    confidence: Decimal,
) -> None:
    trade = _trade(
        "tuple-invalid",
        "100",
        "2026-08-06T19:18:40.000000Z",
        "2026-08-06T19:18:40.050000Z",
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="classification method/class/confidence tuple invalid",
    ):
        ClassifiedTradeV1(
            trade=trade,
            aggressor_classification=classification,
            classification_method=method,
            confidence=confidence,
            confidence_version="lot44-aggressor-confidence-v1",
            quote_snapshot_checksum="0" * 64,
            reason_codes=("NEGATIVE_TEST",),
        )


def test_confidence_state_requires_exact_v1_constants() -> None:
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="Lot 44 v1 confidence constants changed",
    ):
        AggressorConfidenceStateV1(
            policy_version="lot44-aggressor-confidence-v1",
            semantics="DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY",
            quote_test_confidence=Decimal("0.9"),
            tick_rule_confidence=Decimal("0.4"),
            unknown_confidence=Decimal("0"),
            confidence_checksum="0" * 64,
        )


def test_config_requires_exact_v1_confidence_constants() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    config["quote_test_confidence"] = "0.9"
    config["tick_rule_confidence"] = "0.4"
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="Lot 44 v1 confidence policy constants changed",
    ):
        _validate_confidence_policy(config)


def test_state_rejects_self_consistent_wrong_category_counts() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    bad_metrics = replace(
        state.metrics,
        buy_trades_total=2,
        sell_trades_total=1,
        unknown_trades_total=0,
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="metrics do not match classified trades",
    ):
        replace(state, metrics=bad_metrics)


def test_state_rejects_self_consistent_wrong_category_volumes() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    bad_metrics = Lot44MetricsV1(
        trades_total=3,
        buy_trades_total=1,
        sell_trades_total=1,
        unknown_trades_total=1,
        total_volume=Decimal("0.16"),
        buy_volume=Decimal("0.05"),
        sell_volume=Decimal("0.03"),
        unknown_volume=Decimal("0.08"),
        unknown_volume_ratio=Decimal("0.5"),
    )
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="metrics do not match classified trades",
    ):
        replace(state, metrics=bad_metrics)
''',
    encoding="utf-8",
)

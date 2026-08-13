from pathlib import Path

VALIDATION = Path('src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_validation.py')
ENGINE = Path('src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py')
MODELS = Path('src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema_models.py')
TESTS = Path('tests/test_lot44_causal_guards.py')


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise SystemExit(f'expected one patch anchor in {path}: {old[:100]!r}')
    path.write_text(text.replace(old, new), encoding='utf-8')


replace_once(
    VALIDATION,
    'from typing import Any\n',
    'from collections.abc import Mapping\nfrom typing import Any\n',
)
replace_once(
    VALIDATION,
    '''def decimal_text(value: Decimal) -> str:\n    require(value.is_finite(), "decimal must be finite")\n    text = format(value, "f")\n''',
    '''def decimal_text(value: Decimal) -> str:\n    require(value.is_finite(), "decimal must be finite")\n    if value == 0:\n        return "0"\n    text = format(value, "f")\n''',
)
replace_once(
    VALIDATION,
    'def validate_safety(value: dict[str, object]) -> None:\n',
    'def validate_safety(value: Mapping[str, object]) -> None:\n',
)

replace_once(
    ENGINE,
    '''    require_text(config.get("confidence_version"), "confidence_version")\n    parse_utc_timestamp(config.get("generated_at"), "generated_at")\n''',
    '''    confidence_version = require_text(\n        config.get("confidence_version"), "confidence_version"\n    )\n    require(\n        confidence_version == "lot44-aggressor-confidence-v1",\n        "Lot 44 confidence version changed",\n    )\n    parse_utc_timestamp(config.get("generated_at"), "generated_at")\n''',
)

replace_once(
    MODELS,
    '''from dataclasses import dataclass\nfrom decimal import Decimal\nfrom typing import Any\n''',
    '''from collections.abc import Mapping\nfrom dataclasses import dataclass\nfrom decimal import Decimal\nfrom types import MappingProxyType\nfrom typing import Any\n''',
)
replace_once(
    MODELS,
    '    safety: dict[str, object]\n    output_checksum: str\n',
    '    safety: Mapping[str, object]\n    output_checksum: str\n',
)
replace_once(
    MODELS,
    '''        require_reason_codes(self.reason_codes)\n        validate_safety(self.safety)\n        require_sha256(self.output_checksum, "output_checksum")\n''',
    '''        require_reason_codes(self.reason_codes)\n        validate_safety(self.safety)\n        object.__setattr__(self, "safety", MappingProxyType(dict(self.safety)))\n        require_sha256(self.output_checksum, "output_checksum")\n''',
)
replace_once(
    MODELS,
    '    safety: dict[str, object]\n    audit_checksum: str\n',
    '    safety: Mapping[str, object]\n    audit_checksum: str\n',
)
replace_once(
    MODELS,
    '''        require(\n            self.validation_state == "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY",\n            "unknown Lot 44 audit state",\n        )\n        validate_safety(self.safety)\n''',
    '''        require(\n            self.validation_state == "VALIDATED_OFFLINE_AGGRESSOR_CLASSIFICATION_ONLY",\n            "unknown Lot 44 audit state",\n        )\n        validate_safety(self.safety)\n        object.__setattr__(self, "safety", MappingProxyType(dict(self.safety)))\n''',
)

replace_once(
    TESTS,
    '''    CONFIG_PATH,\n    _load_snapshot,\n    _validate_confidence_policy,\n''',
    '''    CONFIG_PATH,\n    _load_snapshot,\n    _validate_config_identity,\n    _validate_confidence_policy,\n''',
)
replace_once(
    TESTS,
    '''from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_validation import (\n    TradesAggressorClassificationValidationError,\n)\n''',
    '''from crypto_quant_bot.microstructure.trades_and_aggressor_classification_schema_validation import (\n    TradesAggressorClassificationValidationError,\n    decimal_text,\n)\n''',
)

TESTS.write_text(
    TESTS.read_text(encoding='utf-8')
    + r'''


def test_decimal_text_normalizes_signed_zero() -> None:
    assert decimal_text(Decimal("-0")) == "0"
    assert decimal_text(Decimal("0")) == "0"


def test_config_rejects_non_v1_confidence_version() -> None:
    config = load_json_object(ROOT / CONFIG_PATH)
    config["confidence_version"] = "lot44-aggressor-confidence-v2"
    with pytest.raises(
        TradesAggressorClassificationValidationError,
        match="Lot 44 confidence version changed",
    ):
        _validate_config_identity(config)


def test_negative_zero_confidence_serializes_to_schema_constant() -> None:
    confidence = AggressorConfidenceStateV1(
        policy_version="lot44-aggressor-confidence-v1",
        semantics="DESCRIPTIVE_METHOD_CONFIDENCE_NOT_PROBABILITY",
        quote_test_confidence=Decimal("1"),
        tick_rule_confidence=Decimal("0.5"),
        unknown_confidence=Decimal("-0"),
        confidence_checksum="0" * 64,
    )
    assert confidence.to_dict()["unknown_confidence"] == "0"


def test_state_safety_is_immutable_after_validation() -> None:
    state, _ = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    with pytest.raises(TypeError):
        state.safety["trade_allowed"] = True  # type: ignore[index]
    assert state.to_dict()["safety"]["trade_allowed"] is False


def test_audit_safety_is_immutable_after_validation() -> None:
    _, audit = build_lot44_artifacts(ROOT, code_commit=CODE_COMMIT)
    with pytest.raises(TypeError):
        audit.safety["trade_allowed"] = True  # type: ignore[index]
    assert audit.to_dict()["safety"]["trade_allowed"] is False
''',
    encoding='utf-8',
)

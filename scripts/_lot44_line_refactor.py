from pathlib import Path

path = Path('src/crypto_quant_bot/microstructure/trades_and_aggressor_classification_schema.py')
text = path.read_text(encoding='utf-8')
old = '''    previous_event = parse_utc_timestamp(previous_trade.event_time, "previous event_time")\n    trade_event = parse_utc_timestamp(trade.event_time, "trade event_time")\n    previous_receive = parse_utc_timestamp(\n        previous_trade.receive_time,\n        "previous receive_time",\n    )\n    trade_receive = parse_utc_timestamp(trade.receive_time, "trade receive_time")\n    require(\n        previous_event <= trade_event and previous_receive <= trade_receive,\n        "tick-rule previous trade cannot be future",\n    )\n    require(\n        (\n            previous_trade.source_id,\n            previous_trade.venue,\n            previous_trade.instrument_id,\n            previous_trade.market_type,\n        )\n        == (trade.source_id, trade.venue, trade.instrument_id, trade.market_type),\n        "tick-rule previous trade identity mismatch",\n    )\n'''
new = '''    _validate_tick_history(previous_trade, trade)\n'''
if text.count(old) != 1:
    raise SystemExit('tick-history block anchor mismatch')
text = text.replace(old, new)
marker = '''\n\ndef _classify_without_quote(\n'''
helper = '''\n\ndef _validate_tick_history(\n    previous_trade: TimestampedTradeV1,\n    trade: TimestampedTradeV1,\n) -> None:\n    previous_event = parse_utc_timestamp(previous_trade.event_time, "previous event_time")\n    trade_event = parse_utc_timestamp(trade.event_time, "trade event_time")\n    previous_receive = parse_utc_timestamp(\n        previous_trade.receive_time, "previous receive_time"\n    )\n    trade_receive = parse_utc_timestamp(trade.receive_time, "trade receive_time")\n    require(\n        previous_event <= trade_event and previous_receive <= trade_receive,\n        "tick-rule previous trade cannot be future",\n    )\n    previous_identity = (\n        previous_trade.source_id,\n        previous_trade.venue,\n        previous_trade.instrument_id,\n        previous_trade.market_type,\n    )\n    trade_identity = (trade.source_id, trade.venue, trade.instrument_id, trade.market_type)\n    require(previous_identity == trade_identity, "tick-rule previous trade identity mismatch")\n\n\ndef _classify_without_quote(\n'''
if text.count(marker) != 1:
    raise SystemExit('classify-without-quote marker mismatch')
path.write_text(text.replace(marker, helper), encoding='utf-8')

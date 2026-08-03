# Lot 1-bis Validation Report

Status: PASS

Validated components:

- official valid fixture exists and contains at least 6 candles
- official invalid fixture exists and is detected as invalid/degraded
- data_writer.py exists
- SHA256 checksum length is 64 characters
- bronze JSONL dataset exists
- dataset catalog exists and contains Lot 1 metadata
- data quality markdown report exists
- Decision Engine still returns WAIT
- Risk Engine still blocks by default
- trade_allowed remains false
- live_execution remains DISABLED
- leverage remains FORBIDDEN

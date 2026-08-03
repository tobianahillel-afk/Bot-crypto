# ATR Policy — Lot 5

True Range is computed as `max(high-low, abs(high-previous_close), abs(low-previous_close))`. For the first row, True Range is `high-low`. ATR is a simple mean over the last 3 or 6 available True Range values. Insufficient windows return `null`.

All ATR values keep `used_for_decision=false` in Lot 5.

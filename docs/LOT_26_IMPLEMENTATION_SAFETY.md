# Lot 26 immutable safety boundary

All Lot 26 public contracts enforce `analysis_only=true`, `used_for_decision=false`, `forecast_generation_allowed=false`, `probability_claims_allowed=false`, `signal_generation_allowed=false`, `order_routing_allowed=false`, `execution_allowed=false`, `trade_allowed=false`, and `approved_size=0`.

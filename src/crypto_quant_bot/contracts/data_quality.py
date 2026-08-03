from dataclasses import dataclass, field

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class DataQualityReport(BaseContract):
    dataset_id: str = ""
    checked_at: str = ""
    row_count: int = 0
    missing_rows: int = 0
    duplicate_rows: int = 0
    invalid_rows: int = 0
    monotonic_timestamp: bool = True
    has_negative_volume: bool = False
    has_ohlc_inconsistency: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

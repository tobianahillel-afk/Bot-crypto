from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from crypto_quant_bot.core.clock import utc_now_iso


@dataclass(frozen=True)
class BaseContract:
    id: str = field(default_factory=lambda: str(uuid4()))
    schema_version: str = "1.0.0"
    source: str = "lot0"
    created_at: str = field(default_factory=utc_now_iso)
    available_at: str = field(default_factory=utc_now_iso)
    lineage_id: str = field(default_factory=lambda: str(uuid4()))
    quality_flag: str = "valid"
    validation_status: str = "unvalidated"
    used_for_decision: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

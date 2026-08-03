import json
from dataclasses import dataclass, field
from typing import Any

from crypto_quant_bot.core.clock import utc_now_iso


@dataclass(frozen=True)
class JsonLogEvent:
    event_type: str
    level: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)

    def to_json(self) -> str:
        return json.dumps(
            {
                "event_type": self.event_type,
                "timestamp": self.timestamp,
                "level": self.level,
                "message": self.message,
                "context": self.context,
            },
            ensure_ascii=False,
            sort_keys=True,
        )


class JsonLogger:
    def log(self, event_type: str, level: str, message: str, context: dict[str, Any] | None = None) -> str:
        event = JsonLogEvent(event_type=event_type, level=level, message=message, context=context or {})
        line = event.to_json()
        print(line)
        return line

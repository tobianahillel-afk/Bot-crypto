from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class ReplayRecord(BaseContract):
    replay_id: str = ""
    decision_id: str = ""
    path: str = ""

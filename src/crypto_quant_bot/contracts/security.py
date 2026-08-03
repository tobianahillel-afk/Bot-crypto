from dataclasses import dataclass

from crypto_quant_bot.contracts.base import BaseContract


@dataclass(frozen=True)
class SecurityPolicyState(BaseContract):
    withdrawal_permission_allowed: bool = False
    live_trading_enabled: bool = False
    secrets_allowed_in_git: bool = False
    reason: str = "lot0_security_skeleton"

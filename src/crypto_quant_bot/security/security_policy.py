from crypto_quant_bot.contracts.security import SecurityPolicyState


class SecurityPolicy:
    def current_state(self) -> SecurityPolicyState:
        return SecurityPolicyState(
            withdrawal_permission_allowed=False,
            live_trading_enabled=False,
            secrets_allowed_in_git=False,
            validation_status="validated_lot0",
        )

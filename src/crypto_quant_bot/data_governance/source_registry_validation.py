from __future__ import annotations


class SourceRegistryValidationError(ValueError):
    """Fail-closed validation error for Lot 31 source-governance contracts."""


ALLOWED_CAPABILITY_STATES = {
    "REQUIRED",
    "OPTIONAL_RESEARCH",
    "DISABLED",
    "FORBIDDEN",
}
ALLOWED_CRITICALITY = {"PRIMARY", "SECONDARY", "TERTIARY"}
FORBIDDEN_SECRET_TOKENS = (
    "api_key",
    "apikey",
    "secret",
    "password",
    "private_key",
    "access_token",
    "bearer",
)


def require_non_empty(value: str, field: str) -> None:
    if not value or value != value.strip():
        raise SourceRegistryValidationError(f"{field} must be explicit and trimmed")


def require_sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise SourceRegistryValidationError(f"{field} must be a lowercase sha256")


def require_git_sha(value: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise SourceRegistryValidationError("code_commit must be a lowercase 40-character git sha")


def require_utc_timestamp(value: str, field: str) -> None:
    require_non_empty(value, field)
    if not value.endswith("Z") or "T" not in value:
        raise SourceRegistryValidationError(f"{field} must be an explicit UTC timestamp")


def require_secret_free(values: tuple[str, ...], field: str) -> None:
    for value in values:
        lowered = value.lower()
        if any(token in lowered for token in FORBIDDEN_SECRET_TOKENS):
            raise SourceRegistryValidationError(f"{field} contains forbidden secret material")


def fail_closed_safety() -> dict[str, object]:
    return {
        "analysis_only": True,
        "used_for_decision": False,
        "external_connectivity_allowed": False,
        "network_ingestion_allowed": False,
        "real_credentials_allowed": False,
        "signal_generation_allowed": False,
        "risk_approval_allowed": False,
        "order_routing_allowed": False,
        "trade_allowed": False,
        "execution_allowed": False,
        "approved_size": 0,
    }


def validate_fail_closed_safety(values: dict[str, object]) -> None:
    if values != fail_closed_safety():
        raise SourceRegistryValidationError("Lot 31 safety boundary must remain exactly fail-closed")

from typing import Any

FORBIDDEN_KEY_TOKENS = [
    "future_",
    "target",
    "label",
    "signal",
]
FORBIDDEN_VALUE_TOKENS = {
    "LONG",
    "SHORT",
    "BUY",
    "SELL",
    "ENTRY",
    "EXIT",
}


def _record(path: str, rule: str, value: Any, reference: Any = None) -> dict[str, Any]:
    return {"path": path, "rule": rule, "value": value, "reference": reference}


def _walk(obj: Any, path: str = "$") -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            lowered = key_text.lower()
            if any(token in lowered for token in FORBIDDEN_KEY_TOKENS):
                violations.append(_record(child_path, "forbidden key", key_text))
            violations.extend(_walk(value, child_path))
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            violations.extend(_walk(item, f"{path}[{index}]"))
    elif isinstance(obj, str) and obj.upper() in FORBIDDEN_VALUE_TOKENS:
        violations.append(_record(path, "forbidden trading direction value", obj))
    return violations


def check_market_state_no_lookahead(market_state: dict[str, Any], step_available_at: str) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    market_available_at = str(market_state.get("available_at", ""))
    if market_available_at and step_available_at and market_available_at > step_available_at:
        violations.append(_record("$.available_at", "market_state.available_at <= step.available_at", market_available_at, step_available_at))
    component_available_at = market_state.get("component_available_at")
    if isinstance(component_available_at, dict):
        for name, value in component_available_at.items():
            if isinstance(value, str) and market_available_at and value > market_available_at:
                violations.append(_record(f"$.component_available_at.{name}", "component_available_at <= market_state.available_at", value, market_available_at))
    violations.extend(_walk(market_state))
    return violations


def check_step_no_lookahead(step: dict[str, Any], market_state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    violations = _walk(step)
    if market_state is not None:
        violations.extend(check_market_state_no_lookahead(market_state, str(step.get("available_at", ""))))
    return violations

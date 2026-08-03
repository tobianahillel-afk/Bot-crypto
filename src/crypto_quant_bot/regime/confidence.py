
def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def confidence_score(values: list[float | None]) -> float | None:
    available = [float(value) for value in values if value is not None]
    if not available:
        return None
    bounded = [clamp01(abs(value)) for value in available]
    return round(sum(bounded) / len(bounded), 12)

SUPPORTED_TIMEFRAMES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
}


def timeframe_to_minutes(timeframe: str) -> int:
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    return SUPPORTED_TIMEFRAMES[timeframe]

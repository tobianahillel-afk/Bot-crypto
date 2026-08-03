from enum import StrEnum


class TradingDecision(StrEnum):
    WAIT = "WAIT"
    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE = "CLOSE"
    REDUCE = "REDUCE"


class SystemDecision(StrEnum):
    BLOCK_TRADING = "BLOCK_TRADING"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    KILL_SWITCH = "KILL_SWITCH"


class ModuleStatus(StrEnum):
    MVP_REQUIRED = "MVP_REQUIRED"
    REQUIRED_BEFORE_LIVE = "REQUIRED_BEFORE_LIVE"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    DISABLED = "DISABLED"
    FORBIDDEN = "FORBIDDEN"

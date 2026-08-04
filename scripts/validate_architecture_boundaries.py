from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKET_ROOT = ROOT / "src" / "crypto_quant_bot" / "market_analysis"
FORBIDDEN_PREFIXES = (
    "crypto_quant_bot.execution",
    "crypto_quant_bot.live",
    "crypto_quant_bot.oms",
    "crypto_quant_bot.ems",
    "crypto_quant_bot.exchange.write",
)


def main() -> int:
    violations: list[str] = []
    for path in sorted(MARKET_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.startswith(FORBIDDEN_PREFIXES):
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}:{name}")
    if violations:
        print("ARCHITECTURE BOUNDARY VIOLATIONS")
        print("\n".join(violations))
        return 1
    print("MARKET_ANALYSIS_EXECUTION_BOUNDARY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

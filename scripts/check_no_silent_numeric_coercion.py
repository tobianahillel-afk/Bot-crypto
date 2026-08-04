from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"


def returns_numeric_zero(node: ast.AST) -> bool:
    return isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) and node.value.value == 0.0


def main() -> int:
    violations: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {
                "_as_float",
                "as_float",
                "to_float",
            }:
                if any(returns_numeric_zero(child) for child in ast.walk(node)):
                    violations.append(f"{path.relative_to(ROOT)}:{node.lineno}:{node.name}")
    if violations:
        print("SILENT NUMERIC COERCION VIOLATIONS")
        print("\n".join(violations))
        return 1
    print("NO_SILENT_NUMERIC_COERCION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

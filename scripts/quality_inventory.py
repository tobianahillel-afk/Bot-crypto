from __future__ import annotations

import argparse
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
REPORT_JSON = ROOT / "reports" / "quality" / "complexity_duplication_inventory.json"
REPORT_MD = ROOT / "reports" / "quality" / "complexity_duplication_inventory.md"

BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.BoolOp,
    ast.IfExp,
    ast.Match,
    ast.comprehension,
)


def function_complexity(node: ast.AST) -> int:
    return 1 + sum(isinstance(child, BRANCH_NODES) for child in ast.walk(node))


def normalized_function_hash(node: ast.AST) -> str:
    normalized = ast.dump(node, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_inventory() -> dict[str, object]:
    files: list[dict[str, object]] = []
    functions: list[dict[str, object]] = []
    duplicate_index: dict[str, list[dict[str, object]]] = defaultdict(list)

    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=relative)
        file_functions = 0
        maximum_complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                file_functions += 1
                complexity = function_complexity(node)
                maximum_complexity = max(maximum_complexity, complexity)
                item = {
                    "path": relative,
                    "name": node.name,
                    "line": node.lineno,
                    "complexity": complexity,
                    "statement_count": sum(isinstance(child, ast.stmt) for child in ast.walk(node)),
                }
                functions.append(item)
                if item["statement_count"] >= 5:
                    duplicate_index[normalized_function_hash(node)].append(item)
        files.append(
            {
                "path": relative,
                "line_count": len(text.splitlines()),
                "function_count": file_functions,
                "maximum_function_complexity": maximum_complexity,
            }
        )

    duplicates = [items for items in duplicate_index.values() if len(items) > 1]
    high_complexity = sorted(
        [item for item in functions if int(item["complexity"]) > 15],
        key=lambda item: int(item["complexity"]),
        reverse=True,
    )
    oversized_files = sorted(
        [item for item in files if int(item["line_count"]) > 700],
        key=lambda item: int(item["line_count"]),
        reverse=True,
    )
    return {
        "schema_version": "quality-inventory-v1",
        "scope": "src/**/*.py",
        "thresholds": {
            "high_complexity": 15,
            "oversized_file_lines": 700,
            "duplicate_min_statements": 5,
        },
        "summary": {
            "files": len(files),
            "functions": len(functions),
            "high_complexity_functions": len(high_complexity),
            "oversized_files": len(oversized_files),
            "duplicate_function_groups": len(duplicates),
        },
        "high_complexity_functions": high_complexity,
        "oversized_files": oversized_files,
        "duplicate_function_groups": duplicates,
    }


def render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# Complexity and Duplication Inventory",
        "",
        "This report is an inventory. Legacy findings are not silently treated as fixed.",
        "",
        "## Summary",
        "",
        f"- Files: {summary['files']}",
        f"- Functions: {summary['functions']}",
        f"- High-complexity functions: {summary['high_complexity_functions']}",
        f"- Oversized files: {summary['oversized_files']}",
        f"- Duplicate function groups: {summary['duplicate_function_groups']}",
        "",
        "## High-complexity functions",
        "",
    ]
    for item in payload["high_complexity_functions"]:
        lines.append(
            f"- `{item['path']}:{item['line']}` `{item['name']}` — complexity {item['complexity']}"
        )
    lines.extend(["", "## Oversized files", ""])
    for item in payload["oversized_files"]:
        lines.append(f"- `{item['path']}` — {item['line_count']} lines")
    lines.extend(["", "## Duplicate function groups", ""])
    for group in payload["duplicate_function_groups"]:
        locations = ", ".join(
            f"{item['path']}:{item['line']}:{item['name']}" for item in group
        )
        lines.append(f"- {locations}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=REPORT_JSON)
    parser.add_argument("--markdown", type=Path, default=REPORT_MD)
    args = parser.parse_args()
    payload = build_inventory()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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

THRESHOLDS = {
    "function_lines": 50,
    "class_lines": 400,
    "module_lines": 800,
    "cyclomatic_complexity": 10,
    "nesting": 4,
    "parameters": 7,
    "duplicate_min_statements": 5,
}

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
NESTING_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
    ast.Match,
)


def function_complexity(node: ast.AST) -> int:
    return 1 + sum(isinstance(child, BRANCH_NODES) for child in ast.walk(node))


def normalized_function_hash(node: ast.AST) -> str:
    normalized = ast.dump(node, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def source_span(node: ast.AST) -> int:
    start = int(getattr(node, "lineno", 0))
    end = int(getattr(node, "end_lineno", start))
    return max(0, end - start + 1)


def parameter_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    args = node.args
    return (
        len(args.posonlyargs)
        + len(args.args)
        + len(args.kwonlyargs)
        + int(args.vararg is not None)
        + int(args.kwarg is not None)
    )


def maximum_nesting(node: ast.AST) -> int:
    maximum = 0

    def visit(current: ast.AST, depth: int) -> None:
        nonlocal maximum
        next_depth = depth + int(isinstance(current, NESTING_NODES))
        maximum = max(maximum, next_depth)
        for child in ast.iter_child_nodes(current):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) and child is not node:
                continue
            visit(child, next_depth)

    visit(node, 0)
    return maximum


def finding_id(category: str, path: str, line: int, name: str) -> str:
    raw = f"{category}|{path}|{line}|{name}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{category}:{digest}"


def build_inventory() -> dict[str, object]:
    files: list[dict[str, object]] = []
    functions: list[dict[str, object]] = []
    classes: list[dict[str, object]] = []
    duplicate_index: dict[str, list[dict[str, object]]] = defaultdict(list)

    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=relative)
        file_functions = 0
        maximum_complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                file_functions += 1
                complexity = function_complexity(node)
                maximum_complexity = max(maximum_complexity, complexity)
                item = {
                    "path": relative,
                    "name": node.name,
                    "line": node.lineno,
                    "end_line": node.end_lineno or node.lineno,
                    "line_count": source_span(node),
                    "complexity": complexity,
                    "nesting": maximum_nesting(node),
                    "parameter_count": parameter_count(node),
                    "statement_count": sum(isinstance(child, ast.stmt) for child in ast.walk(node)),
                }
                functions.append(item)
                if int(item["statement_count"]) >= THRESHOLDS["duplicate_min_statements"]:
                    duplicate_index[normalized_function_hash(node)].append(item)
            elif isinstance(node, ast.ClassDef):
                classes.append(
                    {
                        "path": relative,
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno or node.lineno,
                        "line_count": source_span(node),
                    }
                )
        files.append(
            {
                "path": relative,
                "line_count": len(text.splitlines()),
                "function_count": file_functions,
                "maximum_function_complexity": maximum_complexity,
            }
        )

    duplicate_groups = [items for items in duplicate_index.values() if len(items) > 1]
    findings: list[dict[str, object]] = []

    def add_finding(category: str, item: dict[str, object], observed_key: str, limit: int) -> None:
        path = str(item["path"])
        line = int(item.get("line", 1))
        name = str(item.get("name", Path(path).name))
        findings.append(
            {
                "finding_id": finding_id(category, path, line, name),
                "category": category,
                "path": path,
                "line": line,
                "name": name,
                "observed": int(item[observed_key]),
                "limit": limit,
            }
        )

    for item in functions:
        if int(item["line_count"]) > THRESHOLDS["function_lines"]:
            add_finding("FUNCTION_LINES", item, "line_count", THRESHOLDS["function_lines"])
        if int(item["complexity"]) > THRESHOLDS["cyclomatic_complexity"]:
            add_finding(
                "CYCLOMATIC_COMPLEXITY",
                item,
                "complexity",
                THRESHOLDS["cyclomatic_complexity"],
            )
        if int(item["nesting"]) > THRESHOLDS["nesting"]:
            add_finding("NESTING", item, "nesting", THRESHOLDS["nesting"])
        if int(item["parameter_count"]) > THRESHOLDS["parameters"]:
            add_finding("PARAMETERS", item, "parameter_count", THRESHOLDS["parameters"])

    for item in classes:
        if int(item["line_count"]) > THRESHOLDS["class_lines"]:
            add_finding("CLASS_LINES", item, "line_count", THRESHOLDS["class_lines"])

    for item in files:
        if int(item["line_count"]) > THRESHOLDS["module_lines"]:
            add_finding("MODULE_LINES", item, "line_count", THRESHOLDS["module_lines"])

    duplicates: list[dict[str, object]] = []
    for group in duplicate_groups:
        locations = sorted(
            f"{item['path']}:{item['line']}:{item['name']}" for item in group
        )
        digest = hashlib.sha256("|".join(locations).encode("utf-8")).hexdigest()[:16]
        duplicate = {
            "finding_id": f"DUPLICATE_FUNCTION:{digest}",
            "category": "DUPLICATE_FUNCTION",
            "locations": locations,
            "member_count": len(locations),
            "limit": 1,
        }
        duplicates.append(duplicate)
        findings.append(duplicate)

    findings.sort(key=lambda item: str(item["finding_id"]))
    category_counts: dict[str, int] = defaultdict(int)
    for item in findings:
        category_counts[str(item["category"])] += 1

    return {
        "schema_version": "quality-inventory-v2",
        "scope": "src/**/*.py",
        "thresholds": THRESHOLDS,
        "summary": {
            "files": len(files),
            "functions": len(functions),
            "classes": len(classes),
            "finding_count": len(findings),
            "category_counts": dict(sorted(category_counts.items())),
        },
        "findings": findings,
        "duplicate_function_groups": duplicates,
    }


def render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# Engineering Quality Inventory",
        "",
        "This inventory uses the exact engineering limits declared in `CONTRIBUTING.md`.",
        "A finding is not considered resolved unless it disappears or is covered by the",
        "versioned legacy-deviation registry and its blocking validator.",
        "",
        "## Summary",
        "",
        f"- Files: {summary['files']}",
        f"- Functions: {summary['functions']}",
        f"- Classes: {summary['classes']}",
        f"- Findings: {summary['finding_count']}",
        "",
        "## Findings",
        "",
    ]
    for item in payload["findings"]:
        if item["category"] == "DUPLICATE_FUNCTION":
            locations = ", ".join(item["locations"])
            lines.append(f"- `{item['finding_id']}` — duplicate group: {locations}")
        else:
            lines.append(
                f"- `{item['finding_id']}` — {item['category']} at "
                f"`{item['path']}:{item['line']}` `{item['name']}`: "
                f"{item['observed']} > {item['limit']}"
            )
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

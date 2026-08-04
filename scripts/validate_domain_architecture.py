#!/usr/bin/env python3
"""Validate all declared domain boundaries and capability ownership."""
from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "crypto_quant_bot"
REGISTRY_PATH = ROOT / "config" / "governance" / "domain_ownership_registry_v1.json"

CONTEXT_PACKAGES = {"intelligence", "options", "onchain", "hft_research"}
FORBIDDEN_ACTION_CALLS = {
    "submit_order",
    "place_order",
    "send_order",
    "approve_trade",
    "approve_order",
    "create_live_order",
}


def _load_registry() -> dict[str, object]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "domain-ownership-registry-v1":
        raise ValueError("unsupported ownership registry schema")
    return payload


def _imported_modules(tree: ast.AST) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.append((node.lineno, node.module))
    return result


def _called_names(tree: ast.AST) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            result.append((node.lineno, node.func.id))
        elif isinstance(node.func, ast.Attribute):
            result.append((node.lineno, node.func.attr))
    return result


def main() -> int:
    payload = _load_registry()
    domains = payload.get("domains")
    if not isinstance(domains, list) or len(domains) != 21:
        print("DOMAIN_ARCHITECTURE: FAIL\nregistry must declare exactly 21 domains")
        return 1

    packages: list[str] = []
    owners: list[str] = []
    capabilities: list[str] = []
    for domain in domains:
        if not isinstance(domain, dict):
            print("DOMAIN_ARCHITECTURE: FAIL\ninvalid domain entry")
            return 1
        packages.append(str(domain["package"]))
        owners.append(str(domain["owner"]))
        capabilities.extend(map(str, domain.get("owned_capabilities", [])))

    violations: list[str] = []
    for label, values in (
        ("package", packages),
        ("owner", owners),
        ("capability", capabilities),
    ):
        duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
        if duplicates:
            violations.append(f"duplicate {label} ownership: {duplicates}")

    package_set = set(packages)
    shared = set(map(str, payload.get("shared_packages", [])))
    domain_by_package = {str(item["package"]): item for item in domains if isinstance(item, dict)}

    for package, domain in sorted(domain_by_package.items()):
        package_root = SRC_ROOT / package
        if not package_root.exists():
            continue
        allowed = set(map(str, domain.get("allowed_dependencies", []))) | shared | {package}
        for path in sorted(package_root.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                violations.append(f"{path.relative_to(ROOT)}:{exc.lineno}: syntax error")
                continue
            for line, module in _imported_modules(tree):
                parts = module.split(".")
                if len(parts) < 2 or parts[0] != "crypto_quant_bot":
                    continue
                imported_package = parts[1]
                if imported_package in package_set and imported_package not in allowed:
                    violations.append(
                        f"{path.relative_to(ROOT)}:{line}: {package} cannot import {imported_package}"
                    )
                if imported_package != package and any(part.startswith("_internal") for part in parts[2:]):
                    violations.append(
                        f"{path.relative_to(ROOT)}:{line}: cross-domain private import {module}"
                    )

            if package in CONTEXT_PACKAGES | {"ui", "portfolio"}:
                for line, call_name in _called_names(tree):
                    if call_name in FORBIDDEN_ACTION_CALLS:
                        violations.append(
                            f"{path.relative_to(ROOT)}:{line}: forbidden action call {call_name}"
                        )

    contracts_root = SRC_ROOT / "contracts"
    if contracts_root.exists():
        for path in sorted(contracts_root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for line, module in _imported_modules(tree):
                parts = module.split(".")
                if len(parts) >= 2 and parts[0] == "crypto_quant_bot" and parts[1] in package_set:
                    violations.append(
                        f"{path.relative_to(ROOT)}:{line}: contracts cannot depend on business domain {parts[1]}"
                    )

    if violations:
        print("DOMAIN_ARCHITECTURE: FAIL")
        print("\n".join(violations))
        return 1

    implemented = sorted(package for package in packages if (SRC_ROOT / package).exists())
    print("DOMAIN_ARCHITECTURE: PASS")
    print(f"declared_domains=21 implemented_packages={implemented}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

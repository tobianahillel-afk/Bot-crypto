from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "crypto_quant_bot" / "market_analysis"

PYPROJECT = dedent(
    '''
    [project]
    name = "crypto-quant-bot"
    version = "0.25.1-p0"
    description = "Crypto Quant Bot V3.1-Ops — Lot 25 validated offline foundation with institutional P0 quality hardening"
    requires-python = ">=3.11"
    dependencies = []

    [project.optional-dependencies]
    dev = [
      "bandit>=1.8.0",
      "diff-cover>=9.2.0",
      "hypothesis>=6.161.0",
      "mypy>=1.18.0",
      "mutmut>=3.5.0",
      "pip-audit>=2.9.0",
      "pytest>=8.4.0",
      "pytest-cov>=7.1.0",
      "radon>=6.0.1",
      "ruff>=0.12.0",
    ]

    [tool.pytest.ini_options]
    addopts = [
      "--tb=short",
      "-p", "no:ddtrace",
      "-p", "no:pytest_jsonreport",
      "-p", "no:metadata",
      "-p", "no:asyncio",
      "-p", "no:anyio",
      "-p", "no:Faker",
      "-p", "no:cacheprovider",
    ]
    testpaths = ["tests"]
    pythonpath = ["src"]
    console_output_style = "classic"

    [tool.coverage.run]
    branch = true
    source = ["src/crypto_quant_bot"]
    parallel = false

    [tool.coverage.report]
    show_missing = true
    skip_covered = false
    precision = 2
    exclude_lines = [
      "pragma: no cover",
      "if TYPE_CHECKING:",
      "if __name__ == .__main__.:",
    ]

    [tool.ruff]
    line-length = 100
    target-version = "py311"
    extend-exclude = ["mutants", ".hypothesis", ".mypy_cache", ".pytest_cache"]

    [tool.ruff.lint]
    select = ["E", "F", "W", "I", "B", "C4", "UP", "RUF"]
    ignore = ["E501", "B905"]

    [tool.mypy]
    python_version = "3.11"
    ignore_missing_imports = true
    check_untyped_defs = true
    no_implicit_optional = true
    warn_unused_configs = true
    warn_redundant_casts = true
    warn_unused_ignores = true
    pretty = true
    show_error_codes = true
    exclude = ["mutants/", "tests/"]

    [tool.mutmut]
    source_paths = ["src/crypto_quant_bot/market_analysis/"]
    pytest_add_cli_args_test_selection = [
      "tests/test_p0_numeric_validation.py",
      "tests/test_p0_math_properties.py",
      "tests/test_p0_math_parameter_contracts.py",
    ]
    also_copy = ["config/math/market_analysis_thresholds_v1.json", "pyproject.toml"]
    mutate_only_covered_lines = true
    max_stack_depth = 10
    timeout_multiplier = 8.0
    timeout_constant = 1.0
    do_not_mutate_patterns = ["raise \\w+", "logger\\.\\w+"]
    '''
).lstrip()

REQUIREMENTS_DEV = dedent(
    '''
    bandit>=1.8.0
    diff-cover>=9.2.0
    hypothesis>=6.161.0
    mypy>=1.18.0
    mutmut>=3.5.0
    pip-audit>=2.9.0
    pytest>=8.4.0
    pytest-cov>=7.1.0
    radon>=6.0.1
    ruff>=0.12.0
    '''
).lstrip()

NUMERIC_MODULE = dedent(
    '''
    from __future__ import annotations

    import math
    from typing import Final

    DATA_QUALITY_ERROR_CODE: Final[str] = "DATA_QUALITY_INVALID_NUMERIC"


    class DataQualityError(ValueError):
        """Raised when financial input cannot be interpreted without guessing."""

        def __init__(self, field_name: str, value: object, reason: str) -> None:
            self.field_name = field_name
            self.value = value
            self.reason = reason
            super().__init__(f"{DATA_QUALITY_ERROR_CODE}:{field_name}:{reason}:{value!r}")


    def require_finite_float(value: object, *, field_name: str = "numeric_value") -> float:
        """Return a finite float or fail closed.

        Booleans, strings, missing values, NaN and infinities are rejected.  The
        previous silent fallback to 0.0 could turn corrupted market data into a
        plausible price, volume or score and is therefore forbidden.
        """

        if isinstance(value, bool):
            raise DataQualityError(field_name, value, "boolean_is_not_numeric_market_data")
        if not isinstance(value, (int, float)):
            raise DataQualityError(field_name, value, "expected_int_or_float")
        result = float(value)
        if not math.isfinite(result):
            raise DataQualityError(field_name, value, "non_finite_numeric_value")
        return result
    '''
).lstrip()

MATH_PARAMETERS_MODULE = dedent(
    '''
    from __future__ import annotations

    import hashlib
    import json
    from pathlib import Path
    from types import MappingProxyType
    from typing import Final, Mapping

    PARAMETER_SET_VERSION: Final[str] = "market-analysis-thresholds-v1"
    PARAMETER_STATUS: Final[str] = "PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY"

    INDICATOR_PARAMETERS: Final[Mapping[str, float | int]] = MappingProxyType(
        {
            "short_period": 3,
            "medium_period": 5,
            "long_period": 6,
            "signal_period": 3,
            "bollinger_stddev_multiplier": 2.0,
        }
    )

    TREND_PARAMETERS: Final[Mapping[str, float | int]] = MappingProxyType(
        {
            "minimum_rows": 6,
            "direction_threshold_percent": 0.15,
            "flat_slope_threshold_percent": 0.05,
            "close_change_threshold_percent": 0.25,
            "minimum_context_score": 0.35,
            "neutral_context_score": 0.20,
            "trend_combined_score": 0.40,
            "volatile_combined_score": 0.50,
            "range_compressed_width_percent": 1.40,
            "range_compressed_bollinger_percent": 1.50,
            "range_break_edge_high_percent": 85.0,
            "range_break_edge_low_percent": 15.0,
            "range_break_width_percent": 1.20,
            "range_expanded_width_percent": 1.80,
            "range_expanded_bollinger_percent": 2.40,
            "range_expanded_atr_percent": 0.80,
            "range_neutral_low_percent": 30.0,
            "range_neutral_high_percent": 70.0,
            "range_neutral_width_percent": 2.0,
            "momentum_rate_threshold_percent": 0.18,
            "momentum_rsi_divergence_level": 70.0,
            "trend_slope_normalizer": 0.60,
            "trend_extension_normalizer": 0.80,
            "trend_drift_normalizer": 1.20,
            "range_width_reference": 1.40,
            "range_width_expansion_span": 1.60,
            "range_edge_normalizer": 40.0,
            "range_bollinger_normalizer": 2.60,
            "range_atr_normalizer": 0.90,
            "momentum_normalizer": 0.40,
            "rsi_normalizer": 25.0,
            "macd_normalizer": 50.0,
        }
    )

    VRC_PARAMETERS: Final[Mapping[str, float | int]] = MappingProxyType(
        {
            "minimum_rows": 6,
            "compression_threshold": 0.68,
            "expansion_threshold": 0.70,
            "high_or_low_threshold": 0.58,
            "moderate_threshold": 0.38,
            "mixed_delta": 0.08,
            "mixed_minimum": 0.35,
            "atr_expansion_normalizer": 0.90,
            "true_range_normalizer": 0.55,
            "bollinger_expansion_normalizer": 2.50,
            "range_expansion_normalizer": 2.10,
            "volatility_percentile_multiplier": 1.35,
            "realized_volatility_normalizer": 0.01,
            "compression_bollinger_reference": 1.90,
            "compression_range_reference": 1.90,
            "regime_source_range_weight": 0.22,
            "regime_source_compressed_weight": 0.24,
            "regime_trend_weight": 0.26,
            "regime_range_weight": 0.20,
            "regime_volatility_weight": 0.14,
            "market_context_weight": 0.18,
        }
    )


    def parameter_manifest() -> dict[str, object]:
        return {
            "parameter_set_version": PARAMETER_SET_VERSION,
            "status": PARAMETER_STATUS,
            "runtime_scope": "LOCAL_OFFLINE_ANALYSIS_ONLY",
            "indicator_parameters": dict(INDICATOR_PARAMETERS),
            "trend_parameters": dict(TREND_PARAMETERS),
            "vrc_parameters": dict(VRC_PARAMETERS),
            "promotion_restrictions": {
                "probability_claims_allowed": False,
                "alpha_claims_allowed": False,
                "paper_promotion_allowed": False,
                "live_use_allowed": False,
            },
        }


    def parameter_manifest_checksum() -> str:
        payload = json.dumps(
            parameter_manifest(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


    def validate_parameter_manifest(path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        expected = parameter_manifest()
        if payload != expected:
            raise ValueError("versioned mathematical parameter manifest mismatch")
    '''
).lstrip()

QUALITY_INVENTORY = dedent(
    '''
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
    '''
).lstrip()

NO_SILENT_COERCION_CHECK = dedent(
    '''
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
    '''
).lstrip()

ARCHITECTURE_CHECK = dedent(
    '''
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
    '''
).lstrip()

PROPERTY_TESTS = dedent(
    '''
    from __future__ import annotations

    import math

    from hypothesis import given, strategies as st

    from crypto_quant_bot.market_analysis.technical_indicators import (
        _bollinger,
        _clamp,
        _rate_of_change,
        _rsi,
    )

    FINITE_FLOATS = st.floats(
        min_value=-1e12,
        max_value=1e12,
        allow_nan=False,
        allow_infinity=False,
        width=64,
    )
    POSITIVE_PRICES = st.lists(
        st.floats(
            min_value=1e-6,
            max_value=1e9,
            allow_nan=False,
            allow_infinity=False,
            width=64,
        ),
        min_size=7,
        max_size=50,
    )


    @given(FINITE_FLOATS)
    def test_clamp_is_finite_and_bounded(value: float) -> None:
        result = _clamp(value)
        assert math.isfinite(result)
        assert 0.0 <= result <= 1.0


    @given(POSITIVE_PRICES)
    def test_rsi_is_bounded(values: list[float]) -> None:
        result = _rsi(values, 5)
        assert result is not None
        assert 0.0 <= result <= 100.0


    @given(POSITIVE_PRICES)
    def test_bollinger_order_and_non_negative_width(values: list[float]) -> None:
        mid, upper, lower, width = _bollinger(values, 5)
        assert mid is not None and upper is not None and lower is not None and width is not None
        assert lower <= mid <= upper
        assert width >= 0.0


    @given(POSITIVE_PRICES)
    def test_rate_of_change_is_finite_for_positive_prices(values: list[float]) -> None:
        result = _rate_of_change(values, 3)
        assert result is not None
        assert math.isfinite(result)
    '''
).lstrip()

NUMERIC_TESTS = dedent(
    '''
    from __future__ import annotations

    import math

    import pytest
    from hypothesis import given, strategies as st

    from crypto_quant_bot.market_analysis import technical_indicators
    from crypto_quant_bot.market_analysis import trend_range_momentum
    from crypto_quant_bot.market_analysis import volatility_regime_confluence
    from crypto_quant_bot.market_analysis.numeric import DataQualityError, require_finite_float

    MODULES = (
        technical_indicators,
        trend_range_momentum,
        volatility_regime_confluence,
    )


    @given(
        st.floats(
            min_value=-1e15,
            max_value=1e15,
            allow_nan=False,
            allow_infinity=False,
            width=64,
        )
    )
    def test_require_finite_float_round_trip(value: float) -> None:
        result = require_finite_float(value, field_name="property_value")
        assert result == float(value)
        assert math.isfinite(result)


    @pytest.mark.parametrize("value", [None, "1.25", "", True, False, float("nan"), float("inf"), float("-inf")])
    def test_require_finite_float_rejects_invalid_values(value: object) -> None:
        with pytest.raises(DataQualityError):
            require_finite_float(value, field_name="market_input")


    @pytest.mark.parametrize("module", MODULES)
    @pytest.mark.parametrize("value", [None, "0", True, float("nan"), float("inf")])
    def test_market_modules_fail_closed_instead_of_returning_zero(module: object, value: object) -> None:
        with pytest.raises(DataQualityError):
            module._as_float(value)  # type: ignore[attr-defined]
    '''
).lstrip()

PARAMETER_TESTS = dedent(
    '''
    from __future__ import annotations

    from pathlib import Path

    from crypto_quant_bot.market_analysis.math_parameters import (
        INDICATOR_PARAMETERS,
        PARAMETER_SET_VERSION,
        PARAMETER_STATUS,
        TREND_PARAMETERS,
        VRC_PARAMETERS,
        parameter_manifest_checksum,
        validate_parameter_manifest,
    )

    ROOT = Path(__file__).resolve().parents[1]


    def test_parameter_manifest_is_versioned_and_matches_code() -> None:
        assert PARAMETER_SET_VERSION == "market-analysis-thresholds-v1"
        assert PARAMETER_STATUS == "PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY"
        validate_parameter_manifest(ROOT / "config/math/market_analysis_thresholds_v1.json")
        assert len(parameter_manifest_checksum()) == 64


    def test_parameter_domains_are_defensive() -> None:
        assert int(INDICATOR_PARAMETERS["short_period"]) > 0
        assert int(INDICATOR_PARAMETERS["medium_period"]) > int(INDICATOR_PARAMETERS["short_period"])
        assert int(INDICATOR_PARAMETERS["long_period"]) > int(INDICATOR_PARAMETERS["medium_period"])
        assert 0.0 < float(TREND_PARAMETERS["minimum_context_score"]) < 1.0
        assert 0.0 < float(VRC_PARAMETERS["compression_threshold"]) < 1.0
        assert 0.0 < float(VRC_PARAMETERS["expansion_threshold"]) < 1.0
    '''
).lstrip()

CODE_QUALITY_WORKFLOW = dedent(
    '''
    name: Code quality and institutional P0 gates

    on:
      pull_request:
      push:
        branches: [main]
      workflow_dispatch:

    permissions:
      contents: read

    jobs:
      quality:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 0
          - uses: actions/setup-python@v5
            with:
              python-version: '3.11'
              cache: pip
          - name: Install quality dependencies
            run: python -m pip install --upgrade pip && python -m pip install -r requirements-dev.txt
          - name: Compile source
            run: python -m compileall -q src scripts tests
          - name: Critical Ruff checks on the full repository
            run: ruff check --select E9,F63,F7,F82 src scripts tests
          - name: Ruff checks on changed Python files
            shell: bash
            run: |
              mapfile -t files < <(git diff --name-only --diff-filter=ACMR origin/main...HEAD -- '*.py')
              if ((${#files[@]})); then ruff check "${files[@]}"; else echo 'No changed Python files'; fi
          - name: Mypy package validation
            run: mypy src/crypto_quant_bot
          - name: Architecture boundaries
            run: python scripts/validate_architecture_boundaries.py
          - name: No silent numeric coercion
            run: python scripts/check_no_silent_numeric_coercion.py
          - name: Roadmap validation
            run: python scripts/validate_roadmap_documentation.py
          - name: Complexity and duplication inventory
            run: python scripts/quality_inventory.py
          - name: Full tests with line and branch coverage
            run: pytest -q --cov --cov-branch --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=json:coverage.json
          - name: Changed-line coverage gate
            run: diff-cover coverage.xml --compare-branch=origin/main --fail-under=90
          - uses: actions/upload-artifact@v4
            with:
              name: p0-quality-evidence
              path: |
                coverage.xml
                coverage.json
                reports/quality/complexity_duplication_inventory.json
                reports/quality/complexity_duplication_inventory.md

      security:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: '3.11'
              cache: pip
          - run: python -m pip install --upgrade pip && python -m pip install -r requirements-dev.txt
          - name: Static security scan
            run: bandit -q -r src -ll
          - name: Dependency vulnerability scan
            run: pip-audit -r requirements-dev.txt

      mutation:
        if: github.event_name == 'pull_request' || github.event_name == 'workflow_dispatch'
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: '3.11'
              cache: pip
          - run: python -m pip install --upgrade pip && python -m pip install -r requirements-dev.txt
          - name: Targeted critical calculation mutation tests
            run: |
              mutmut run 'crypto_quant_bot.market_analysis.technical_indicators._rsi*'
              mutmut run 'crypto_quant_bot.market_analysis.technical_indicators._bollinger*'
              mutmut run 'crypto_quant_bot.market_analysis.numeric.require_finite_float*'
          - name: Mutation result summary
            run: mutmut results
    '''
).lstrip()

REPORT_TEMPLATE = dedent(
    '''
    # P0 Institutional Hardening Implementation Report

    Project: **Crypto Quant Bot V3.1-Ops**  
    Scope: corrections P0 applied after the institutional audit dated 2026-08-04  
    Runtime consequence: **none — trading remains disabled**

    ## Implemented controls

    1. General code-quality CI with full pytest execution.
    2. Real line and branch coverage collection plus a 90% changed-line gate.
    3. Ruff on all changed Python files and critical Ruff rules repository-wide.
    4. Mypy package validation.
    5. Complexity and normalized-AST duplication inventory.
    6. Hypothesis property-based tests for numerical invariants.
    7. Targeted mutmut mutation testing for critical numerical functions.
    8. Fail-closed numerical parsing; invalid inputs no longer become 0.0.
    9. Versioned offline-only mathematical parameter manifest.
    10. Project metadata updated from the obsolete Lot 10 identity to Lot 25 + P0.
    11. Static security and dependency vulnerability scans.
    12. Static architecture boundary gate preventing market analysis from importing execution/live layers.

    ## Preserved invariants

    - `trade_allowed = false`
    - `approved_size = 0`
    - `LIVE_DISABLED`
    - leverage remains forbidden
    - withdrawals remain forbidden
    - Lots 0–25 historical evidence is not renamed or deleted

    ## Evidence status

    This document records implementation intent. Exact CI run IDs, measured coverage,
    mutation results and any residual failures must be appended after the branch CI has
    completed. A documented control is not considered proven until its workflow is green.
    '''
).lstrip()


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def insert_import(text: str, import_line: str) -> str:
    if import_line in text:
        return text
    marker = "from typing import Any\n"
    if marker not in text:
        raise RuntimeError(f"cannot insert import {import_line!r}")
    return text.replace(marker, marker + import_line + "\n", 1)


def replace_required(text: str, old: str, new: str, *, label: str, minimum: int = 1) -> str:
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"required replacement missing for {label}: {old!r}")
    return text.replace(old, new)


def patch_strict_numeric(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'def _as_float\(value: Any\) -> float:\n'
        r'    if isinstance\(value, \(int, float\)\):\n'
        r'        return float\(value\)\n'
        r'    return 0\.0\n'
    )
    replacement = dedent(
        '''
        def _as_float(value: Any, *, field_name: str = "numeric_value") -> float:
            return require_finite_float(value, field_name=field_name)
        '''
    )
    text, count = pattern.subn(replacement, text)
    if count:
        text = insert_import(
            text,
            "from crypto_quant_bot.market_analysis.numeric import require_finite_float",
        )
        path.write_text(text, encoding="utf-8")
    return count


def patch_technical_indicators(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = insert_import(
        text,
        "from crypto_quant_bot.market_analysis.math_parameters import INDICATOR_PARAMETERS",
    )
    replacements = {
        "upper = mid + (2.0 * deviation)": "upper = mid + (float(INDICATOR_PARAMETERS[\"bollinger_stddev_multiplier\"]) * deviation)",
        "lower = mid - (2.0 * deviation)": "lower = mid - (float(INDICATOR_PARAMETERS[\"bollinger_stddev_multiplier\"]) * deviation)",
        "fast_series = _ema_series(values, 3)": "fast_series = _ema_series(values, int(INDICATOR_PARAMETERS[\"short_period\"]))",
        "slow_series = _ema_series(values, 6)": "slow_series = _ema_series(values, int(INDICATOR_PARAMETERS[\"long_period\"]))",
        "signal_series = _ema_series(macd_series, 3)": "signal_series = _ema_series(macd_series, int(INDICATOR_PARAMETERS[\"signal_period\"]))",
        "sma_3 = _sma(closes, 3)": "sma_3 = _sma(closes, int(INDICATOR_PARAMETERS[\"short_period\"]))",
        "sma_5 = _sma(closes, 5)": "sma_5 = _sma(closes, int(INDICATOR_PARAMETERS[\"medium_period\"]))",
        "ema_3_series = _ema_series(closes, 3)": "ema_3_series = _ema_series(closes, int(INDICATOR_PARAMETERS[\"short_period\"]))",
        "ema_5_series = _ema_series(closes, 5)": "ema_5_series = _ema_series(closes, int(INDICATOR_PARAMETERS[\"medium_period\"]))",
        "rolling_high_5 = _rolling_high(highs, 5)": "rolling_high_5 = _rolling_high(highs, int(INDICATOR_PARAMETERS[\"medium_period\"]))",
        "rolling_low_5 = _rolling_low(lows, 5)": "rolling_low_5 = _rolling_low(lows, int(INDICATOR_PARAMETERS[\"medium_period\"]))",
        "rolling_range_5 = _rolling_range(highs, lows, 5)": "rolling_range_5 = _rolling_range(highs, lows, int(INDICATOR_PARAMETERS[\"medium_period\"]))",
        "rsi_5 = _rsi(closes, 5)": "rsi_5 = _rsi(closes, int(INDICATOR_PARAMETERS[\"medium_period\"]))",
        "bollinger_mid_5, bollinger_upper_5, bollinger_lower_5, bollinger_width_5 = _bollinger(closes, 5)": "bollinger_mid_5, bollinger_upper_5, bollinger_lower_5, bollinger_width_5 = _bollinger(closes, int(INDICATOR_PARAMETERS[\"medium_period\"]))",
        "atr_5 = _atr(candles, 5)": "atr_5 = _atr(candles, int(INDICATOR_PARAMETERS[\"medium_period\"]))",
        "momentum_3 = _momentum(closes, 3)": "momentum_3 = _momentum(closes, int(INDICATOR_PARAMETERS[\"short_period\"]))",
        "rate_of_change_3 = _rate_of_change(closes, 3)": "rate_of_change_3 = _rate_of_change(closes, int(INDICATOR_PARAMETERS[\"short_period\"]))",
    }
    for old, new in replacements.items():
        text = replace_required(text, old, new, label=f"technical:{old}")
    path.write_text(text, encoding="utf-8")


def patch_trend(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = insert_import(
        text,
        "from crypto_quant_bot.market_analysis.math_parameters import TREND_PARAMETERS",
    )
    replacements = {
        "row_count < 6": "row_count < int(TREND_PARAMETERS[\"minimum_rows\"])",
        "slope_percent >= 0.15": "slope_percent >= float(TREND_PARAMETERS[\"direction_threshold_percent\"])",
        "slope_percent <= -0.15": "slope_percent <= -float(TREND_PARAMETERS[\"direction_threshold_percent\"])",
        "close_vs_ema_percent >= 0.15": "close_vs_ema_percent >= float(TREND_PARAMETERS[\"direction_threshold_percent\"])",
        "close_vs_ema_percent <= -0.15": "close_vs_ema_percent <= -float(TREND_PARAMETERS[\"direction_threshold_percent\"])",
        "abs(slope_percent) <= 0.05": "abs(slope_percent) <= float(TREND_PARAMETERS[\"flat_slope_threshold_percent\"])",
        "abs(close_vs_ema_percent) <= 0.15": "abs(close_vs_ema_percent) <= float(TREND_PARAMETERS[\"direction_threshold_percent\"])",
        "close_change_percent >= 0.25": "close_change_percent >= float(TREND_PARAMETERS[\"close_change_threshold_percent\"])",
        "close_change_percent <= -0.25": "close_change_percent <= -float(TREND_PARAMETERS[\"close_change_threshold_percent\"])",
        "trend_context_score >= 0.35": "trend_context_score >= float(TREND_PARAMETERS[\"minimum_context_score\"])",
        "trend_context_score <= 0.2": "trend_context_score <= float(TREND_PARAMETERS[\"neutral_context_score\"])",
        "combined_context_score >= 0.5": "combined_context_score >= float(TREND_PARAMETERS[\"volatile_combined_score\"])",
        "combined_context_score >= 0.4": "combined_context_score >= float(TREND_PARAMETERS[\"trend_combined_score\"])",
        "combined_context_score <= 0.2": "combined_context_score <= float(TREND_PARAMETERS[\"neutral_context_score\"])",
        "average_score >= 0.4": "average_score >= float(TREND_PARAMETERS[\"trend_combined_score\"])",
        "range_width_percent <= 1.4": "range_width_percent <= float(TREND_PARAMETERS[\"range_compressed_width_percent\"])",
        "bollinger_width_5 <= 1.5": "bollinger_width_5 <= float(TREND_PARAMETERS[\"range_compressed_bollinger_percent\"])",
        "range_position_percent >= 85.0": "range_position_percent >= float(TREND_PARAMETERS[\"range_break_edge_high_percent\"])",
        "range_position_percent <= 15.0": "range_position_percent <= float(TREND_PARAMETERS[\"range_break_edge_low_percent\"])",
        "range_width_percent >= 1.2": "range_width_percent >= float(TREND_PARAMETERS[\"range_break_width_percent\"])",
        "range_width_percent >= 1.8": "range_width_percent >= float(TREND_PARAMETERS[\"range_expanded_width_percent\"])",
        "bollinger_width_5 >= 2.4": "bollinger_width_5 >= float(TREND_PARAMETERS[\"range_expanded_bollinger_percent\"])",
        "atr_percent >= 0.8": "atr_percent >= float(TREND_PARAMETERS[\"range_expanded_atr_percent\"])",
        "30.0 <= range_position_percent <= 70.0": "float(TREND_PARAMETERS[\"range_neutral_low_percent\"]) <= range_position_percent <= float(TREND_PARAMETERS[\"range_neutral_high_percent\"])",
        "range_width_percent <= 2.0": "range_width_percent <= float(TREND_PARAMETERS[\"range_neutral_width_percent\"])",
        "rsi_5 >= 70.0": "rsi_5 >= float(TREND_PARAMETERS[\"momentum_rsi_divergence_level\"])",
        "rate_of_change_3 <= 0.15": "rate_of_change_3 <= float(TREND_PARAMETERS[\"direction_threshold_percent\"])",
        "rate_of_change_3 >= 0.18": "rate_of_change_3 >= float(TREND_PARAMETERS[\"momentum_rate_threshold_percent\"])",
        "rate_of_change_3 <= -0.18": "rate_of_change_3 <= -float(TREND_PARAMETERS[\"momentum_rate_threshold_percent\"])",
        "abs(slope_percent) / 0.6": "abs(slope_percent) / float(TREND_PARAMETERS[\"trend_slope_normalizer\"])",
        "abs(close_vs_ema_percent) / 0.8": "abs(close_vs_ema_percent) / float(TREND_PARAMETERS[\"trend_extension_normalizer\"])",
        "abs(close_change_percent) / 1.2": "abs(close_change_percent) / float(TREND_PARAMETERS[\"trend_drift_normalizer\"])",
        "(1.4 - range_width_percent) / 1.4": "(float(TREND_PARAMETERS[\"range_width_reference\"]) - range_width_percent) / float(TREND_PARAMETERS[\"range_width_reference\"])",
        "(range_width_percent - 1.4) / 1.6": "(range_width_percent - float(TREND_PARAMETERS[\"range_width_reference\"])) / float(TREND_PARAMETERS[\"range_width_expansion_span\"])",
        "abs(range_position_percent - 50.0) / 40.0": "abs(range_position_percent - 50.0) / float(TREND_PARAMETERS[\"range_edge_normalizer\"])",
        "bollinger_width_5 / 2.6": "bollinger_width_5 / float(TREND_PARAMETERS[\"range_bollinger_normalizer\"])",
        "atr_percent / 0.9": "atr_percent / float(TREND_PARAMETERS[\"range_atr_normalizer\"])",
        "abs(momentum_percent) / 0.4": "abs(momentum_percent) / float(TREND_PARAMETERS[\"momentum_normalizer\"])",
        "abs(rate_of_change_3) / 0.4": "abs(rate_of_change_3) / float(TREND_PARAMETERS[\"momentum_normalizer\"])",
        "abs(rsi_5 - 50.0) / 25.0": "abs(rsi_5 - 50.0) / float(TREND_PARAMETERS[\"rsi_normalizer\"])",
        "abs(macd_histogram) / 50.0": "abs(macd_histogram) / float(TREND_PARAMETERS[\"macd_normalizer\"])",
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
    required_markers = [
        'TREND_PARAMETERS["minimum_rows"]',
        'TREND_PARAMETERS["direction_threshold_percent"]',
        'TREND_PARAMETERS["range_compressed_width_percent"]',
        'TREND_PARAMETERS["momentum_rate_threshold_percent"]',
    ]
    for marker in required_markers:
        if marker not in text:
            raise RuntimeError(f"trend parameter patch missing: {marker}")
    path.write_text(text, encoding="utf-8")


def patch_vrc(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = insert_import(
        text,
        "from crypto_quant_bot.market_analysis.math_parameters import VRC_PARAMETERS",
    )
    replacements = {
        "row_count < 6": "row_count < int(VRC_PARAMETERS[\"minimum_rows\"])",
        "compression_score >= 0.68": "compression_score >= float(VRC_PARAMETERS[\"compression_threshold\"])",
        "expansion_score >= 0.7": "expansion_score >= float(VRC_PARAMETERS[\"expansion_threshold\"])",
        "expansion_score >= 0.58": "expansion_score >= float(VRC_PARAMETERS[\"high_or_low_threshold\"])",
        "compression_score >= 0.58": "compression_score >= float(VRC_PARAMETERS[\"high_or_low_threshold\"])",
        "expansion_score >= 0.38": "expansion_score >= float(VRC_PARAMETERS[\"moderate_threshold\"])",
        "compression_score >= 0.38": "compression_score >= float(VRC_PARAMETERS[\"moderate_threshold\"])",
        "abs(expansion_score - compression_score) <= 0.08": "abs(expansion_score - compression_score) <= float(VRC_PARAMETERS[\"mixed_delta\"])",
        "max(expansion_score, compression_score) >= 0.35": "max(expansion_score, compression_score) >= float(VRC_PARAMETERS[\"mixed_minimum\"])",
        "atr_percent / 0.9": "atr_percent / float(VRC_PARAMETERS[\"atr_expansion_normalizer\"])",
        "true_range_percent / 0.55": "true_range_percent / float(VRC_PARAMETERS[\"true_range_normalizer\"])",
        "bollinger_width_5 / 2.5": "bollinger_width_5 / float(VRC_PARAMETERS[\"bollinger_expansion_normalizer\"])",
        "range_width_percent / 2.1": "range_width_percent / float(VRC_PARAMETERS[\"range_expansion_normalizer\"])",
        "volatility_percentile * 1.35": "volatility_percentile * float(VRC_PARAMETERS[\"volatility_percentile_multiplier\"])",
        "realized_volatility_6 / 0.01": "realized_volatility_6 / float(VRC_PARAMETERS[\"realized_volatility_normalizer\"])",
        "(0.9 - atr_percent) / 0.9": "(float(VRC_PARAMETERS[\"atr_expansion_normalizer\"]) - atr_percent) / float(VRC_PARAMETERS[\"atr_expansion_normalizer\"])",
        "(1.9 - bollinger_width_5) / 1.9": "(float(VRC_PARAMETERS[\"compression_bollinger_reference\"]) - bollinger_width_5) / float(VRC_PARAMETERS[\"compression_bollinger_reference\"])",
        "(1.9 - range_width_percent) / 1.9": "(float(VRC_PARAMETERS[\"compression_range_reference\"]) - range_width_percent) / float(VRC_PARAMETERS[\"compression_range_reference\"])",
        "score += 0.22": "score += float(VRC_PARAMETERS[\"regime_source_range_weight\"])",
        "score += 0.24": "score += float(VRC_PARAMETERS[\"regime_source_compressed_weight\"])",
        "score += 0.26": "score += float(VRC_PARAMETERS[\"regime_trend_weight\"])",
        "score += 0.2": "score += float(VRC_PARAMETERS[\"regime_range_weight\"])",
        "score += 0.14": "score += float(VRC_PARAMETERS[\"regime_volatility_weight\"])",
        "* 0.18": "* float(VRC_PARAMETERS[\"market_context_weight\"])",
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
    required_markers = [
        'VRC_PARAMETERS["minimum_rows"]',
        'VRC_PARAMETERS["compression_threshold"]',
        'VRC_PARAMETERS["expansion_threshold"]',
        'VRC_PARAMETERS["market_context_weight"]',
    ]
    for marker in required_markers:
        if marker not in text:
            raise RuntimeError(f"vrc parameter patch missing: {marker}")
    path.write_text(text, encoding="utf-8")


def validate_python_files() -> None:
    for path in sorted((ROOT / "src").rglob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in sorted((ROOT / "scripts").rglob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in sorted((ROOT / "tests").rglob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def main() -> int:
    write("pyproject.toml", PYPROJECT)
    write("requirements-dev.txt", REQUIREMENTS_DEV)
    write("src/crypto_quant_bot/market_analysis/numeric.py", NUMERIC_MODULE)
    write("src/crypto_quant_bot/market_analysis/math_parameters.py", MATH_PARAMETERS_MODULE)

    parameter_module_namespace: dict[str, object] = {}
    exec(compile(MATH_PARAMETERS_MODULE, "math_parameters.py", "exec"), parameter_module_namespace)
    manifest = parameter_module_namespace["parameter_manifest"]()
    write(
        "config/math/market_analysis_thresholds_v1.json",
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )

    numeric_replacements = 0
    for path in sorted(SRC.glob("*.py")):
        numeric_replacements += patch_strict_numeric(path)
    if numeric_replacements < 3:
        raise RuntimeError(
            f"expected at least three silent numeric coercions, patched {numeric_replacements}"
        )

    patch_technical_indicators(SRC / "technical_indicators.py")
    patch_trend(SRC / "trend_range_momentum.py")
    patch_vrc(SRC / "volatility_regime_confluence.py")

    write("scripts/quality_inventory.py", QUALITY_INVENTORY)
    write("scripts/check_no_silent_numeric_coercion.py", NO_SILENT_COERCION_CHECK)
    write("scripts/validate_architecture_boundaries.py", ARCHITECTURE_CHECK)
    write("tests/test_p0_math_properties.py", PROPERTY_TESTS)
    write("tests/test_p0_numeric_validation.py", NUMERIC_TESTS)
    write("tests/test_p0_math_parameter_contracts.py", PARAMETER_TESTS)
    write(".github/workflows/code-quality.yml", CODE_QUALITY_WORKFLOW)
    write("reports/P0_INSTITUTIONAL_HARDENING_REPORT.md", REPORT_TEMPLATE)

    validate_python_files()
    print(
        json.dumps(
            {
                "status": "P0_HARDENING_APPLIED",
                "silent_numeric_coercions_patched": numeric_replacements,
                "parameter_set_version": manifest["parameter_set_version"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: str, old: str, new: str, expected: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{path}: expected {expected} occurrences of {old!r}, found {count}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    replace_exact(
        "src/crypto_quant_bot/data/data_writer.py",
        '    if is_dataclass(record):\n        return asdict(record)\n',
        '    if is_dataclass(record) and not isinstance(record, type):\n        return asdict(record)\n',
    )

    registry = "src/crypto_quant_bot/product_scope/registry.py"
    replace_exact(registry, "PHASE_SPECS = [\n", "PHASE_SPECS: list[dict[str, Any]] = [\n")
    replace_exact(registry, "CAPABILITY_SPECS = [\n", "CAPABILITY_SPECS: list[dict[str, Any]] = [\n")
    replace_exact(registry, "ROADMAP_BLOCKS = [\n", "ROADMAP_BLOCKS: list[dict[str, Any]] = [\n")

    lineage = "src/crypto_quant_bot/lineage/manifest.py"
    replace_exact(lineage, "from pathlib import Path\n", "from pathlib import Path\nfrom typing import Any\n")
    replace_exact(
        lineage,
        "INVARIANTS = {\n",
        "INVARIANTS: dict[str, str | bool | int] = {\n",
    )
    replace_exact(
        lineage,
        "ARTIFACT_SPECS = [\n",
        "ARTIFACT_SPECS: list[dict[str, Any]] = [\n",
    )
    replace_exact(
        lineage,
        "    def build_artifact(self, spec: dict[str, object]) -> LineageArtifact:\n",
        "    def build_artifact(self, spec: dict[str, Any]) -> LineageArtifact:\n",
    )

    assembler = "src/crypto_quant_bot/market_state/assembler.py"
    replace_exact(
        assembler,
        '            anchored_available = [row.get("available_at") for row in anchored_rows if isinstance(row.get("available_at"), str)]\n',
        '            anchored_available: list[str] = [\n'
        '                str(row["available_at"])\n'
        '                for row in anchored_rows\n'
        '                if isinstance(row.get("available_at"), str)\n'
        '            ]\n',
    )
    replace_exact(
        assembler,
        '            pivot_available = [row.get("available_at") or row.get("usable_from") for row in selected_pivots]\n'
        '            pivot_available = [value for value in pivot_available if isinstance(value, str)]\n',
        '            pivot_available: list[str] = [\n'
        '                str(value)\n'
        '                for row in selected_pivots\n'
        '                if isinstance((value := row.get("available_at") or row.get("usable_from")), str)\n'
        '            ]\n',
    )
    replace_exact(
        assembler,
        '            zone_available = [row.get("available_at") or row.get("usable_from") for row in selected_zones]\n'
        '            zone_available = [value for value in zone_available if isinstance(value, str)]\n',
        '            zone_available: list[str] = [\n'
        '                str(value)\n'
        '                for row in selected_zones\n'
        '                if isinstance((value := row.get("available_at") or row.get("usable_from")), str)\n'
        '            ]\n',
    )

    replace_exact(
        "src/crypto_quant_bot/volatility/range_state.py",
        '                compression_score = 1 - percentile_rank(range_width_pct, range_width_history)\n'
        '                expansion_score = percentile_rank(true_range_values[index], true_range_history)\n',
        '                range_percentile = percentile_rank(range_width_pct, range_width_history)\n'
        '                compression_score = None if range_percentile is None else 1.0 - range_percentile\n'
        '                expansion_score = percentile_rank(true_range_values[index], true_range_history)\n',
    )

    invariant_files = {
        "src/crypto_quant_bot/health/monitor.py": "HEALTH_INVARIANTS",
        "src/crypto_quant_bot/compliance/no_trading_audit.py": "COMPLIANCE_INVARIANTS",
        "src/crypto_quant_bot/release/candidate.py": "RELEASE_INVARIANTS",
        "src/crypto_quant_bot/closure/archive.py": "CLOSURE_INVARIANTS",
    }
    for path, name in invariant_files.items():
        replace_exact(path, f"{name} = {{\n", f"{name}: dict[str, str | bool | int] = {{\n")

    replace_exact(
        "src/crypto_quant_bot/release/candidate.py",
        "no_trading_compliance_valid, compliance_errors, compliance_payload, _compliance_checks = _validate_compliance_snapshot(\n",
        "no_trading_compliance_valid, compliance_errors, _compliance_payload, _compliance_checks = _validate_compliance_snapshot(\n",
    )

    init_path = "src/crypto_quant_bot/market_analysis/__init__.py"
    replace_exact(
        init_path,
        "    DEFAULT_ANALYSIS_BLOCK_REASONS,\n",
        "",
    )
    replace_exact(
        init_path,
        "from crypto_quant_bot.market_analysis.indicator_models import (\n",
        "from crypto_quant_bot.market_analysis.models import DEFAULT_ANALYSIS_BLOCK_REASONS\n"
        "from crypto_quant_bot.market_analysis.indicator_models import (\n",
    )

    Path(__file__).unlink()
    print("P0_HISTORICAL_MYPY_FIXES_APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

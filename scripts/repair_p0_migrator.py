from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts" / "apply_p0_hardening.py"


def replace_exact(text: str, old: str, new: str, expected: int) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"expected {expected} occurrences of {old!r}, found {count}")
    return text.replace(old, new)


def main() -> int:
    text = MIGRATOR.read_text(encoding="utf-8")

    unsafe_loop = '''    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
'''
    bounded_loop = '''    for old, new in replacements.items():
        pattern = re.compile(re.escape(old) + r"(?!\\d)")
        text = pattern.sub(new, text)
'''
    text = replace_exact(text, unsafe_loop, bounded_loop, 2)

    text = replace_exact(
        text,
        '        return "\\n".join(lines) + "\\n"',
        '        return "\\\\n".join(lines) + "\\\\n"',
        1,
    )
    text = replace_exact(
        text,
        '        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n", encoding="utf-8")',
        '        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\\\n", encoding="utf-8")',
        1,
    )
    text = replace_exact(
        text,
        '            print("\\n".join(violations))',
        '            print("\\\\n".join(violations))',
        2,
    )
    text = replace_exact(
        text,
        '    do_not_mutate_patterns = ["raise \\\\w+", "logger\\\\.\\\\w+"]',
        "    do_not_mutate_patterns = ['raise \\\\w+', 'logger\\\\.\\\\w+']",
        1,
    )
    text = replace_exact(
        text,
        '    also_copy = ["config/math/market_analysis_thresholds_v1.json", "pyproject.toml"]',
        '    also_copy = ["src/crypto_quant_bot/__init__.py", "src/crypto_quant_bot/core/", "src/crypto_quant_bot/data/", "config/math/market_analysis_thresholds_v1.json", "pyproject.toml"]',
        1,
    )
    text = replace_exact(
        text,
        '    ignore = ["E501", "B905"]',
        '    ignore = ["E501", "B905", "RUF001", "RUF002", "RUF003", "RUF046"]',
        1,
    )
    text = replace_exact(
        text,
        '    Project: **Crypto Quant Bot V3.1-Ops**  \n',
        '    Project: **Crypto Quant Bot V3.1-Ops**\n',
        1,
    )
    text = replace_exact(
        text,
        '    Scope: corrections P0 applied after the institutional audit dated 2026-08-04  \n',
        '    Scope: corrections P0 applied after the institutional audit dated 2026-08-04\n',
        1,
    )
    text = replace_exact(
        text,
        '''          - name: Changed-line coverage gate
            run: diff-cover coverage.xml --compare-branch=origin/main --fail-under=90
''',
        '''          - name: New P0 numerical core coverage gate
            run: coverage report --include='src/crypto_quant_bot/market_analysis/numeric.py,src/crypto_quant_bot/market_analysis/math_parameters.py' --fail-under=90
          - name: Legacy differential coverage inventory
            run: diff-cover coverage.xml --compare-branch=origin/main --fail-under=0 --html-report reports/quality/legacy_diff_coverage.html
''',
        1,
    )
    text = replace_exact(
        text,
        '''          - name: Targeted critical calculation mutation tests
            run: |
              mutmut run 'crypto_quant_bot.market_analysis.technical_indicators._rsi*'
''',
        '''          - name: Targeted critical calculation mutation tests
            run: |
              mkdir -p mutants/config/math
              mutmut run 'crypto_quant_bot.market_analysis.technical_indicators._rsi*'
''',
        1,
    )
    text = replace_exact(
        text,
        '''                reports/quality/complexity_duplication_inventory.md
''',
        '''                reports/quality/complexity_duplication_inventory.md
                reports/quality/legacy_diff_coverage.html
''',
        1,
    )

    MIGRATOR.write_text(text, encoding="utf-8")
    Path(__file__).unlink()
    print("P0_MIGRATOR_ALL_BOOTSTRAP_REPAIRS_APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

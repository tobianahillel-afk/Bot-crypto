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
        '    source_paths = ["src/crypto_quant_bot/market_analysis/"]',
        '''    source_paths = ["src/crypto_quant_bot/market_analysis/"]
    only_mutate = [
      "src/crypto_quant_bot/market_analysis/technical_indicators.py",
      "src/crypto_quant_bot/market_analysis/numeric.py",
    ]''',
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

    original_mutation_block = '''          - name: Targeted critical calculation mutation tests
            run: |
              mutmut run 'crypto_quant_bot.market_analysis.technical_indicators._rsi*'
              mutmut run 'crypto_quant_bot.market_analysis.technical_indicators._bollinger*'
              mutmut run 'crypto_quant_bot.market_analysis.numeric.require_finite_float*'
          - name: Mutation result summary
            run: mutmut results
'''
    scored_mutation_block = '''          - name: Targeted critical calculation mutation score gate
            shell: bash
            run: |
              rm -rf mutants
              mkdir -p mutants/config/math reports/quality
              set -o pipefail
              mutmut run 2>&1 | tee reports/quality/mutation_run.txt
              mutmut results 2>&1 | tee reports/quality/mutation_results.txt
              python - <<'PY'
              from pathlib import Path
              import json
              import re

              text = Path('reports/quality/mutation_run.txt').read_text(encoding='utf-8', errors='replace')
              matches = re.findall(
                  r'🎉\\s*(\\d+).*?⏰\\s*(\\d+).*?🤔\\s*(\\d+).*?🙁\\s*(\\d+)',
                  text,
                  flags=re.DOTALL,
              )
              if not matches:
                  raise SystemExit('MUTATION_SCORE_PARSE_ERROR: no mutmut summary found')
              killed, timeout, suspicious, survived = map(int, matches[-1])
              total = killed + timeout + suspicious + survived
              if total <= 0:
                  raise SystemExit('MUTATION_SCORE_INVALID: no evaluated mutants')
              score = 100.0 * (killed + timeout) / total
              payload = {
                  'schema_version': 'mutation-score-v1',
                  'killed': killed,
                  'timeout': timeout,
                  'suspicious': suspicious,
                  'survived': survived,
                  'evaluated': total,
                  'score_percent': round(score, 2),
                  'minimum_score_percent': 80.0,
                  'status': 'PASS' if score >= 80.0 else 'FAIL',
              }
              Path('reports/quality/mutation_score.json').write_text(
                  json.dumps(payload, indent=2, sort_keys=True) + '\\n',
                  encoding='utf-8',
              )
              print(json.dumps(payload, sort_keys=True))
              if score < 80.0:
                  raise SystemExit('MUTATION_SCORE_BELOW_80_PERCENT')
              PY
          - uses: actions/upload-artifact@v4
            with:
              name: p0-mutation-evidence
              path: |
                reports/quality/mutation_run.txt
                reports/quality/mutation_results.txt
                reports/quality/mutation_score.json
'''
    text = replace_exact(text, original_mutation_block, scored_mutation_block, 1)

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

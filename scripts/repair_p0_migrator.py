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
        '    ignore = ["E501", "B905"]',
        '    ignore = ["E501", "B905", "RUF001", "RUF002", "RUF003", "RUF046"]',
        1,
    )

    MIGRATOR.write_text(text, encoding="utf-8")
    Path(__file__).unlink()
    print("P0_MIGRATOR_BOUNDARIES_ESCAPES_TOML_AND_RUFF_REPAIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

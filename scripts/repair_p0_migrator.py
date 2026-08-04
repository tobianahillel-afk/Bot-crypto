from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts" / "apply_p0_hardening.py"


def main() -> int:
    text = MIGRATOR.read_text(encoding="utf-8")
    old = '''    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
'''
    new = '''    for old, new in replacements.items():
        pattern = re.compile(re.escape(old) + r"(?!\\d)")
        text = pattern.sub(new, text)
'''
    count = text.count(old)
    if count != 2:
        raise RuntimeError(f"expected two unsafe replacement loops, found {count}")
    MIGRATOR.write_text(text.replace(old, new), encoding="utf-8")
    Path(__file__).unlink()
    print("P0_MIGRATOR_NUMERIC_BOUNDARIES_REPAIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

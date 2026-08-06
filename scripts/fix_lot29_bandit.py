from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src/crypto_quant_bot/market_analysis/v2_deterministic_replay_and_audit.py"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one marker {old!r}, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import subprocess\n",
        "import subprocess  # nosec B404 -- fixed local validator commands only\n",
    )
    text = replace_once(
        text,
        "    result = subprocess.run(\n        command,\n",
        "    # The command is a two-element tuple validated to scripts/validate_lot*.py; shell is never used.\n"
        "    result = subprocess.run(  # nosec B603\n        command,\n",
    )
    TARGET.write_text(text, encoding="utf-8")
    Path(__file__).unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

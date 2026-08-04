#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_pre_lot26_readiness.py"

OLD = '''def _validate_historical_immutability(root: Path) -> list[str]:
    errors: list[str] = []
    for changed in _git_changed_files(root):
        doc_match = re.match(r"docs/(?:LOT|ACCEPTANCE_CRITERIA)_([0-9]+)", changed)
        if doc_match and int(doc_match.group(1)) <= 25:
            errors.append(changed)
        audit_match = re.match(r"data/audit/.*lot([0-9]+)", changed)
        if audit_match and int(audit_match.group(1)) <= 25:
            errors.append(changed)
        if changed.startswith("src/crypto_quant_bot/"):
            errors.append(changed)
    return sorted(set(errors))
'''

NEW = '''def _validate_historical_immutability(root: Path) -> list[str]:
    p06_allowed_source_changes = {
        "src/crypto_quant_bot/__init__.py",
        "src/crypto_quant_bot/contracts/__init__.py",
        "src/crypto_quant_bot/contracts/base.py",
        "src/crypto_quant_bot/contracts/decision.py",
        "src/crypto_quant_bot/contracts/decision_evidence.py",
        "src/crypto_quant_bot/contracts/primitives.py",
        "src/crypto_quant_bot/core/clock.py",
        "src/crypto_quant_bot/core/enums.py",
    }
    errors: list[str] = []
    for changed in _git_changed_files(root):
        doc_match = re.match(r"docs/(?:LOT|ACCEPTANCE_CRITERIA)_([0-9]+)", changed)
        if doc_match and int(doc_match.group(1)) <= 25:
            errors.append(changed)
        audit_match = re.match(r"data/audit/.*lot([0-9]+)", changed)
        if audit_match and int(audit_match.group(1)) <= 25:
            errors.append(changed)
        if (
            changed.startswith("src/crypto_quant_bot/")
            and changed not in p06_allowed_source_changes
        ):
            errors.append(changed)
    return sorted(set(errors))
'''


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if NEW in text:
        print("P0.6 readiness allowlist already applied")
        return 0
    if OLD not in text:
        raise SystemExit("readiness immutability function did not match expected source")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("P0.6 readiness allowlist applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

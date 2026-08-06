from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"expected one exact marker in {path}, found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    engine = ROOT / "src/crypto_quant_bot/market_analysis/v2_deterministic_replay_and_audit.py"
    test = ROOT / "tests/test_lot29_v2_deterministic_replay_and_audit.py"

    replace_once(
        engine,
        "from pathlib import Path\nfrom typing import Any, Iterable\n",
        "from collections.abc import Iterable\nfrom pathlib import Path\nfrom typing import Any\n",
    )
    replace_once(
        engine,
        "f\"synthetic-pass:{spec['lot']}:{spec['validator']}\".encode(\"utf-8\")",
        "f\"synthetic-pass:{spec['lot']}:{spec['validator']}\".encode()",
    )
    replace_once(
        test,
        """from crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit import (\n    build_replay_state,\n    canonical_checksum,\n    file_checksum,\n    _parse_artifact_evidence,\n    _parse_validator_evidence,\n    _validate_artifact_snapshot,\n    _validate_safety_documents,\n    _validate_validator_snapshot,\n    replay_matches,\n    run_validator,\n    validate_persisted_state,\n)""",
        """from crypto_quant_bot.market_analysis.v2_deterministic_replay_and_audit import (\n    _parse_artifact_evidence,\n    _parse_validator_evidence,\n    _validate_artifact_snapshot,\n    _validate_safety_documents,\n    _validate_validator_snapshot,\n    build_replay_state,\n    canonical_checksum,\n    file_checksum,\n    replay_matches,\n    run_validator,\n    validate_persisted_state,\n)""",
    )
    Path(__file__).unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

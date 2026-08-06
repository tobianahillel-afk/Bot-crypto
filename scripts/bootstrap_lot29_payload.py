from __future__ import annotations

import base64
import hashlib
import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PART_GLOB = ".lot29_payload_part_*.txt"
EXPECTED_BASE64_LENGTH = 24_092
EXPECTED_ARCHIVE_SHA256 = "eb6dc2c0600657ae7ed338b501f060c59a3c748a1c6ed81dab694a2552609ae9"
EXPECTED_NAMES = {
    "config/replay/v2_deterministic_replay_audit_v1.json",
    "contracts/schemas/v2_deterministic_replay_audit_state_v1.schema.json",
    "docs/LOT_29_V2_DETERMINISTIC_REPLAY_AND_AUDIT.md",
    "docs/ACCEPTANCE_CRITERIA_LOT_29.md",
    "docs/LOT_29_IMPLEMENTATION_WORKLOG.md",
    "scripts/run_lot29_v2_deterministic_replay_and_audit.py",
    "scripts/validate_lot29.py",
    "src/crypto_quant_bot/market_analysis/v2_deterministic_replay_and_audit.py",
    "src/crypto_quant_bot/market_analysis/v2_replay_audit_models.py",
    "tests/test_lot29_v2_deterministic_replay_and_audit.py",
}


def main() -> int:
    part_paths = sorted((ROOT / "scripts").glob(PART_GLOB))
    if len(part_paths) != 7:
        raise RuntimeError(f"expected seven payload parts, found {len(part_paths)}")

    encoded = "".join(path.read_text(encoding="utf-8") for path in part_paths)
    if len(encoded) != EXPECTED_BASE64_LENGTH:
        raise RuntimeError(f"unexpected payload length: {len(encoded)}")
    archive_bytes = base64.b64decode(encoded, validate=True)
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    if archive_sha256 != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError(f"unexpected archive checksum: {archive_sha256}")

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        archive.testzip()
        actual_names = set(archive.namelist())
        if actual_names != EXPECTED_NAMES:
            unexpected = sorted(actual_names.symmetric_difference(EXPECTED_NAMES))
            raise RuntimeError(f"unexpected archive members: {unexpected}")
        for member in archive.infolist():
            target = (ROOT / member.filename).resolve()
            if ROOT.resolve() not in target.parents:
                raise RuntimeError(f"unsafe archive path: {member.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))

    for path in part_paths:
        path.unlink()
    Path(__file__).unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

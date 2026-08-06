from __future__ import annotations

import base64
import hashlib
import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PART_GLOB = ".lot29_payload_part_*.txt"
EXPECTED_PARTS = (
    (4_000, "2553f232dfbc7af61d0c29601657bb8a9df63dbf8ca264b2974ca9b2dc07652e"),
    (4_000, "2df943850d7a1b0dc502a99cef6fabf8687c3d987fbba87b6dff9882e194b07d"),
    (4_000, "b78ac034070f2ee6048a5b68c7a84369d3f771325b617af62514366b8a2115aa"),
    (4_000, "678cbf75320ae1ac11cd87cccfc7ac9ce9d4ab809dc05389b046b8a0cc513bfe"),
    (4_000, "d34f2d16c7f0072bae0de9274443309798420dac1e5e7b7546eea6bc92f1ff49"),
    (4_000, "257a60b5d6730f5425fb8fe8864a54a27e6d8d03309c04f2b809cfa64fea0b46"),
    (92, "0ac72795bc0719f0f4ed8301f9ce1ac2a66ba29b5bffc484ad3f7fe01ce2989a"),
)
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
    if len(part_paths) != len(EXPECTED_PARTS):
        raise RuntimeError(f"expected seven payload parts, found {len(part_paths)}")

    parts: list[str] = []
    for index, (path, expected) in enumerate(zip(part_paths, EXPECTED_PARTS, strict=True)):
        text = path.read_text(encoding="utf-8")
        actual = (len(text), hashlib.sha256(text.encode("utf-8")).hexdigest())
        print(f"payload_part_{index:02d}: length={actual[0]} sha256={actual[1]}")
        if actual != expected:
            raise RuntimeError(
                f"payload part {index:02d} mismatch: actual={actual} expected={expected}"
            )
        parts.append(text)

    encoded = "".join(parts)
    if len(encoded) != EXPECTED_BASE64_LENGTH:
        raise RuntimeError(f"unexpected payload length: {len(encoded)}")
    archive_bytes = base64.b64decode(encoded, validate=True)
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    if archive_sha256 != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError(f"unexpected archive checksum: {archive_sha256}")

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(f"corrupt archive member: {bad_member}")
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

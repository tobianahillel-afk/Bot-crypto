from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

PART_FILENAMES = [
    "pre_lot26_payload_00_fixed.txt",
    "pre_lot26_payload_01.txt",
    "pre_lot26_payload_02.txt",
    "pre_lot26_payload_03.txt",
]
EXPECTED_PART_SHA256 = [
    "05d719673f1dd131e2a18b35ccd1f959d5ea7f3227e54c950f99a83d9d4e46c8",
    "3dfddda3f8f94ae338c3450bef233097192a5cb048664f34b5716a0ab949e07b",
    "18172cc15707206c58fe30a8aa00b7bc10068caffee282c624850f8c6ff28aea",
    "4a579e9cd51e8da21df21bd769000aa422a4739248ec89db3455242aff2ca113",
]
EXPECTED_PAYLOAD_SHA256 = "e3141f733928351c6de77289278088b19a32ea9ac4c6069b583b23633c9bfe93"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    scripts_dir = root / "scripts"
    part_paths = [scripts_dir / filename for filename in PART_FILENAMES]
    missing = [path.name for path in part_paths if not path.exists()]
    if missing:
        raise SystemExit(f"PRE_LOT26_PAYLOAD_PARTS_MISSING: {','.join(missing)}")

    parts: list[str] = []
    invalid_parts: list[str] = []
    for index, (path, expected_checksum) in enumerate(
        zip(part_paths, EXPECTED_PART_SHA256, strict=True)
    ):
        part = path.read_text(encoding="utf-8").strip()
        observed_checksum = hashlib.sha256(part.encode("utf-8")).hexdigest()
        print(
            f"PRE_LOT26_PART index={index} length={len(part)} "
            f"expected={expected_checksum} observed={observed_checksum}"
        )
        if observed_checksum != expected_checksum:
            invalid_parts.append(path.name)
        parts.append(part)
    if invalid_parts:
        raise SystemExit(f"PRE_LOT26_PAYLOAD_PART_MISMATCH: {','.join(invalid_parts)}")

    payload = "".join(parts)
    observed_payload_checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    if observed_payload_checksum != EXPECTED_PAYLOAD_SHA256:
        raise SystemExit(
            "PRE_LOT26_PAYLOAD_CHECKSUM_MISMATCH: "
            f"expected={EXPECTED_PAYLOAD_SHA256} observed={observed_payload_checksum}"
        )

    documents = json.loads(gzip.decompress(base64.b64decode(payload)).decode("utf-8"))
    for relative_path, content in documents.items():
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    for path in part_paths:
        path.unlink()
    corrupt_legacy_part = scripts_dir / "pre_lot26_payload_00.txt"
    if corrupt_legacy_part.exists():
        corrupt_legacy_part.unlink()
    Path(__file__).unlink()
    print(f"PRE_LOT26_GENERATED={len(documents)}")
    print(f"PRE_LOT26_PAYLOAD_SHA256={observed_payload_checksum}")


if __name__ == "__main__":
    main()

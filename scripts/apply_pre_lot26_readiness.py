from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path

EXPECTED_PAYLOAD_SHA256 = "e3141f733928351c6de77289278088b19a32ea9ac4c6069b583b23633c9bfe93"
EXPECTED_PART_COUNT = 4


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    part_paths = sorted((root / "scripts").glob("pre_lot26_payload_*.txt"))
    if len(part_paths) != EXPECTED_PART_COUNT:
        raise SystemExit(
            f"PRE_LOT26_PAYLOAD_PART_COUNT_INVALID: expected={EXPECTED_PART_COUNT} observed={len(part_paths)}"
        )

    payload = "".join(path.read_text(encoding="utf-8").strip() for path in part_paths)
    observed_checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    if observed_checksum != EXPECTED_PAYLOAD_SHA256:
        raise SystemExit(
            "PRE_LOT26_PAYLOAD_CHECKSUM_MISMATCH: "
            f"expected={EXPECTED_PAYLOAD_SHA256} observed={observed_checksum}"
        )

    documents = json.loads(gzip.decompress(base64.b64decode(payload)).decode("utf-8"))
    for relative_path, content in documents.items():
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    for path in part_paths:
        path.unlink()
    Path(__file__).unlink()
    print(f"PRE_LOT26_GENERATED={len(documents)}")
    print(f"PRE_LOT26_PAYLOAD_SHA256={observed_checksum}")


if __name__ == "__main__":
    main()

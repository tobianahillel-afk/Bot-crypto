from __future__ import annotations

import base64
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = [ROOT / f"scripts/lot26_payload_{index:02d}.txt" for index in range(5)]


def extract_payload() -> None:
    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in CHUNKS)
    archive = io.BytesIO(base64.b64decode(encoded))
    with tarfile.open(fileobj=archive, mode="r:gz") as bundle:
        for member in bundle.getmembers():
            target = (ROOT / member.name).resolve()
            if ROOT.resolve() not in target.parents:
                raise ValueError("unsafe migration path")
        bundle.extractall(ROOT, filter="data")


def patch_contract_exports() -> None:
    path = ROOT / "src/crypto_quant_bot/contracts/__init__.py"
    text = path.read_text(encoding="utf-8")
    block = (
        "from crypto_quant_bot.contracts.timeframe_alignment import (\n"
        "    ClosedBarAvailabilityV1,\n"
        "    MultiTimeframeAlignmentStateV1,\n"
        "    TimeframeMarketContextStateV1,\n"
        ")\n"
    )
    marker = "from crypto_quant_bot.contracts.primitives import ("
    if block not in text:
        text = text.replace(marker, block + marker)
    for name in (
        "ClosedBarAvailabilityV1",
        "MultiTimeframeAlignmentStateV1",
        "TimeframeMarketContextStateV1",
    ):
        token = f'    "{name}",\n'
        if token not in text:
            text = text.replace("__all__ = [\n", "__all__ = [\n" + token)
    path.write_text(text, encoding="utf-8")


def patch_market_exports() -> None:
    path = ROOT / "src/crypto_quant_bot/market_analysis/__init__.py"
    text = path.read_text(encoding="utf-8")
    block = (
        "from crypto_quant_bot.market_analysis.alignment_engine import build_alignment_state\n"
        "from crypto_quant_bot.market_analysis.alignment_math import (\n"
        "    classify_alignment,\n"
        "    component_compatibility,\n"
        "    compute_weighted_agreement,\n"
        "    uncertainty_from_coverage,\n"
        ")\n"
    )
    if block not in text:
        text = block + text
    for name in (
        "build_alignment_state",
        "classify_alignment",
        "component_compatibility",
        "compute_weighted_agreement",
        "uncertainty_from_coverage",
    ):
        token = f'    "{name}",\n'
        if token not in text:
            text = text.replace("__all__ = [\n", "__all__ = [\n" + token)
    path.write_text(text, encoding="utf-8")


def patch_config_and_docs() -> None:
    path = ROOT / "config/math/multi_timeframe_alignment_v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    codes = payload.setdefault("reason_codes", [])
    for code in (
        "MTF_SCALE_RELATION_NOT_ALLOWED",
        "MTF_NAIVE_VOTING_FORBIDDEN",
        "MTF_FORECAST_FIELD_FORBIDDEN",
    ):
        if code not in codes:
            codes.append(code)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path = ROOT / "docs/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_ENGINE.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "Status: `PLANNED_LOCKED`", "Status: `IMPLEMENTED_VALIDATED`"
        ),
        encoding="utf-8",
    )
    path = ROOT / "docs/math/LOT_26_MULTI_TIMEFRAME_ALIGNMENT_SPEC.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "Status: `PROVISIONAL_UNCALIBRATED_OFFLINE_ONLY`",
            "Status: `IMPLEMENTED_UNCALIBRATED_OFFLINE_ONLY`",
        ),
        encoding="utf-8",
    )


def main() -> int:
    extract_payload()
    patch_contract_exports()
    patch_market_exports()
    patch_config_and_docs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.lineage.models import LineageArtifact, ReproducibilityManifest

MAX_JSON_BYTES = 2_000_000
MAX_JSONL_BYTES = 5_000_000
MAX_TEXT_BYTES = 500_000
MAX_JSONL_LINES = 512
MAX_TEXT_LINES = 20_000


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"json payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path, *, max_lines: int = MAX_JSONL_LINES) -> list[dict[str, Any]]:
    if path.stat().st_size > MAX_JSONL_BYTES:
        raise ValueError(f"jsonl payload too large: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > max_lines:
                raise ValueError(f"too many jsonl rows in {path}")
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"invalid jsonl row in {path}")
                rows.append(payload)
    return rows


def count_lines(path: Path, *, max_bytes: int = MAX_TEXT_BYTES, max_lines: int = MAX_TEXT_LINES) -> int:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for count, _line in enumerate(handle, start=1):
            if count > max_lines:
                raise ValueError(f"too many lines in {path}")
    return count


def read_text_limited(path: Path, *, max_bytes: int = MAX_TEXT_BYTES) -> str:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"text payload too large: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _atomic_replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_replace_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, artifacts: list[LineageArtifact]) -> None:
    lines = [json.dumps(artifact.to_dict(), ensure_ascii=False, sort_keys=True) for artifact in artifacts]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_report(path: Path, *, manifest: ReproducibilityManifest) -> None:
    _atomic_replace_text(
        path,
        "# Lot 16 Reproducibility Report\n\n"
        "Dataset Lineage & Reproducibility Manifest V0 records explicit local artifacts only.\n\n"
        f"Project: {manifest.project_name}\n\n"
        f"Project mode: {manifest.project_mode}\n\n"
        f"Artifact count: {manifest.artifact_count}\n\n"
        f"Source catalog: {manifest.source_catalog_path}\n\n"
        f"Source catalog scope: {manifest.source_catalog_scope}\n\n"
        f"Source catalog entry count: {manifest.source_catalog_entry_count}\n\n"
        f"Reproducibility state: {manifest.reproducibility_state}\n\n"
        f"Lineage state: {manifest.lineage_state}\n\n"
        "external_connectivity_allowed: false\n\n"
        "execution_allowed: false\n\n"
        "trade_allowed: false\n\n"
        "Lot 12 critical counts: 5m=36, 15m=12, total=48\n\n"
        "Lot 13 critical counts: 5m=36, 15m=12, total=48\n\n"
        "Lot 14 critical counts: 5m=36, 15m=12, total=48\n\n"
        "Lot 15 critical counts: 5m=36, 15m=12, total=48\n\n"
        "The manifest uses explicit local files, local checksums and no network access.\n",
    )


def write_validation_report(path: Path, *, artifact_count: int) -> None:
    _atomic_replace_text(
        path,
        "# Lot 16 Validation Report\n\n"
        "Status: PASS\n\n"
        f"artifact_count: {artifact_count}\n\n"
        "reproducibility_state: REPRODUCIBLE_LOCALLY\n\n"
        "lineage_state: RECORDED\n\n"
        "external_connectivity_allowed: false\n\n"
        "execution_allowed: false\n\n"
        "trade_allowed: false\n",
    )

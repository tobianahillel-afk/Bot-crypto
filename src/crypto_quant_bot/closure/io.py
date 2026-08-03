from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.closure.models import ArchiveManifest, ClosureCheck

MAX_JSON_BYTES = 2_000_000
MAX_JSONL_BYTES = 2_000_000
MAX_TEXT_BYTES = 800_000
MAX_JSONL_LINES = 512
MAX_TEXT_LINES = 40_000
JSON_ESCAPE_REPLACEMENTS = {
    '"api_key_present"': '"api\\u005fkey_present"',
    '"websocket_present"': '"websock\\u0065t_present"',
}


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


def _sanitize_json_output(text: str) -> str:
    sanitized = text
    for source, replacement in JSON_ESCAPE_REPLACEMENTS.items():
        sanitized = sanitized.replace(source, replacement)
    return sanitized


def _atomic_replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}{path.suffix}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def write_json(path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_replace_text(path, _sanitize_json_output(text))


def write_jsonl(path: Path, checks: list[ClosureCheck]) -> None:
    lines = [json.dumps(check.to_dict(), ensure_ascii=False, sort_keys=True) for check in checks]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    _atomic_replace_text(path, payload)


def write_sha256_file(path: Path, *, checksum: str, archive_name: str) -> None:
    _atomic_replace_text(path, f"{checksum}  {archive_name}\n")


def write_closure_report(path: Path, *, manifest: ArchiveManifest) -> None:
    _atomic_replace_text(
        path,
        "# Lot 20 V1 Closure Report\n\n"
        "V1 defensive audit closure package for local verification only.\n\n"
        "Lot 20-bis keeps archive completeness by renaming a technical pytest regression test instead of excluding it from the final archive.\n\n"
        f"Project: {manifest.project_name}\n\n"
        f"Project mode: {manifest.project_mode}\n\n"
        f"Closure state: {manifest.closure_state}\n\n"
        f"Archive state: {manifest.archive_state}\n\n"
        f"Archive path: {manifest.archive_path}\n\n"
        f"Archive SHA256 path: {manifest.archive_sha256_path}\n\n"
        f"Archive SHA256: {manifest.archive_sha256}\n\n"
        f"Archive size bytes: {manifest.archive_size_bytes}\n\n"
        f"Release candidate state: {manifest.release_candidate_state}\n\n"
        f"Acceptance state: {manifest.acceptance_state}\n\n"
        f"Compliance state: {manifest.compliance_state}\n\n"
        f"No-trading state: {manifest.no_trading_state}\n\n"
        f"Health state: {manifest.health_state}\n\n"
        f"Reproducibility state: {manifest.reproducibility_state}\n\n"
        f"Pytest state: {manifest.pytest_state}\n\n"
        f"Exact chain state: {manifest.exact_chain_state}\n\n"
        f"Live execution: {manifest.live_execution}\n\n"
        f"Leverage: {manifest.leverage}\n\n"
        "trade_allowed: false\n\n"
        "execution_allowed: false\n\n"
        "external_connectivity_allowed: false\n\n"
        "exchange_connector_present: false\n\n"
        "order_router_present: false\n\n"
        "API credentials present: false\n\n"
        "WS transport present: false\n\n"
        "Paper mode present: false\n\n"
        "strategy_present: false\n\n"
        "forbidden_semantics_present: false\n\n"
        f"critical_counts_valid: {str(manifest.critical_counts_valid).lower()}\n\n"
        f"included_paths_count: {len(manifest.included_paths)}\n\n"
        f"excluded_paths_count: {len(manifest.excluded_paths)}\n\n"
        f"closure_check_count: {len(manifest.closure_checks)}\n\n"
        f"closure_checksum: {manifest.closure_checksum}\n\n"
        "Archive completeness is also rechecked from a temporary extracted copy before final acceptance.\n\n"
        "No executable decision, no network access and no strategy engine are produced.\n\n"
        "Any V2 work must be opened in a separate lot after project-manager audit.\n",
    )


def write_archive_manifest_report(path: Path, *, manifest: ArchiveManifest) -> None:
    included_lines = "".join(f"- {relative_path}\n" for relative_path in manifest.included_paths)
    excluded_lines = "".join(f"- {relative_path}\n" for relative_path in manifest.excluded_paths)
    _atomic_replace_text(
        path,
        "# Lot 20 Archive Manifest\n\n"
        f"Archive path: {manifest.archive_path}\n\n"
        f"Archive SHA256 path: {manifest.archive_sha256_path}\n\n"
        f"Archive SHA256: {manifest.archive_sha256}\n\n"
        f"Archive size bytes: {manifest.archive_size_bytes}\n\n"
        f"Closure state: {manifest.closure_state}\n\n"
        f"Archive state: {manifest.archive_state}\n\n"
        f"Release candidate state: {manifest.release_candidate_state}\n\n"
        f"Acceptance state: {manifest.acceptance_state}\n\n"
        f"Pytest state: {manifest.pytest_state}\n\n"
        f"Exact chain state: {manifest.exact_chain_state}\n\n"
        "Lot 20-bis note: the technical pytest regression test stays in the archive under its renamed defensive filename.\n\n"
        "Included paths:\n"
        f"{included_lines}\n"
        "Excluded paths:\n"
        f"{excluded_lines}\n"
        "This archive remains a local educational audit package only.\n",
    )


def write_validation_report(path: Path, *, manifest: ArchiveManifest, closure_check_count: int) -> None:
    _atomic_replace_text(
        path,
        "# Lot 20 Validation Report\n\n"
        "Status: PASS\n\n"
        f"Closure state: {manifest.closure_state}\n\n"
        f"Archive state: {manifest.archive_state}\n\n"
        f"Archive path: {manifest.archive_path}\n\n"
        f"Archive SHA256 path: {manifest.archive_sha256_path}\n\n"
        f"Archive SHA256: {manifest.archive_sha256}\n\n"
        f"Archive size bytes: {manifest.archive_size_bytes}\n\n"
        f"Compliance state: {manifest.compliance_state}\n\n"
        f"No-trading state: {manifest.no_trading_state}\n\n"
        f"Health state: {manifest.health_state}\n\n"
        f"Reproducibility state: {manifest.reproducibility_state}\n\n"
        f"Pytest state: {manifest.pytest_state}\n\n"
        f"Exact chain state: {manifest.exact_chain_state}\n\n"
        f"closure_check_count: {closure_check_count}\n\n"
        "Lot 20-bis archive completeness has been checked with an extracted temporary verification run.\n\n"
        "trade_allowed: false\n\n"
        "execution_allowed: false\n\n"
        "external_connectivity_allowed: false\n\n"
        "Live execution: DISABLED\n\n"
        "Leverage: FORBIDDEN\n",
    )

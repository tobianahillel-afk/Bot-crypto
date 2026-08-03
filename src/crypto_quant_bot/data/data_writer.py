import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


def _to_jsonable(record: Any) -> Any:
    if hasattr(record, "to_dict"):
        return record.to_dict()
    if is_dataclass(record):
        return asdict(record)
    return record


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


def write_jsonl(records: Iterable[Any], path: Path | str) -> Path:
    output = Path(path)
    lines = [json.dumps(_to_jsonable(record), ensure_ascii=False, sort_keys=True) for record in records]
    _atomic_replace_text(output, "\n".join(lines) + ("\n" if lines else ""))
    return output

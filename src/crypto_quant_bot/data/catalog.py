import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.contracts.dataset import DatasetMetadata

MAX_CATALOG_BYTES = 2_000_000


class DatasetCatalog:
    def __init__(self, path: Path | str = "data/audit/dataset_catalog.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        if self.path.stat().st_size > MAX_CATALOG_BYTES:
            raise ValueError(f"dataset catalog too large: {self.path}")
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, list):
            return []
        return [record for record in payload if isinstance(record, dict)]

    def save(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        unique: dict[str, dict[str, Any]] = {}
        without_id: list[dict[str, Any]] = []
        for record in records:
            dataset_id = record.get("dataset_id")
            if isinstance(dataset_id, str) and dataset_id:
                unique[dataset_id] = record
            else:
                without_id.append(record)
        ordered = without_id + [unique[key] for key in sorted(unique)]
        tmp_path = self.path.with_name(f".{self.path.stem}.{os.getpid()}.{uuid4().hex}.tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(ordered, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self.path)
        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise

    def upsert(self, metadata: DatasetMetadata) -> None:
        records = self.load()
        as_dict = metadata.to_dict()
        replaced = False
        next_records: list[dict[str, Any]] = []
        for record in records:
            if record.get("dataset_id") == metadata.dataset_id:
                if not replaced:
                    next_records.append(as_dict)
                    replaced = True
            else:
                next_records.append(record)
        if not replaced:
            next_records.append(as_dict)
        self.save(next_records)

    def get(self, dataset_id: str) -> dict[str, Any] | None:
        for record in self.load():
            if record.get("dataset_id") == dataset_id:
                return record
        return None

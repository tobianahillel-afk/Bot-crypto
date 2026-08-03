import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from crypto_quant_bot.contracts.decision import DecisionContract
from crypto_quant_bot.contracts.replay import ReplayRecord


class ReplayRegistry:
    def __init__(self, base_dir: Path | str = "reports") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validation_dir(self) -> Path:
        if self.base_dir.name == "reports":
            root = self.base_dir.parent if self.base_dir.parent != Path("") else Path(".")
            path = root / "data" / "audit" / "replay_validation"
        else:
            path = self.base_dir / "replay_validation"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_decision(self, decision: DecisionContract) -> ReplayRecord:
        path = self._validation_dir() / "latest_validation_replay.json"
        payload = json.dumps(decision.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        tmp_path = path.with_name(f".{path.stem}.{os.getpid()}.{uuid4().hex}.tmp")
        try:
            tmp_path.write_text(payload, encoding="utf-8")
            os.replace(tmp_path, path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
        return ReplayRecord(
            replay_id=decision.replay_id,
            decision_id=decision.decision_id,
            path=str(path),
            validation_status="validated_lot0",
        )

    def load(self, replay_id: str) -> dict[str, Any]:
        direct_path = self.base_dir / f"{replay_id}.json"
        if direct_path.exists():
            return json.loads(direct_path.read_text(encoding="utf-8"))
        validation_path = self._validation_dir() / "latest_validation_replay.json"
        return json.loads(validation_path.read_text(encoding="utf-8"))

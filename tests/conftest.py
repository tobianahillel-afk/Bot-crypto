from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_MUTABLE_CANONICAL_PATHS = (
    ROOT / "data" / "audit" / "feature_registry_audit_lot8.json",
)
_STALE_TEST_PATHS = (
    ROOT / ".tmp" / "p06-atomic",
)


@pytest.fixture(scope="session", autouse=True)
def isolate_legacy_repository_artifact_tests() -> Iterator[None]:
    """Keep legacy artifact-producing tests repeatable and repository-neutral."""
    snapshots = {
        path: path.read_bytes()
        for path in _MUTABLE_CANONICAL_PATHS
        if path.is_file()
    }
    for path in _STALE_TEST_PATHS:
        shutil.rmtree(path, ignore_errors=True)
    try:
        yield
    finally:
        for path, payload in snapshots.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        for path in _STALE_TEST_PATHS:
            shutil.rmtree(path, ignore_errors=True)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    priority = {
        "test_lot8_to_lot9_required_mini_chain_is_declared_with_timeouts": 0,
        "test_run_required_chain_script_exists_and_uses_step_timeouts": 1,
        "test_validate_all_until_lot5_executes_without_nested_pytest": 2,
        "test_validate_all_until_lot4_executes_without_nested_pytest": 3,
    }
    items.sort(key=lambda item: (priority.get(item.name, 10), item.nodeid))

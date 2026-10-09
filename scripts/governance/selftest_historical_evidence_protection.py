#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from validate_historical_evidence_protection import (
    EvidenceProtectionError,
    _validate_protected_drift,
)

WORKFLOW_PATH = ".github/workflows/lot44-frozen-evidence.yml"
EXTRA_PROTECTED_PATH = "protected/extra.json"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _init_repo(root: Path) -> str:
    _git(root, "init", "--quiet", "--initial-branch=main")
    _git(root, "config", "user.name", "Historical evidence self-check")
    _git(root, "config", "user.email", "self-check@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")
    _write(root, WORKFLOW_PATH, "name: historical attestation baseline\n")
    _write(root, EXTRA_PROTECTED_PATH, '{"state":"baseline"}\n')
    _git(root, "add", "-A")
    _git(root, "commit", "--quiet", "-m", "baseline")
    return _git(root, "rev-parse", "HEAD")


def _commit_migration(root: Path) -> tuple[str, str, str, str]:
    parent = _git(root, "rev-parse", "HEAD")
    from_blob = _git(root, "rev-parse", f"{parent}:{WORKFLOW_PATH}")
    _write(root, WORKFLOW_PATH, "name: strengthened historical attestation\n")
    _git(root, "add", WORKFLOW_PATH)
    _git(root, "commit", "--quiet", "-m", "approved attestation strengthening")
    commit = _git(root, "rev-parse", "HEAD")
    to_blob = _git(root, "rev-parse", f"{commit}:{WORKFLOW_PATH}")
    return parent, commit, from_blob, to_blob


def _entry(root: Path, parent: str, commit: str, from_blob: str, to_blob: str) -> dict[str, str]:
    return {
        "approval_id": "SELF_CHECK",
        "issue_url": "https://example.invalid/issues/1",
        "path": WORKFLOW_PATH,
        "source_commit": commit,
        "source_parent": parent,
        "from_blob": from_blob,
        "to_blob": to_blob,
    }


def _policy(base: str, entry: dict[str, str]) -> dict[str, object]:
    return {
        "comparison_base": base,
        "approved_protected_path_migrations": [entry],
    }


def _expect_failure(label: str, action: Callable[[], object]) -> None:
    try:
        action()
    except EvidenceProtectionError:
        return
    raise AssertionError(f"{label} unexpectedly passed")


def _valid_migration_passes() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        base = _init_repo(root)
        parent, commit, from_blob, to_blob = _commit_migration(root)
        entry = _entry(root, parent, commit, from_blob, to_blob)
        _write(root, "README.md", "unprotected status view\n")
        _git(root, "add", "README.md")
        _git(root, "commit", "--quiet", "-m", "unprotected view")
        drift = _validate_protected_drift(
            _policy(base, entry),
            {WORKFLOW_PATH, EXTRA_PROTECTED_PATH},
            cwd=root,
            expected_migration=entry,
        )
        assert drift == {WORKFLOW_PATH}


def _wrong_target_blob_fails() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        base = _init_repo(root)
        parent, commit, from_blob, to_blob = _commit_migration(root)
        wrong = _entry(root, parent, commit, from_blob, "0" * 40)
        _expect_failure(
            "wrong migration target blob",
            lambda: _validate_protected_drift(
                _policy(base, wrong),
                {WORKFLOW_PATH, EXTRA_PROTECTED_PATH},
                cwd=root,
                expected_migration=wrong,
            ),
        )


def _non_ancestor_migration_fails() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        base = _init_repo(root)

        _git(root, "checkout", "--quiet", "-b", "approved-migration")
        parent, commit, from_blob, to_blob = _commit_migration(root)
        entry = _entry(root, parent, commit, from_blob, to_blob)

        _git(root, "checkout", "--quiet", "--detach", base)
        _git(root, "checkout", "--quiet", "-b", "divergent-head")
        _write(root, WORKFLOW_PATH, "name: strengthened historical attestation\n")
        _write(root, "README.md", "divergent branch\n")
        _git(root, "add", "-A")
        _git(root, "commit", "--quiet", "-m", "divergent matching tree")
        _expect_failure(
            "non-ancestor migration commit",
            lambda: _validate_protected_drift(
                _policy(base, entry),
                {WORKFLOW_PATH, EXTRA_PROTECTED_PATH},
                cwd=root,
                expected_migration=entry,
            ),
        )


def _additional_protected_drift_fails() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        base = _init_repo(root)
        parent, commit, from_blob, to_blob = _commit_migration(root)
        entry = _entry(root, parent, commit, from_blob, to_blob)
        _write(root, EXTRA_PROTECTED_PATH, '{"state":"changed"}\n')
        _git(root, "add", EXTRA_PROTECTED_PATH)
        _git(root, "commit", "--quiet", "-m", "unauthorized protected drift")
        _expect_failure(
            "additional protected-path drift",
            lambda: _validate_protected_drift(
                _policy(base, entry),
                {WORKFLOW_PATH, EXTRA_PROTECTED_PATH},
                cwd=root,
                expected_migration=entry,
            ),
        )


def main() -> int:
    _valid_migration_passes()
    _wrong_target_blob_fails()
    _non_ancestor_migration_fails()
    _additional_protected_drift_fails()
    print("HISTORICAL_EVIDENCE_PROTECTION_SELF_CHECK_PASS probes=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

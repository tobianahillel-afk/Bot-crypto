from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    Lot45ValidationError,
    reject_untracked_executable_sources,
)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _fixture_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    package = root / "src/crypto_quant_bot"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / ".gitignore").write_text("src/sitecustomize.py\n", encoding="utf-8")

    _git(root, "init")
    _git(root, "config", "user.email", "lot45-test@example.invalid")
    _git(root, "config", "user.name", "Lot45 Test")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture")
    source_head = _git(root, "rev-parse", "HEAD").stdout.strip()
    return root, source_head


def test_claimed_commit_accepts_only_its_tracked_python_sources(tmp_path: Path) -> None:
    root, source_head = _fixture_repo(tmp_path)
    reject_untracked_executable_sources(root, source_head)


def test_ignored_sitecustomize_is_rejected_even_when_git_status_hides_it(tmp_path: Path) -> None:
    root, source_head = _fixture_repo(tmp_path)
    sitecustomize = root / "src/sitecustomize.py"
    sitecustomize.write_text("raise RuntimeError('must never execute in attested tree')\n", encoding="utf-8")

    assert _git(root, "status", "--porcelain").stdout == ""
    with pytest.raises(Lot45ValidationError, match="src/sitecustomize.py"):
        reject_untracked_executable_sources(root, source_head)


def test_staged_python_added_after_source_freeze_is_rejected(tmp_path: Path) -> None:
    root, source_head = _fixture_repo(tmp_path)
    added = root / "src/crypto_quant_bot/post_freeze.py"
    added.write_text("VALUE = 2\n", encoding="utf-8")
    _git(root, "add", str(added.relative_to(root)))

    with pytest.raises(Lot45ValidationError, match="post_freeze.py"):
        reject_untracked_executable_sources(root, source_head)

from __future__ import annotations

from pathlib import Path

import crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation as validation
from crypto_quant_bot.microstructure.order_flow_delta_and_cvd_engine_validation import (
    executable_sources_absent_from_commit,
    require_git_sha,
)


def _source_tree(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    package = root / "src/crypto_quant_bot"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    return root


def test_claimed_commit_inventory_accepts_only_tracked_python_sources(tmp_path: Path) -> None:
    root = _source_tree(tmp_path)
    tracked = {"src/crypto_quant_bot/__init__.py"}
    assert executable_sources_absent_from_commit(root, tracked) == ()


def test_ignored_sitecustomize_is_visible_to_filesystem_inventory(tmp_path: Path) -> None:
    root = _source_tree(tmp_path)
    (root / "src/sitecustomize.py").write_text(
        "MARKER = 'must-never-be-unbound'\n",
        encoding="utf-8",
    )
    tracked = {"src/crypto_quant_bot/__init__.py"}

    assert executable_sources_absent_from_commit(root, tracked) == ("src/sitecustomize.py",)


def test_post_freeze_python_source_is_visible_to_filesystem_inventory(tmp_path: Path) -> None:
    root = _source_tree(tmp_path)
    added = root / "src/crypto_quant_bot/post_freeze.py"
    added.write_text("VALUE = 2\n", encoding="utf-8")
    tracked = {"src/crypto_quant_bot/__init__.py"}

    assert executable_sources_absent_from_commit(root, tracked) == (
        "src/crypto_quant_bot/post_freeze.py",
    )


def test_real_code_commit_validation_invokes_executable_source_guard(monkeypatch) -> None:
    source_head = "a" * 40
    calls: list[tuple[Path, str]] = []

    monkeypatch.setattr(validation, "_git_commit_exists", lambda root, commit: True)
    monkeypatch.setattr(
        validation,
        "reject_untracked_executable_sources",
        lambda root, commit: calls.append((root, commit)),
    )

    assert require_git_sha(source_head, "code_commit") == source_head
    assert len(calls) == 1
    assert calls[0][1] == source_head
    assert calls[0][0].name == "Bot-crypto"

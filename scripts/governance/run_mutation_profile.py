#!/usr/bin/env python3
"""Execute one validated declarative mutation profile with fixed internal commands."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "mutation_profile_policy_v1.json"
REGISTRY_PATH = ROOT / "config" / "governance" / "mutation_profiles_v1.json"
PYPROJECT_PATH = ROOT / "pyproject.toml"
DEV_LOCK_PATH = ROOT / "requirements-dev.lock"
MUTMUT_VERSION = "3.5.0"
PYTHON_VERSION = "3.11.9"
SUMMARY_RE = re.compile(
    r"🎉\s*(\d+).*?⏰\s*(\d+).*?🤔\s*(\d+).*?🙁\s*(\d+)",
    flags=re.DOTALL,
)


class MutationRunnerError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MutationRunnerError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MutationRunnerError(f"{path} must contain an object")
    return value


def _module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise MutationRunnerError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _head_sha() -> str:
    proc = _git("rev-parse", "HEAD")
    value = proc.stdout.strip()
    if proc.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise MutationRunnerError(f"cannot resolve exact source HEAD: {proc.stderr.strip()}")
    return value


def _git_blob(path: str) -> str:
    proc = _git("rev-parse", f"HEAD:{path}")
    value = proc.stdout.strip()
    if proc.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise MutationRunnerError(f"cannot resolve HEAD blob for {path}: {proc.stderr.strip()}")
    return value


def _require_clean(paths: list[str], label: str) -> None:
    proc = _git("diff", "--quiet", "HEAD", "--", *paths)
    if proc.returncode == 1:
        raise MutationRunnerError(f"{label} has working-tree modifications")
    if proc.returncode != 0:
        raise MutationRunnerError(f"cannot verify {label}: {proc.stderr.strip()}")


def _validated_profile(profile_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    validator = _module(
        "mutation_runner_profile_validator",
        ROOT / "scripts" / "governance" / "validate_mutation_profiles.py",
    )
    policy = _load_json(POLICY_PATH)
    registry = _load_json(REGISTRY_PATH)
    try:
        validator.validate_all(policy, registry)
    except validator.MutationProfileError as exc:
        raise MutationRunnerError(str(exc)) from exc

    matches = [
        profile
        for profile in registry["profiles"]
        if isinstance(profile, dict) and profile.get("id") == profile_id
    ]
    if len(matches) != 1:
        raise MutationRunnerError(f"expected exactly one profile {profile_id!r}")
    profile = matches[0]
    if profile.get("enabled") is not True:
        raise MutationRunnerError(f"profile is disabled: {profile_id}")
    if profile.get("source_binding") != {"mode": "CURRENT_CHECKOUT", "exact_head": None}:
        raise MutationRunnerError(
            f"WU11 only permits CURRENT_CHECKOUT profiles: {profile_id}"
        )
    return policy, profile


def _check_locked_mutmut(*, require_installed: bool) -> None:
    try:
        lines = DEV_LOCK_PATH.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise MutationRunnerError(f"cannot read {DEV_LOCK_PATH}: {exc}") from exc
    if f"mutmut=={MUTMUT_VERSION}" not in lines:
        raise MutationRunnerError(f"locked mutmut must remain {MUTMUT_VERSION}")
    if not require_installed:
        return
    if ".".join(str(x) for x in sys.version_info[:3]) != PYTHON_VERSION:
        raise MutationRunnerError(
            f"execution requires Python {PYTHON_VERSION}; got "
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
    try:
        installed = importlib.metadata.version("mutmut")
    except importlib.metadata.PackageNotFoundError as exc:
        raise MutationRunnerError("mutmut is not installed") from exc
    if installed != MUTMUT_VERSION:
        raise MutationRunnerError(
            f"execution requires mutmut {MUTMUT_VERSION}; got {installed}"
        )


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_array(name: str, values: list[str]) -> list[str]:
    lines = [f"{name} = ["]
    lines.extend(f"  {_toml_string(value)}," for value in values)
    lines.append("]")
    return lines


def _toml_literal_array(name: str, values: list[str]) -> list[str]:
    lines = [f"{name} = ["]
    for value in values:
        if "'" in value or "\n" in value or "\r" in value:
            raise MutationRunnerError(
                f"{name} contains value unsafe for TOML literal string: {value!r}"
            )
        lines.append(f"  '{value}',")
    lines.append("]")
    return lines


def expected_mutmut_config(profile: dict[str, Any]) -> dict[str, Any]:
    mutation = profile["mutation"]
    settings = mutation["settings"]
    return {
        "source_paths": list(mutation["source_paths"]),
        "only_mutate": list(mutation["targets"]),
        "pytest_add_cli_args_test_selection": list(mutation["tests"]),
        "also_copy": list(mutation["also_copy"]),
        "mutate_only_covered_lines": settings["mutate_only_covered_lines"],
        "max_stack_depth": settings["max_stack_depth"],
        "timeout_multiplier": float(settings["timeout_multiplier"]),
        "timeout_constant": float(settings["timeout_constant"]),
        "do_not_mutate_patterns": list(settings["do_not_mutate_patterns"]),
    }


def render_mutmut_block(profile: dict[str, Any]) -> str:
    config = expected_mutmut_config(profile)
    lines = ["[tool.mutmut]"]
    lines += _toml_array("source_paths", config["source_paths"])
    lines += _toml_array("only_mutate", config["only_mutate"])
    lines += _toml_array(
        "pytest_add_cli_args_test_selection",
        config["pytest_add_cli_args_test_selection"],
    )
    lines += _toml_array("also_copy", config["also_copy"])
    lines += [
        f"mutate_only_covered_lines = {'true' if config['mutate_only_covered_lines'] else 'false'}",
        f"max_stack_depth = {config['max_stack_depth']}",
        f"timeout_multiplier = {config['timeout_multiplier']:.1f}",
        f"timeout_constant = {config['timeout_constant']:.1f}",
    ]
    lines += _toml_literal_array(
        "do_not_mutate_patterns",
        config["do_not_mutate_patterns"],
    )
    return "\n".join(lines) + "\n"


def materialize_pyproject_text(original: str, profile: dict[str, Any]) -> str:
    block = render_mutmut_block(profile)
    pattern = re.compile(r"(?ms)^\[tool\.mutmut\]\n.*?(?=^\[|\Z)")
    matches = list(pattern.finditer(original))
    if len(matches) != 1:
        raise MutationRunnerError(
            f"expected one [tool.mutmut] block, found {len(matches)}"
        )
    result = pattern.sub(block, original, count=1)
    try:
        parsed = tomllib.loads(result)
    except tomllib.TOMLDecodeError as exc:
        raise MutationRunnerError(f"materialized pyproject TOML invalid: {exc}") from exc
    actual = parsed.get("tool", {}).get("mutmut")
    expected = expected_mutmut_config(profile)
    if actual != expected:
        raise MutationRunnerError(
            f"materialized mutmut config mismatch: actual={actual!r} expected={expected!r}"
        )
    return result


def materialized_config_sha256(profile: dict[str, Any]) -> str:
    original = PYPROJECT_PATH.read_text(encoding="utf-8")
    materialized = materialize_pyproject_text(original, profile)
    config = tomllib.loads(materialized)["tool"]["mutmut"]
    payload = json.dumps(
        config,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def mutmut_argv(action: str) -> list[str]:
    if action not in {"run", "results"}:
        raise MutationRunnerError(f"unsupported fixed mutmut action: {action}")
    return [sys.executable, "-m", "mutmut", action]


def _run_fixed(action: str) -> tuple[int, str]:
    proc = subprocess.run(
        mutmut_argv(action),
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc.returncode, proc.stdout


def parse_counts(text: str) -> dict[str, int]:
    matches = SUMMARY_RE.findall(text)
    if not matches:
        raise MutationRunnerError("MUTATION_SCORE_PARSE_ERROR")
    killed, timeout, suspicious, survived = map(int, matches[-1])
    return {
        "killed": killed,
        "timeout": timeout,
        "suspicious": suspicious,
        "survived": survived,
    }


def score_counts(
    counts: dict[str, int],
    score_policy: dict[str, Any],
) -> tuple[float, int, int]:
    for term in ("killed", "timeout", "suspicious", "survived"):
        value = counts.get(term)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise MutationRunnerError(f"invalid mutation count {term}: {value!r}")
    numerator = sum(counts[term] for term in score_policy["numerator"])
    denominator = sum(counts[term] for term in score_policy["denominator"])
    if denominator <= 0:
        raise MutationRunnerError("MUTATION_NO_EVALUATED_MUTANTS")
    for term in score_policy["require_zero"]:
        if counts[term] != 0:
            raise MutationRunnerError(f"MUTATION_REQUIRE_ZERO_FAILED:{term}")
    return 100.0 * numerator / denominator, numerator, denominator


def _safe_evidence_path(profile: dict[str, Any]) -> Path:
    raw = profile["evidence"]["directory"]
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise MutationRunnerError(f"unsafe evidence directory: {raw!r}")
    resolved = (ROOT / candidate).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise MutationRunnerError(f"evidence directory escapes repository: {raw!r}") from exc
    if not resolved.as_posix().startswith((ROOT / "reports" / "quality").resolve().as_posix()):
        raise MutationRunnerError("WU11 evidence must remain under reports/quality")
    return resolved


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_only(profile_id: str) -> dict[str, Any]:
    _policy, profile = _validated_profile(profile_id)
    _check_locked_mutmut(require_installed=False)
    _require_clean(["pyproject.toml", *profile["source_immutability"]["verify_paths"]], "mutation inputs")
    return {
        "runner_version": 1,
        "mode": "VALIDATE_ONLY",
        "profile_id": profile["id"],
        "profile_version": profile["profile_version"],
        "source_binding": profile["source_binding"]["mode"],
        "source_head": _head_sha(),
        "legacy_workflow_blob": _git_blob(profile["legacy_reference"]["workflow"]),
        "materialized_config_sha256": materialized_config_sha256(profile),
        "mutmut_version_locked": MUTMUT_VERSION,
        "mutation_executed": False,
    }


def execute_profile(profile_id: str) -> dict[str, Any]:
    _policy, profile = _validated_profile(profile_id)
    _check_locked_mutmut(require_installed=True)
    immutable_paths = list(profile["source_immutability"]["verify_paths"])
    restore_paths = list(profile["source_immutability"]["restore_paths"])
    _require_clean([*restore_paths, *immutable_paths], "mutation inputs")

    evidence_dir = _safe_evidence_path(profile)
    if evidence_dir.exists():
        shutil.rmtree(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    mutants = ROOT / "mutants"
    if mutants.exists():
        shutil.rmtree(mutants)

    original_pyproject = PYPROJECT_PATH.read_bytes()
    source_head = _head_sha()
    config_sha = materialized_config_sha256(profile)
    run_text = ""
    results_text = ""
    run_rc = results_rc = -1
    try:
        original_text = original_pyproject.decode("utf-8")
        PYPROJECT_PATH.write_text(
            materialize_pyproject_text(original_text, profile),
            encoding="utf-8",
        )
        run_rc, run_text = _run_fixed("run")
        (evidence_dir / profile["evidence"]["run_log"]).write_text(
            run_text,
            encoding="utf-8",
        )
        if run_rc != 0:
            raise MutationRunnerError(f"mutmut run failed with exit code {run_rc}")
        results_rc, results_text = _run_fixed("results")
        (evidence_dir / profile["evidence"]["results_log"]).write_text(
            results_text,
            encoding="utf-8",
        )
        if results_rc != 0:
            raise MutationRunnerError(
                f"mutmut results failed with exit code {results_rc}"
            )
    finally:
        PYPROJECT_PATH.write_bytes(original_pyproject)
        if mutants.exists():
            shutil.rmtree(mutants)

    _require_clean(restore_paths, "restored mutation config")
    _require_clean(immutable_paths, "mutation source")
    counts = parse_counts(run_text)
    score, numerator, denominator = score_counts(counts, profile["score"])
    minimum = float(profile["score"]["minimum_percent"])
    status = "PASS" if score >= minimum else "FAIL"
    common = {
        "schema_version": "mutation-profile-evidence-v1",
        "profile_id": profile["id"],
        "profile_version": profile["profile_version"],
        "source_head": source_head,
        "source_binding": profile["source_binding"]["mode"],
        "legacy_workflow": profile["legacy_reference"]["workflow"],
        "legacy_workflow_blob": _git_blob(profile["legacy_reference"]["workflow"]),
        "materialized_config_sha256": config_sha,
        "mutmut_version": MUTMUT_VERSION,
        "python_version": PYTHON_VERSION,
        "counts": counts,
        "score": {
            "numerator_terms": profile["score"]["numerator"],
            "denominator_terms": profile["score"]["denominator"],
            "require_zero": profile["score"]["require_zero"],
            "numerator": numerator,
            "denominator": denominator,
            "score_percent": round(score, 2),
            "minimum_percent": minimum,
        },
        "status": status,
        "fixed_commands": [
            ["python", "-m", "mutmut", "run"],
            ["python", "-m", "mutmut", "results"],
        ],
    }
    _write_json(evidence_dir / "profile_evidence.json", common)

    legacy_score = {
        "schema_version": profile["evidence"]["schema_version"],
        "scope": profile["id"],
        **counts,
        "evaluated": denominator,
        "score_percent": round(score, 2),
        "minimum_score_percent": minimum,
        "status": status,
    }
    _write_json(evidence_dir / profile["evidence"]["score_file"], legacy_score)
    if status != "PASS":
        raise MutationRunnerError(
            f"MUTATION_PROFILE_BELOW_THRESHOLD:{score:.2f}<{minimum:.2f}"
        )
    return common


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            validate_only(args.profile)
            if args.validate_only
            else execute_profile(args.profile)
        )
    except (MutationRunnerError, OSError, KeyError, TypeError) as exc:
        print(f"MUTATION_RUNNER_INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

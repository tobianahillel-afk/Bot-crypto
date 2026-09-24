#!/usr/bin/env python3
"""Benchmark an exact lychee binary in offline local-link mode only."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "documentation_tooling_lychee_benchmark_v1.json"


class LycheeBenchmarkError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LycheeBenchmarkError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LycheeBenchmarkError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise LycheeBenchmarkError("unsupported lychee benchmark policy version")
    if policy.get("policy_kind") != "documentation_tooling_lychee_benchmark_v1":
        raise LycheeBenchmarkError("invalid lychee benchmark policy kind")
    if policy.get("semantics") != "LYCHEE_PINNED_OFFLINE_LOCAL_LINKS_EVIDENCE_ONLY":
        raise LycheeBenchmarkError("lychee benchmark semantics drift")
    if policy.get("authority_role") != "NON_AUTHORITATIVE":
        raise LycheeBenchmarkError("lychee benchmark cannot become documentation authority")

    release = policy.get("release")
    if not isinstance(release, dict):
        raise LycheeBenchmarkError("lychee release metadata missing")
    expected = {
        "tag": "lychee-v0.24.2",
        "source_commit": "2bba271688c1abb1503097a064e6c3bc1d1b6a9b",
        "asset_name": "lychee-x86_64-unknown-linux-gnu.tar.gz",
        "asset_sha256": "1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a",
        "expected_version": "0.24.2",
        "license": "MIT OR Apache-2.0",
    }
    for key, value in expected.items():
        if release.get(key) != value:
            raise LycheeBenchmarkError(f"lychee release {key} drift")
    if release.get("immutable_release") is not False:
        raise LycheeBenchmarkError("lychee release mutability observation drift")
    if release.get("asset_digest_is_execution_authority") is not True:
        raise LycheeBenchmarkError("asset digest must remain the execution authority")
    url = release.get("asset_url")
    if not isinstance(url, str) or not url.startswith(
        "https://github.com/lycheeverse/lychee/releases/download/lychee-v0.24.2/"
    ):
        raise LycheeBenchmarkError("lychee asset URL drift")

    workflow = policy.get("workflow")
    if not isinstance(workflow, dict):
        raise LycheeBenchmarkError("lychee workflow policy missing")
    if workflow.get("checkout_action_sha") != "3d3c42e5aac5ba805825da76410c181273ba90b1":
        raise LycheeBenchmarkError("checkout action pin drift")
    if workflow.get("permissions") != {"contents": "read"}:
        raise LycheeBenchmarkError("lychee workflow must remain contents-read only")

    execution = policy.get("execution")
    if not isinstance(execution, dict):
        raise LycheeBenchmarkError("lychee execution policy missing")
    if execution.get("offline_required") is not True:
        raise LycheeBenchmarkError("lychee offline mode is mandatory")
    for key in (
        "external_url_health_checks_allowed",
        "github_token_required",
        "cache_allowed",
        "paid_api_required",
        "paid_saas_required",
        "paid_llm_required",
        "paid_runner_required",
    ):
        if execution.get(key) is not False:
            raise LycheeBenchmarkError(f"{key} must remain false")
    if execution.get("download_network_scope") != "PINNED_RELEASE_ASSET_ONLY":
        raise LycheeBenchmarkError("download network scope drift")
    if execution.get("max_representative_docs") != 4:
        raise LycheeBenchmarkError("representative-doc cap drift")
    if not 100 <= execution.get("max_lychee_elapsed_ms", 0) <= 10000:
        raise LycheeBenchmarkError("invalid lychee elapsed-time budget")
    if execution.get("broken_fixture_required_errors") != 1:
        raise LycheeBenchmarkError("broken fixture error floor drift")
    if execution.get("valid_fixture_max_errors") != 0:
        raise LycheeBenchmarkError("valid fixture error ceiling drift")

    docs = policy.get("representative_docs")
    if not isinstance(docs, list) or len(docs) != execution["max_representative_docs"]:
        raise LycheeBenchmarkError("representative-doc set must match configured cap")
    if len(docs) != len(set(docs)):
        raise LycheeBenchmarkError("representative-doc set contains duplicates")
    for item in docs:
        path = Path(item)
        if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".md":
            raise LycheeBenchmarkError(f"unsafe representative doc path: {item}")


def _command(lychee_bin: Path, inputs: list[str]) -> list[str]:
    if not inputs:
        raise LycheeBenchmarkError("lychee benchmark needs at least one local input")
    for item in inputs:
        lowered = item.lower()
        if "://" in lowered or lowered.startswith("mailto:"):
            raise LycheeBenchmarkError(f"remote input forbidden in offline benchmark: {item}")
    return [
        str(lychee_bin),
        "--offline",
        "--format",
        "json",
        "--no-progress",
        "--cache=false",
        *inputs,
    ]


def _run(
    lychee_bin: Path,
    inputs: list[str],
    *,
    cwd: Path,
) -> tuple[subprocess.CompletedProcess[str], float, dict[str, Any]]:
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            _command(lychee_bin, inputs),
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "NO_COLOR": "1"},
        )
    except subprocess.TimeoutExpired as exc:
        raise LycheeBenchmarkError("lychee invocation timed out") from exc
    elapsed = round((time.perf_counter() - started) * 1000, 3)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise LycheeBenchmarkError(
            f"lychee JSON output invalid (exit={proc.returncode}): {proc.stdout[-1500:]!r}"
        ) from exc
    if not isinstance(payload, dict):
        raise LycheeBenchmarkError("lychee JSON output must be an object")
    for key in ("total", "successful", "errors", "timeouts", "unknown", "unsupported"):
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise LycheeBenchmarkError(f"lychee JSON counter invalid: {key}={value!r}")
    return proc, elapsed, payload


def _validate_binary(lychee_bin: Path, policy: dict[str, Any]) -> str:
    if not lychee_bin.is_file():
        raise LycheeBenchmarkError(f"lychee binary missing: {lychee_bin}")
    try:
        proc = subprocess.run(
            [str(lychee_bin), "--version"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired as exc:
        raise LycheeBenchmarkError("lychee --version timed out") from exc
    if proc.returncode != 0:
        raise LycheeBenchmarkError("lychee --version failed")
    version = (proc.stdout + "\n" + proc.stderr).strip()
    if policy["release"]["expected_version"] not in version:
        raise LycheeBenchmarkError(f"unexpected lychee version: {version!r}")
    return version


def _stats(payload: dict[str, Any], elapsed_ms: float, exit_code: int) -> dict[str, Any]:
    return {
        "exit_code": exit_code,
        "elapsed_ms": elapsed_ms,
        "total": payload["total"],
        "successful": payload["successful"],
        "errors": payload["errors"],
        "timeouts": payload["timeouts"],
        "unknown": payload["unknown"],
        "unsupported": payload["unsupported"],
    }


def benchmark(lychee_bin: Path, policy: dict[str, Any]) -> dict[str, Any]:
    validate_policy(policy)
    version = _validate_binary(lychee_bin, policy)
    representative = []
    for item in policy["representative_docs"]:
        path = ROOT / item
        if not path.is_file():
            raise LycheeBenchmarkError(f"representative doc missing: {item}")
        representative.append(item)

    with tempfile.TemporaryDirectory(prefix="cqb-lychee-benchmark-") as raw:
        tmp = Path(raw)
        (tmp / "target.md").write_text("# Existing target\n", encoding="utf-8")
        (tmp / "valid.md").write_text("[existing](target.md)\n", encoding="utf-8")
        (tmp / "broken.md").write_text("[missing](missing-target.md)\n", encoding="utf-8")

        broken_proc, broken_ms, broken_json = _run(
            lychee_bin, ["broken.md"], cwd=tmp
        )
        if broken_proc.returncode != 2:
            raise LycheeBenchmarkError(
                f"broken local link must return exit code 2, got {broken_proc.returncode}"
            )
        if broken_json["errors"] < policy["execution"]["broken_fixture_required_errors"]:
            raise LycheeBenchmarkError("broken local link did not produce required error")

        valid_proc, valid_ms, valid_json = _run(
            lychee_bin, ["valid.md"], cwd=tmp
        )
        if valid_proc.returncode != 0:
            raise LycheeBenchmarkError(
                f"valid local link must pass, got exit code {valid_proc.returncode}"
            )
        if valid_json["errors"] > policy["execution"]["valid_fixture_max_errors"]:
            raise LycheeBenchmarkError("valid local link produced an error")

    representative_proc, representative_ms, representative_json = _run(
        lychee_bin, representative, cwd=ROOT
    )
    if representative_proc.returncode not in (0, 2):
        raise LycheeBenchmarkError(
            f"representative lychee run failed operationally: {representative_proc.returncode}"
        )

    total_ms = round(broken_ms + valid_ms + representative_ms, 3)
    if total_ms > policy["execution"]["max_lychee_elapsed_ms"]:
        raise LycheeBenchmarkError(
            f"lychee benchmark exceeded {policy['execution']['max_lychee_elapsed_ms']} ms: "
            f"{total_ms}"
        )

    return {
        "schema_version": 1,
        "benchmark_kind": "lychee_offline_local_links_v1",
        "lychee_version_output": version,
        "release_tag": policy["release"]["tag"],
        "release_source_commit": policy["release"]["source_commit"],
        "asset_sha256": policy["release"]["asset_sha256"],
        "synthetic_broken": _stats(broken_json, broken_ms, broken_proc.returncode),
        "synthetic_valid": _stats(valid_json, valid_ms, valid_proc.returncode),
        "representative": {
            "documents": representative,
            **_stats(
                representative_json,
                representative_ms,
                representative_proc.returncode,
            ),
        },
        "total_lychee_elapsed_ms": total_ms,
        "offline_required": True,
        "external_url_health_checks": False,
        "github_token_used": False,
        "paid_dependency": False,
        "authority_role": policy["authority_role"],
        "verdict": "PASS",
    }


def _self_check(policy: dict[str, Any]) -> None:
    validate_policy(policy)
    fake = Path("/tmp/lychee")
    command = _command(fake, ["README.md"])
    if "--offline" not in command:
        raise LycheeBenchmarkError("offline flag missing from constructed command")
    if "--cache=false" not in command:
        raise LycheeBenchmarkError("disk cache must remain disabled")
    try:
        _command(fake, ["https://example.com"])
    except LycheeBenchmarkError:
        pass
    else:
        raise LycheeBenchmarkError("remote URL input unexpectedly accepted")
    try:
        _command(fake, ["mailto:test@example.com"])
    except LycheeBenchmarkError:
        pass
    else:
        raise LycheeBenchmarkError("mailto input unexpectedly accepted")
    print("DOCUMENTATION_TOOLING_LYCHEE_SELF_CHECK_PASS probes=4")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--lychee-bin", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        policy = _json(POLICY_PATH)
        if args.self_check:
            _self_check(policy)
            return 0
        if args.lychee_bin is None:
            raise LycheeBenchmarkError("--lychee-bin is required unless --self-check is used")
        result = benchmark(args.lychee_bin, policy)
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
        print("LYCHEE_BENCHMARK_RESULT=" + encoded)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return 0
    except (LycheeBenchmarkError, KeyError, TypeError) as exc:
        print(f"DOCUMENTATION_TOOLING_LYCHEE_INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

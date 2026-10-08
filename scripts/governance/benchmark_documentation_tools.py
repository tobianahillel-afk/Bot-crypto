#!/usr/bin/env python3
"""Benchmark an exact Vale binary using temporary local rules only."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "documentation_tooling_benchmark_v1.json"


class ValeBenchmarkError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValeBenchmarkError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValeBenchmarkError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise ValeBenchmarkError("unsupported benchmark policy schema_version")
    if policy.get("policy_kind") != "documentation_tooling_benchmark_v1":
        raise ValeBenchmarkError("invalid benchmark policy kind")
    if policy.get("semantics") != "VALE_PINNED_OFFLINE_LOCAL_RULES_EVIDENCE_ONLY":
        raise ValeBenchmarkError("benchmark semantics drift")
    if policy.get("authority_role") != "NON_AUTHORITATIVE":
        raise ValeBenchmarkError("Vale benchmark cannot become documentation authority")

    release = policy.get("release")
    if not isinstance(release, dict):
        raise ValeBenchmarkError("Vale release metadata missing")
    expected = {
        "tag": "v3.22.0",
        "source_commit": "e109c06297dc58a513f10691a275f3a9465584a1",
        "asset_name": "vale_3.22.0_Linux_64-bit.tar.gz",
        "asset_sha256": "52f5cd0314a1b7384cac6aa102a68193977312f6ba9c9f3ae001b5deec8e3a10",
        "expected_version": "3.22.0",
        "license": "MIT",
    }
    for key, value in expected.items():
        if release.get(key) != value:
            raise ValeBenchmarkError(f"Vale release {key} drift")
    if release.get("immutable_release") is not True:
        raise ValeBenchmarkError("Vale release must remain immutable")
    url = release.get("asset_url")
    if not isinstance(url, str) or not url.startswith(
        "https://github.com/vale-cli/vale/releases/download/v3.22.0/"
    ):
        raise ValeBenchmarkError("Vale asset URL drift")

    workflow = policy.get("workflow")
    if not isinstance(workflow, dict):
        raise ValeBenchmarkError("benchmark workflow policy missing")
    if workflow.get("checkout_action_sha") != "3d3c42e5aac5ba805825da76410c181273ba90b1":
        raise ValeBenchmarkError("checkout action pin drift")
    if workflow.get("permissions") != {"contents": "read"}:
        raise ValeBenchmarkError("benchmark workflow must remain contents-read only")

    execution = policy.get("execution")
    if not isinstance(execution, dict):
        raise ValeBenchmarkError("benchmark execution policy missing")
    for key in (
        "package_sync_allowed",
        "remote_style_packages_allowed",
        "vale_runtime_network_required",
        "paid_api_required",
        "paid_saas_required",
        "paid_llm_required",
        "paid_runner_required",
    ):
        if execution.get(key) is not False:
            raise ValeBenchmarkError(f"{key} must remain False")
    if execution.get("download_network_scope") != "PINNED_RELEASE_ASSET_ONLY":
        raise ValeBenchmarkError("download network scope drift")
    if execution.get("max_representative_docs") != 4:
        raise ValeBenchmarkError("representative-doc cap drift")
    if not 100 <= execution.get("max_vale_elapsed_ms", 0) <= 10000:
        raise ValeBenchmarkError("invalid Vale elapsed-time budget")
    if execution.get("min_synthetic_findings") != 1:
        raise ValeBenchmarkError("synthetic finding floor drift")
    if execution.get("max_representative_findings") != 0:
        raise ValeBenchmarkError("representative finding ceiling drift")

    rule = policy.get("local_rule")
    if not isinstance(rule, dict):
        raise ValeBenchmarkError("local rule missing")
    if rule.get("forbidden_token") != "ENGINEBENCHPLACEHOLDER":
        raise ValeBenchmarkError("synthetic token drift")
    if rule.get("level") != "error":
        raise ValeBenchmarkError("synthetic rule must remain error-level")

    docs = policy.get("representative_docs")
    if not isinstance(docs, list) or len(docs) != execution["max_representative_docs"]:
        raise ValeBenchmarkError("representative-doc set must match configured cap")
    if len(docs) != len(set(docs)):
        raise ValeBenchmarkError("representative-doc set contains duplicates")
    for item in docs:
        path = Path(item)
        if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".md":
            raise ValeBenchmarkError(f"unsafe representative doc path: {item}")


def _run(command: list[str], *, cwd: Path, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "NO_COLOR": "1"},
        )
    except subprocess.TimeoutExpired as exc:
        raise ValeBenchmarkError(f"command timed out: {command[0]}") from exc
    if not allow_failure and proc.returncode != 0:
        tail = (proc.stdout + "\n" + proc.stderr)[-4000:]
        raise ValeBenchmarkError(f"command failed ({proc.returncode}): {tail}")
    return proc


def _parse_vale_json(text: str) -> tuple[int, set[str]]:
    stripped = text.strip()
    if not stripped:
        return 0, set()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValeBenchmarkError(f"Vale JSON output invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValeBenchmarkError("Vale JSON output must be an object")
    count = 0
    checks: set[str] = set()
    for alerts in payload.values():
        if not isinstance(alerts, list):
            raise ValeBenchmarkError("Vale JSON file alerts must be arrays")
        count += len(alerts)
        for alert in alerts:
            if isinstance(alert, dict) and isinstance(alert.get("Check"), str):
                checks.add(alert["Check"])
    return count, checks


def _write_local_config(tmp: Path, policy: dict[str, Any]) -> tuple[Path, Path]:
    style = policy["local_rule"]["style_name"]
    rule_name = policy["local_rule"]["rule_name"]
    styles = tmp / "styles" / style
    styles.mkdir(parents=True, exist_ok=True)
    rule_file = styles / f"{rule_name}.yml"
    rule_file.write_text(
        "\n".join(
            [
                "extends: substitution",
                "message: \"Use '%s' instead of '%s'.\"",
                f"level: {policy['local_rule']['level']}",
                "ignorecase: False",
                "swap:",
                f"  '{policy['local_rule']['forbidden_token']}': '{policy['local_rule']['replacement']}'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    config = tmp / ".vale.ini"
    config.write_text(
        "\n".join(
            [
                f"StylesPath = {tmp / 'styles'}",
                "MinAlertLevel = suggestion",
                "",
                "[*.md]",
                f"BasedOnStyles = {style}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config, rule_file


def _validate_vale_binary(vale_bin: Path, policy: dict[str, Any]) -> str:
    if not vale_bin.is_file():
        raise ValeBenchmarkError(f"Vale binary missing: {vale_bin}")
    proc = _run([str(vale_bin), "--version"], cwd=ROOT)
    version_text = (proc.stdout + "\n" + proc.stderr).strip()
    if policy["release"]["expected_version"] not in version_text:
        raise ValeBenchmarkError(f"unexpected Vale version: {version_text!r}")
    return version_text


def benchmark(vale_bin: Path, policy: dict[str, Any]) -> dict[str, Any]:
    validate_policy(policy)
    version = _validate_vale_binary(vale_bin, policy)
    representative_paths: list[Path] = []
    for item in policy["representative_docs"]:
        path = ROOT / item
        if not path.is_file():
            raise ValeBenchmarkError(f"representative doc missing: {item}")
        representative_paths.append(path)

    with tempfile.TemporaryDirectory(prefix="cqb-vale-benchmark-") as raw:
        tmp = Path(raw)
        config, _rule_file = _write_local_config(tmp, policy)
        synthetic = tmp / "synthetic.md"
        synthetic.write_text(
            "# Synthetic benchmark\n\n"
            + policy["local_rule"]["forbidden_token"]
            + " must be detected.\n",
            encoding="utf-8",
        )

        started = time.perf_counter()
        synthetic_run = _run(
            [str(vale_bin), "--config", str(config), "--output", "JSON", str(synthetic)],
            cwd=ROOT,
            allow_failure=True,
        )
        synthetic_ms = round((time.perf_counter() - started) * 1000, 3)
        synthetic_count, synthetic_checks = _parse_vale_json(synthetic_run.stdout)
        expected_check = (
            policy["local_rule"]["style_name"] + "." + policy["local_rule"]["rule_name"]
        )
        if synthetic_count < policy["execution"]["min_synthetic_findings"]:
            raise ValeBenchmarkError("synthetic Vale violation was not detected")
        if expected_check not in synthetic_checks:
            raise ValeBenchmarkError(
                f"synthetic finding did not use expected local rule: {sorted(synthetic_checks)}"
            )

        started = time.perf_counter()
        representative_run = _run(
            [
                str(vale_bin),
                "--config",
                str(config),
                "--output",
                "JSON",
                *[str(path) for path in representative_paths],
            ],
            cwd=ROOT,
            allow_failure=True,
        )
        representative_ms = round((time.perf_counter() - started) * 1000, 3)
        representative_count, representative_checks = _parse_vale_json(
            representative_run.stdout
        )
        if representative_count > policy["execution"]["max_representative_findings"]:
            raise ValeBenchmarkError(
                f"representative findings exceed benchmark ceiling: {representative_count}"
            )

    total_vale_ms = round(synthetic_ms + representative_ms, 3)
    if total_vale_ms > policy["execution"]["max_vale_elapsed_ms"]:
        raise ValeBenchmarkError(
            f"Vale benchmark exceeded {policy['execution']['max_vale_elapsed_ms']} ms: "
            f"{total_vale_ms}"
        )
    return {
        "schema_version": 1,
        "benchmark_kind": "vale_offline_local_rules_v1",
        "vale_version_output": version,
        "release_tag": policy["release"]["tag"],
        "release_source_commit": policy["release"]["source_commit"],
        "asset_sha256": policy["release"]["asset_sha256"],
        "synthetic": {
            "finding_count": synthetic_count,
            "checks": sorted(synthetic_checks),
            "elapsed_ms": synthetic_ms,
        },
        "representative": {
            "documents": policy["representative_docs"],
            "finding_count": representative_count,
            "checks": sorted(representative_checks),
            "elapsed_ms": representative_ms,
        },
        "total_vale_elapsed_ms": total_vale_ms,
        "networked_style_resolution": False,
        "package_sync_executed": False,
        "paid_dependency": False,
        "authority_role": policy["authority_role"],
        "verdict": "PASS",
    }


def _self_check(policy: dict[str, Any]) -> None:
    validate_policy(policy)
    with tempfile.TemporaryDirectory(prefix="cqb-vale-selfcheck-") as raw:
        tmp = Path(raw)
        config, rule = _write_local_config(tmp, policy)
        config_text = config.read_text(encoding="utf-8")
        rule_text = rule.read_text(encoding="utf-8")
        if "Packages" in config_text or "https://" in config_text or "http://" in config_text:
            raise ValeBenchmarkError("temporary Vale config contains remote/package resolution")
        if "BasedOnStyles = CQBBenchmark" not in config_text:
            raise ValeBenchmarkError("temporary Vale config did not enable local benchmark style")
        if policy["local_rule"]["forbidden_token"] not in rule_text:
            raise ValeBenchmarkError("temporary Vale rule missing synthetic token")
    print("DOCUMENTATION_TOOLING_BENCHMARK_SELF_CHECK_PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--vale-bin", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        policy = _json(POLICY_PATH)
        if args.self_check:
            _self_check(policy)
            return 0
        if args.vale_bin is None:
            raise ValeBenchmarkError("--vale-bin is required unless --self-check is used")
        result = benchmark(args.vale_bin, policy)
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
        print("VALE_BENCHMARK_RESULT=" + encoded)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    except (ValeBenchmarkError, KeyError, TypeError) as exc:
        print(f"DOCUMENTATION_TOOLING_BENCHMARK_INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

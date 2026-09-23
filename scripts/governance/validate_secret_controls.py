#!/usr/bin/env python3
"""Validate ENG-04.1 secret-control configuration without executing Gitleaks."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "governance" / "secret_control_policy_v1.json"
CONFIG_PATH = ROOT / ".gitleaks.toml"
IGNORE_PATH = ROOT / ".gitleaksignore"


class SecretControlError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SecretControlError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SecretControlError(f"{path} must contain an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise SecretControlError("unsupported secret-control policy schema_version")
    if policy.get("policy_kind") != "secret_control_policy_v1":
        raise SecretControlError("invalid secret-control policy kind")
    if policy.get("semantics") != "PINNED_MIT_GITLEAKS_REDACTED_FAIL_CLOSED":
        raise SecretControlError("secret-control semantics drift")
    gl = policy.get("gitleaks")
    if not isinstance(gl, dict):
        raise SecretControlError("gitleaks pin missing")
    if gl.get("tag") != "v8.30.1":
        raise SecretControlError("Gitleaks tag drift")
    if gl.get("commit") != "83d9cd684c87d95d656c1458ef04895a7f1cbd8e":
        raise SecretControlError("Gitleaks commit drift")
    if gl.get("version") != "8.30.1" or gl.get("license") != "MIT":
        raise SecretControlError("Gitleaks version/license drift")
    toolchain = policy.get("toolchain")
    if not isinstance(toolchain, dict):
        raise SecretControlError("toolchain pin missing")
    if toolchain.get("go_version") != "1.24.11":
        raise SecretControlError("Go version drift")
    for key in ("checkout_action_sha", "setup_go_action_sha"):
        value = toolchain.get(key)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
            raise SecretControlError(f"{key} must be exact 40-hex SHA")
    cost = policy.get("cost_policy")
    if not isinstance(cost, dict) or any(cost.values()):
        raise SecretControlError("mandatory secret-control path must remain zero-cost")
    if policy.get("required_redaction_percent") != 100:
        raise SecretControlError("full redaction is mandatory")
    if policy.get("required_scans") != [
        "SYNTHETIC_POSITIVE_CONTROL", "CURRENT_TREE", "FULL_GIT_HISTORY"
    ]:
        raise SecretControlError("required scan set drift")
    if policy.get("false_positive_policy") != "EXACT_FINGERPRINT_PLUS_IMMUTABLE_GIT_BLOB_BINDING_ONLY":
        raise SecretControlError("false-positive policy drift")
    if policy.get("false_positive_registry") != "config/governance/secret_false_positive_registry_v1.json":
        raise SecretControlError("false-positive registry path drift")
    if policy.get("gitleaks_ignore_path") != ".gitleaksignore":
        raise SecretControlError("Gitleaks ignore path drift")


def validate_config(config_text: str) -> None:
    try:
        parsed = tomllib.loads(config_text)
    except tomllib.TOMLDecodeError as exc:
        raise SecretControlError(f"invalid .gitleaks.toml: {exc}") from exc
    extend = parsed.get("extend")
    if not isinstance(extend, dict) or extend.get("useDefault") is not True:
        raise SecretControlError("default Gitleaks rules must remain enabled")
    if "allowlist" in config_text.lower():
        raise SecretControlError("secret allowlists require separate finding-specific review")


def _head_blob_sha(path: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", f"HEAD:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SecretControlError(f"cannot resolve HEAD blob for {path}: {proc.stderr.strip()}")
    blob = proc.stdout.strip()
    if re.fullmatch(r"[0-9a-f]{40}", blob) is None:
        raise SecretControlError(f"invalid HEAD blob SHA for {path}: {blob!r}")
    diff = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", path],
        cwd=ROOT,
        check=False,
    )
    if diff.returncode != 0:
        raise SecretControlError(f"bound audit artifact has working-tree changes: {path}")
    return blob


def validate_false_positive_registry(policy: dict[str, Any], ignore_text: str) -> None:
    registry = _json(ROOT / policy["false_positive_registry"])
    if registry.get("schema_version") != 1:
        raise SecretControlError("unsupported false-positive registry version")
    if registry.get("registry_kind") != "secret_false_positive_registry_v1":
        raise SecretControlError("invalid false-positive registry kind")
    if registry.get("semantics") != "EXACT_FINGERPRINT_BOUND_TO_IMMUTABLE_AUDIT_BLOB":
        raise SecretControlError("false-positive registry semantics drift")

    artifact = registry.get("artifact")
    if not isinstance(artifact, dict):
        raise SecretControlError("false-positive artifact binding missing")
    artifact_path = artifact.get("path")
    if artifact_path != "data/audit/product_scope_roadmap_lot21.jsonl":
        raise SecretControlError("false-positive artifact path drift")
    if artifact.get("historical_evidence") is not True:
        raise SecretControlError("false-positive artifact must remain historical evidence")
    if artifact.get("mutation_forbidden_in_awu") != "ENG-04.1-WU01":
        raise SecretControlError("historical mutation prohibition drift")

    full = ROOT / artifact_path
    try:
        data = full.read_bytes()
    except OSError as exc:
        raise SecretControlError(f"cannot read bound audit artifact: {exc}") from exc
    actual_blob = _head_blob_sha(artifact_path)
    if actual_blob != artifact.get("git_blob_sha"):
        raise SecretControlError(
            f"false-positive artifact blob changed: {actual_blob} != {artifact.get('git_blob_sha')}"
        )

    entries = registry.get("entries")
    if not isinstance(entries, list) or len(entries) != 2:
        raise SecretControlError("exactly two vetted false-positive entries are required")

    lines = data.decode("utf-8").splitlines()
    expected_fingerprints: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise SecretControlError("false-positive entry must be an object")
        line_no = entry.get("line")
        if not isinstance(line_no, int) or not 1 <= line_no <= len(lines):
            raise SecretControlError("false-positive line out of range")
        fingerprint = f"{artifact_path}:generic-api-key:{line_no}"
        if entry.get("fingerprint") != fingerprint:
            raise SecretControlError("false-positive fingerprint does not match bound line")
        if entry.get("classification") != "FALSE_POSITIVE_CONTRACT_IDENTIFIER_ADJACENCY":
            raise SecretControlError("false-positive classification drift")
        if entry.get("json_field") != "output_contracts":
            raise SecretControlError("false-positive must remain bound to output_contracts")
        try:
            record = json.loads(lines[line_no - 1])
        except json.JSONDecodeError as exc:
            raise SecretControlError(f"bound audit line is not JSON: {line_no}") from exc
        if record.get("lot_id") != entry.get("lot_id") or record.get("title") != entry.get("title"):
            raise SecretControlError("false-positive lot identity drift")
        contracts = record.get("output_contracts")
        if contracts != entry.get("expected_contract_identifiers"):
            raise SecretControlError("false-positive contract identifiers drift")
        if not isinstance(contracts, list) or not all(
            isinstance(name, str) and re.fullmatch(r"[A-Z][A-Za-z0-9]+V1", name)
            for name in contracts
        ):
            raise SecretControlError("vetted false-positive values must remain contract identifiers")
        expected_fingerprints.append(fingerprint)

    active = [
        line.strip()
        for line in ignore_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if active != expected_fingerprints:
        raise SecretControlError(
            f".gitleaksignore must exactly equal vetted registry fingerprints: {active}"
        )


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SecretControlError(f"workflow missing {label}: {needle}")


def validate_workflow(policy: dict[str, Any], workflow_text: str) -> None:
    for token in policy["forbidden_tokens"]:
        if token in workflow_text:
            raise SecretControlError(f"forbidden workflow token present: {token}")
    if "permissions:\n  contents: read\n" not in workflow_text:
        raise SecretControlError("workflow permissions must be contents: read only")
    toolchain = policy["toolchain"]
    _require(
        workflow_text,
        "actions/checkout@" + toolchain["checkout_action_sha"],
        "exact checkout pin",
    )
    _require(
        workflow_text,
        "actions/setup-go@" + toolchain["setup_go_action_sha"],
        "exact setup-go pin",
    )
    _require(workflow_text, 'go-version: "' + toolchain["go_version"] + '"', "exact Go version")
    gl = policy["gitleaks"]
    _require(workflow_text, 'GITLEAKS_TAG: "' + gl["tag"] + '"', "Gitleaks tag")
    _require(workflow_text, 'GITLEAKS_COMMIT: "' + gl["commit"] + '"', "Gitleaks commit")
    _require(
        workflow_text,
        'GITLEAKS_EXPECTED_VERSION: "' + gl["version"] + '"',
        "Gitleaks version",
    )
    _require(workflow_text, 'git -C "${src}" rev-parse HEAD', "source commit verification")
    _require(workflow_text, 'test "${actual}" = "${GITLEAKS_COMMIT}"', "commit equality check")
    _require(
        workflow_text,
        "github.com/zricethezav/gitleaks/v8/version.Version=${GITLEAKS_TAG}",
        "official version ldflags",
    )
    _require(workflow_text, "--gitleaks-ignore-path .gitleaksignore", "explicit vetted ignore path")
    if workflow_text.count("--gitleaks-ignore-path .gitleaksignore") < 3:
        raise SecretControlError("all three scans must use the vetted ignore file")
    _require(workflow_text, "--redact=100", "full redaction")
    if workflow_text.count("--redact=100") < 3:
        raise SecretControlError("all three scans must use full redaction")
    _require(workflow_text, '"${GITLEAKS_BIN}" dir', "directory scan")
    _require(workflow_text, '"${GITLEAKS_BIN}" git', "Git history scan")
    _require(workflow_text, "--report-format json", "ephemeral JSON report")
    _require(workflow_text, "path.unlink(missing_ok=True)", "ephemeral report deletion")
    _require(workflow_text, "GITLEAKS_CURRENT_STATUS", "current-scan status binding")
    _require(workflow_text, "GITLEAKS_HISTORY_STATUS", "history-scan status binding")
    _require(workflow_text, "Enforce clean secret scans", "fail-closed final gate")
    for forbidden_field in ('finding.get("Secret")', 'finding.get("Match")'):
        if forbidden_field in workflow_text:
            raise SecretControlError("workflow must not print secret or match values")
    _require(workflow_text, "fetch-depth: 0", "full checkout history")
    _require(workflow_text, "persist-credentials: false", "credential persistence disabled")
    _require(workflow_text, 'token = "gh" + "p_" + suffix', "runtime-only positive control")
    _require(workflow_text, "for i in range(36)", "high-entropy synthetic suffix")
    if "ghp_" in workflow_text:
        raise SecretControlError("synthetic secret literal must not be committed")
    for trigger in ("push:", "pull_request:", "workflow_dispatch:"):
        _require(workflow_text, trigger, f"{trigger} trigger")


def validate_documents(
    policy: dict[str, Any],
    workflow_text: str,
    config_text: str,
    ignore_text: str,
) -> None:
    validate_policy(policy)
    validate_config(config_text)
    validate_false_positive_registry(policy, ignore_text)
    validate_workflow(policy, workflow_text)


def main() -> int:
    try:
        policy = _json(POLICY_PATH)
        workflow_path = ROOT / policy["workflow_path"]
        workflow_text = workflow_path.read_text(encoding="utf-8")
        config_text = CONFIG_PATH.read_text(encoding="utf-8")
        ignore_text = IGNORE_PATH.read_text(encoding="utf-8")
        validate_documents(policy, workflow_text, config_text, ignore_text)
    except (SecretControlError, OSError, KeyError) as exc:
        print(f"SECRET_CONTROLS_INVALID: {exc}", file=sys.stderr)
        return 1
    print("SECRET_CONTROLS_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Adversarial qualification for exact-input proof reuse semantics."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]


def _module()->ModuleType:
    path=ROOT/"scripts"/"governance"/"proof_reuse.py"
    spec=importlib.util.spec_from_file_location("proof_reuse_selftest_engine",path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def _expect(exc_type:type[Exception],fn:Any,label:str)->None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"proof-reuse negative scenario unexpectedly passed: {label}")


def main()->int:
    mod=_module()
    policy=mod._json(mod.POLICY_PATH)
    mod.validate_policy(policy)

    with tempfile.TemporaryDirectory() as raw:
        root=Path(raw)
        for name,text in {
            "input.py":"VALUE = 1\n",
            "policy.json":'{"v":1}\n',
            "impl.py":"def f():\n    return 1\n",
        }.items():
            (root/name).write_text(text,encoding="utf-8")
        env={
            "python_implementation":"CPython",
            "python_version":"3.11.9",
            "platform":"linux",
            "machine":"x86_64",
        }
        kwargs=dict(
            tier="T2",
            subject_id="CHANGED_DOMAIN_TESTS",
            input_paths=["input.py"],
            policy_paths=["policy.json"],
            implementation_paths=["impl.py"],
            parameters={"targets":["tests/test_x.py"],"mode":"q"},
            environment=env,
            policy=policy,
            root=root,
        )
        material=mod.build_material(**kwargs)
        material_again=mod.build_material(**kwargs)
        assert mod.proof_key(material)==mod.proof_key(material_again)

        proof=mod.issue_proof(
            material,result="PASS",
            metadata={
                "observed_head":"a"*40,
                "created_at_utc":"2026-09-23T00:00:00Z",
            },
        )
        reused=mod.evaluate_reuse(proof,material_again,policy)
        assert reused["reusable"] is True

        metadata_changed=copy.deepcopy(proof)
        metadata_changed["metadata"]["observed_head"]="b"*40
        metadata_changed["metadata"]["created_at_utc"]="2099-01-01T00:00:00Z"
        assert mod.evaluate_reuse(metadata_changed,material_again,policy)["reusable"] is True

        (root/"input.py").write_text("VALUE = 2\n",encoding="utf-8")
        changed=mod.build_material(**kwargs)
        assert mod.proof_key(changed)!=proof["proof_key"]
        mismatch=mod.evaluate_reuse(proof,changed,policy)
        assert mismatch["reusable"] is False
        assert mismatch["reason"]=="EXACT_INPUT_KEY_MISMATCH"
        (root/"input.py").write_text("VALUE = 1\n",encoding="utf-8")

        param_kwargs=dict(kwargs)
        param_kwargs["parameters"]={"targets":["tests/test_y.py"],"mode":"q"}
        param_changed=mod.build_material(**param_kwargs)
        assert mod.proof_key(param_changed)!=proof["proof_key"]

        env_kwargs=dict(kwargs)
        env_kwargs["environment"]={**env,"python_version":"3.12.0"}
        env_changed=mod.build_material(**env_kwargs)
        assert mod.proof_key(env_changed)!=proof["proof_key"]

        failed=mod.issue_proof(material,result="FAIL")
        _expect(
            mod.ProofReuseError,
            lambda:mod.evaluate_reuse(failed,material,policy),
            "failed proof reuse",
        )

        tampered=copy.deepcopy(proof)
        tampered["material"]["parameters"]["mode"]="tampered"
        _expect(
            mod.ProofReuseError,
            lambda:mod.evaluate_reuse(tampered,material,policy),
            "tampered material",
        )

        _expect(
            mod.ProofReuseError,
            lambda:mod.build_material(
                **{**kwargs,"tier":"T4","subject_id":"EXACT_HEAD_CERTIFICATION"}
            ),
            "T4 reuse",
        )

        _expect(
            mod.ProofReuseError,
            lambda:mod.build_material(
                **{**kwargs,"input_paths":["../escape.py"]}
            ),
            "path traversal",
        )

        missing_kwargs=dict(kwargs)
        missing_kwargs["input_paths"]=["missing.py"]
        _expect(
            mod.ProofReuseError,
            lambda:mod.build_material(**missing_kwargs),
            "missing file",
        )

        if hasattr(os,"symlink"):
            try:
                os.symlink(root/"input.py",root/"link.py")
            except OSError:
                pass
            else:
                link_kwargs=dict(kwargs)
                link_kwargs["input_paths"]=["link.py"]
                _expect(
                    mod.ProofReuseError,
                    lambda:mod.build_material(**link_kwargs),
                    "symlink binding",
                )

    print("PROOF_REUSE_SELFTEST_PASS probes=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

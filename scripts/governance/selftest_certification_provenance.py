#!/usr/bin/env python3
"""Adversarial qualification for ENG-06.4 certification provenance semantics."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
HEAD="a"*40


def _module()->ModuleType:
    path=ROOT/"scripts/governance/validate_certification_provenance.py"
    spec=importlib.util.spec_from_file_location("certification_provenance_selftest",path)
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
    raise AssertionError(f"provenance negative scenario unexpectedly passed: {label}")


def _input(mod:ModuleType,tree:str="b"*40)->dict[str,Any]:
    material={
        "material_version":1,
        "candidate":{"candidate_id":"CANDIDATE-1","head_sha":HEAD,"risk_class":"R2"},
        "git_tree_sha":tree,
        "bound_blobs":[],
        "context":{"awu_id":"WU","scope_base_sha":"c"*40,"required_t3":[],"required_t4":[]},
    }
    return {"binding_version":1,"input_identity_sha256":mod._sha256_json(material),"material":material}


def _assurance(mod:ModuleType,head:str=HEAD,run_id:int=101)->tuple[dict[str,Any],dict[str,Any]]:
    plan_material={
        "plan_version":1,
        "candidate_head":head,
        "t3_requirements":["WORKFLOW_ASSURANCE"],
        "selection_reasons":[
            {"requirement":"WORKFLOW_ASSURANCE","reason":"RESIDUAL_IMPACT:WORKFLOW_SYNTAX","controls":["WORKFLOW_SECURITY"]}
        ],
        "controls":[
            {"control_id":"WORKFLOW_SECURITY","automatic":True,"workflow_name":"Security Actions","workflow_path":".github/workflows/security-actions.yml"}
        ],
        "execution_model":"EXISTING_EVENT_TRIGGERED_WORKFLOWS_NO_DUPLICATE_SCANNER_RUNS",
    }
    plan={"plan_version":1,"plan_identity_sha256":mod._sha256_json(plan_material),"manual_review_required":False,"material":plan_material}
    result_material={
        "plan_identity_sha256":plan["plan_identity_sha256"],
        "status":"PASS","satisfied":True,"missing_controls":[],"manual_review_required":False,
        "evidence_runs":[{"control_id":"WORKFLOW_SECURITY","run_id":run_id,"workflow":"Security Actions","head_sha":head,"conclusion":"success"}],
    }
    verdict={**result_material,"assurance_identity_sha256":mod._sha256_json(result_material)}
    return plan,verdict


def _workflow(run_id:int=201)->dict[str,Any]:
    return {
        "repository":"tobianahillel-afk/Bot-crypto",
        "workflow_path":".github/workflows/certification-provenance.yml",
        "workflow_ref":"refs/heads/engineering/bootstrap-development-engine",
        "workflow_sha":HEAD,
        "run_id":run_id,
        "run_attempt":1,
    }


def _refs()->list[dict[str,str]]:
    return [
        {"path":"data/audit/domain-state.json","algorithm":"sha256","digest":"1"*64},
        {"path":"reports/certification.json","algorithm":"sha256","digest":"2"*64},
    ]


def main()->int:
    mod=_module()
    policy,lifecycle,exact_head,assurance_policy,evidence=mod._load_policies()
    mod.validate_policy(policy,lifecycle,exact_head,assurance_policy,evidence)

    input1=_input(mod)
    plan,verdict=_assurance(mod)
    refs=_refs()
    env1=mod.build_provenance(
        input1,plan,verdict,_workflow(),refs,policy,
        metadata={"created_at_utc":"2026-09-24T00:00:00Z","notes":"first"},
    )
    env2=mod.build_provenance(
        input1,plan,verdict,_workflow(),refs,policy,
        metadata={"created_at_utc":"2099-01-01T00:00:00Z","notes":"different"},
    )
    assert env1["provenance_identity_sha256"]==env2["provenance_identity_sha256"]
    mod.validate_provenance(env1,policy)
    assert env1["attestation_subject"]["digest"]["sha256"]==env1["provenance_identity_sha256"]
    assert env1["material"]["domain_integrity_refs"]==sorted(refs,key=lambda x:x["path"])

    wrong_input=copy.deepcopy(input1)
    wrong_input["material"]["candidate"]["head_sha"]="b"*40
    wrong_input["input_identity_sha256"]=mod._sha256_json(wrong_input["material"])
    _expect(
        mod.CertificationProvenanceError,
        lambda:mod.build_provenance(wrong_input,plan,verdict,_workflow(),refs,policy),
        "candidate head mismatch",
    )

    wrong_plan,_= _assurance(mod,head="b"*40)
    _expect(
        mod.CertificationProvenanceError,
        lambda:mod.build_provenance(input1,wrong_plan,verdict,_workflow(),refs,policy),
        "assurance head mismatch",
    )

    unsatisfied=copy.deepcopy(verdict)
    body={k:v for k,v in unsatisfied.items() if k!="assurance_identity_sha256"}
    body["satisfied"]=False
    body["status"]="INCOMPLETE"
    unsatisfied={**body,"assurance_identity_sha256":mod._sha256_json(body)}
    _expect(
        mod.CertificationProvenanceError,
        lambda:mod.build_provenance(input1,plan,unsatisfied,_workflow(),refs,policy),
        "unsatisfied assurance",
    )

    input2=_input(mod,tree="d"*40)
    changed_input=mod.build_provenance(input2,plan,verdict,_workflow(),refs,policy)
    assert changed_input["provenance_identity_sha256"]!=env1["provenance_identity_sha256"]

    plan2,verdict2=_assurance(mod,run_id=999)
    changed_assurance=mod.build_provenance(input1,plan2,verdict2,_workflow(),refs,policy)
    assert changed_assurance["provenance_identity_sha256"]!=env1["provenance_identity_sha256"]

    changed_workflow=mod.build_provenance(input1,plan,verdict,_workflow(run_id=777),refs,policy)
    assert changed_workflow["provenance_identity_sha256"]!=env1["provenance_identity_sha256"]

    bad_workflow=_workflow()
    bad_workflow["workflow_sha"]="e"*40
    _expect(
        mod.CertificationProvenanceError,
        lambda:mod.build_provenance(input1,plan,verdict,bad_workflow,refs,policy),
        "workflow SHA mismatch",
    )

    duplicate=refs+[copy.deepcopy(refs[0])]
    _expect(
        mod.CertificationProvenanceError,
        lambda:mod.build_provenance(input1,plan,verdict,_workflow(),duplicate,policy),
        "duplicate domain reference",
    )

    traversal=[{"path":"../secret","algorithm":"sha256","digest":"3"*64}]
    _expect(
        mod.CertificationProvenanceError,
        lambda:mod.build_provenance(input1,plan,verdict,_workflow(),traversal,policy),
        "domain path traversal",
    )

    tampered=copy.deepcopy(env1)
    tampered["material"]["workflow"]["run_id"]=9999
    _expect(
        mod.CertificationProvenanceError,
        lambda:mod.validate_provenance(tampered,policy),
        "provenance tamper",
    )

    wrong_subject=copy.deepcopy(env1)
    wrong_subject["attestation_subject"]["digest"]["sha256"]="f"*64
    _expect(
        mod.CertificationProvenanceError,
        lambda:mod.validate_provenance(wrong_subject,policy),
        "subject digest replacement",
    )

    reordered=list(reversed(refs))
    reordered_env=mod.build_provenance(input1,plan,verdict,_workflow(),reordered,policy)
    assert reordered_env["provenance_identity_sha256"]==env1["provenance_identity_sha256"]

    print("CERTIFICATION_PROVENANCE_SELFTEST_PASS probes=12")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

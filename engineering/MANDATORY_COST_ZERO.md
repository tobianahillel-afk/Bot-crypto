# Mandatory execution cost — ENG-08.4 WU01

ENG-08.4 WU01 performs a **static, offline** audit of the permanent mandatory Development
Engine path. It does not query billing APIs and it does not infer account pricing.

The bounded mandatory workflow set is:

- Engineering Bootstrap;
- Security Secrets;
- Security Dependencies;
- Security SAST;
- Security Actions;
- Security Supply Chain.

The auditor verifies that:

- every `runs-on` value is the standard allowlisted `ubuntu-latest`;
- self-hosted, larger-runner, xlarge and GPU markers are rejected;
- every remote `uses:` reference is a 40-hex commit SHA approved by
  `action_pin_registry_v1.json`;
- every action repository is explicitly classified as public MIT software requiring no
  separate paid credential/service;
- repository `secrets.*` references and known paid-provider credentials are absent;
- the canonical project cost policy, agent capability cost policy and every ENG-04
  governance `cost_policy` contain only boolean `false` values.

## Deliberate WU01 limitation

Static repository files do **not** prove how GitHub bills hosted runner minutes for the
current repository/account. Therefore WU01 returns:

`PASS_WITH_VISIBILITY_UNVERIFIED`

and records:

- `repository_visibility = UNVERIFIED`;
- `github_hosted_runner_cost = UNVERIFIED`;
- `total_mandatory_execution_cost_claim = NOT_MADE_IN_WU01`.

ENG-08.4 WU02 must bind live repository visibility evidence (the repository is expected to be
public) and adversarially qualify failure cases before the project may claim mandatory
execution cost is zero.

Policy: `config/governance/mandatory_cost_zero_policy_v1.json`

Auditor: `scripts/governance/verify_mandatory_cost_zero.py --static`

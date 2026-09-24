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


## WU02 live qualification — 2026-09-24

WU02 binds the static WU01 inventory to two external facts observed on 2026-09-24:

1. the GitHub connector reports repository `tobianahillel-afk/Bot-crypto`,
   id `1322269966`, as **public**, non-archived, default branch `main`;
2. current official GitHub documentation states that standard GitHub-hosted runners are free
   (and the standard public-repository runner table describes them as free/unlimited) for
   public repositories, while larger runners are always billed.

The same official documentation records a default 10 GB Actions cache allowance per
repository; paid cache storage is only relevant above the included allowance when a higher
limit is configured/used. The mandatory engine does not require such expansion. Its only
dependency cache declaration is the ordinary `setup-python cache: pip` path in
`security-dependencies.yml`.

GitHub also documents code scanning and dependency review as free for public repositories,
so the mandatory CodeQL and dependency-review controls do not require a paid GitHub Advanced
Security license under the observed public-repository condition.

The qualified claim is intentionally narrow:

> **the permanent mandatory Development Engine path requires zero paid spend under the bound
> public-repository + standard-runner conditions.**

It is **not** a claim that the GitHub account can never incur optional charges from unrelated
products, manually enlarged cache limits, larger runners, private repositories, or other
user-selected paid services.

Machine evidence: `engineering/MANDATORY_COST_ZERO_EVIDENCE.json`.

WU02 qualification is executed only while `ENG-08.4-WU02` is active, through the existing
permanent WU01 audit step. No additional mandatory workflow step is added.

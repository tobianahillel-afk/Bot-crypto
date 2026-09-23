# Workflow Security Controls — ENG-04.4

ENG-04.4 is intentionally split into two Agent Work Units because the governance engine correctly rejected a two-dependency work unit.

## WU01 — actionlint syntax/expression gate

WU01 introduces only actionlint v1.7.12:
- source tag: v1.7.12
- audited tag commit: 914e7df21a07ef503a81201c76d2b11c789d3fca
- Linux amd64 release asset: actionlint_1.7.12_linux_amd64.tar.gz
- GitHub-published SHA-256: 8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8
- license: MIT

The binary is downloaded only from the exact release URL and its SHA-256 is verified before extraction.

The workflow runs a runtime-only malformed-workflow positive control, then derives changed workflow files from Git history and runs actionlint only on those files. Unchanged legacy workflows are not silently certified and are not made blockers in this WU; repository-wide legacy remediation belongs to ENG-04.5.

The mandatory path uses only a standard GitHub-hosted runner, contents: read, no external token, no paid API/SaaS/LLM, and no broad ignore configuration.

WU02 will add zizmor as a separate dependency after WU01 is certified.

## WU02 — zizmor offline security gate

WU02 adds only zizmor v1.30.1:

- audited tag commit: 99a054ed9283c90abdd2d5b9fb5101d27dde9783
- Linux x86_64 release asset: zizmor-x86_64-unknown-linux-gnu.tar.gz
- GitHub-published SHA-256: e65324f4430c2717591937edcec90ccbefaf14c174f8ec9415e03ca875b46e1a
- license: MIT

The same Git-diff discovery is reused. actionlint receives changed workflow files; zizmor receives
those workflows plus changed local .github/actions definitions. Zizmor is forced into
--offline --strict-collection --no-config mode and receives no GitHub token.

A dangerous pull_request_target/template-injection fixture is assembled only at runtime and must
be rejected. Real findings are reduced to rule, severity, confidence, file and row metadata;
workflow feature/snippet text is never printed by the wrapper.

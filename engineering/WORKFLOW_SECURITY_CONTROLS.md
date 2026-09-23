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

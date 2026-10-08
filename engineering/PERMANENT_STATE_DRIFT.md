# Permanent External State-Drift Verification

The permanent state contains an **observation snapshot**, not permission to assume GitHub
has remained unchanged.

Every fresh GitHub-backed agent must re-check:
- `main` head;
- `main` protection flag;
- repository ruleset count;
- active business candidate PR state, merged flag, head and base.

Unexpected movement emits `STATE_DRIFT`. The verifier never rewrites state automatically.

## Execution modes

- `--mode snapshot`: deterministic internal binding validation, no network.
- `--mode github`: live GitHub REST verification; used by engineering CI and by agents with
  appropriate GitHub access.

The mandatory path uses only the Python standard library and the free GitHub API/token
already provided to Actions.

Verifier: `scripts/governance/verify_external_git_state.py`.

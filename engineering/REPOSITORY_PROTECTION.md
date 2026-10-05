# Repository Protection — current verified state

Current live observation for **Crypto Quant Bot V3.1-Ops**:

- main SHA: `390d0779f2be257fa8134faf8f02193a760a09c3`;
- GitHub branch resource: `protected=true`;
- one repository ruleset is active: **Protect** (ID `24172517`);
- the ruleset targets only `refs/heads/main`;
- pull requests are required;
- required status checks are enforced;
- non-fast-forward updates are blocked;
- branch deletion is blocked;
- `current_user_can_bypass=never`.

The connected GitHub App still cannot read the classic branch-protection administration
endpoint, but that is not used as proof. Protection is positively verified through the
repository ruleset, which is an accepted mechanism under
`config/governance/repository_protection_policy_v1.json`.

The machine-readable current snapshot is
`engineering/REPOSITORY_PROTECTION_STATUS.json`. The historical ENG-04.6 observation is not
rewritten as historical evidence; this file documents the **current** verified state.

Business-development authority is already ACTIVE through the separately immutable activation
evidence. Lot46 remains LOCKED and runtime/trading permissions remain unchanged.

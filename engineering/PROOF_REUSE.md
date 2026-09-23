# Exact-input Proof Reuse — ENG-03.7

Proof reuse is allowed only when the **current expected proof key** equals a previously issued
PASS proof key.

The key is SHA-256 over canonical JSON containing:

- symbolic tier + subject id;
- SHA-256 and byte length of every relevant input file;
- policy-file digests;
- implementation-file digests;
- deterministic parameters;
- Python implementation/version, platform and machine.

Operational metadata such as source HEAD, creation time and producer run ID is stored outside
the key. This permits safe reuse across unrelated commits **only when the relevant exact inputs
are identical**.

Safety rules:

- candidate proof must first verify its own material/key integrity;
- candidate key must then equal a freshly recomputed expected key;
- only PASS proofs can be reused;
- paths may not escape the repository and symlinks are rejected;
- T0 is too cheap to cache;
- T3/T4, live external Git state, exact-head certification and provenance certification are
  non-reusable;
- no external cache service is required. A future CI layer may store proof JSON as an artifact
  or local cache entry without changing the reuse semantics.

Policy: `config/governance/proof_reuse_policy_v1.json`
Engine: `scripts/governance/proof_reuse.py`

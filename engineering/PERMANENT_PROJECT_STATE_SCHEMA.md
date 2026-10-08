# Permanent Project State Schema V1 — ENG-01.1

The permanent state is intentionally split into independent tracks:

- `business_track`: merged/certified baseline, merged entry gate, candidate and next lock;
- `engineering_track`: Development Engine lifecycle;
- `audit_track`: historical audit lifecycle.

The schema also carries safety, mandatory-cost policy, authority pointers, external Git
observations, unresolved findings, stop conditions and freshness rules.

## Design constraints

- closed objects: unknown top-level/section keys are rejected by the JSON Schema;
- candidate state is never conflated with merged certified state;
- external Git observations are explicit and revalidated on resume;
- findings remain first-class state, not prose-only warnings;
- schema structure is defined here; legal cross-field transitions are ENG-01.3.

Schema: `config/governance/project_state_v1.schema.json`.
Reference fixture: `engineering/fixtures/project_state_v1.example.json`.

The fixture is not yet the canonical state. Canonical migration happens after the track and
state-machine tasks are complete.

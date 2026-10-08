# Certification Promotion — ENG-06.5

ENG-06.5 defines a **pure fail-closed decision**. It does not certify a real business
candidate, mutate a branch/PR, unlock Lot46, or change runtime/trading authority.

A promotion is allowed only from `CERTIFICATION_READY` to `CERTIFIED` when one immutable
candidate identity agrees across:

1. validated lifecycle state and fresh prerequisites;
2. exact-input binding plus exact-head successful CI evidence bundle;
3. the selected T3 requirements and their satisfied deep-assurance verdict;
4. all declared T4 requirements;
5. the canonical provenance envelope;
6. a native GitHub attestation whose subject SHA-256 equals the provenance identity;
7. a self-integral explicit `PASS` certification verdict binding the exact-head,
   assurance, provenance and attestation identities;
8. an empty blocker set.

Any missing, stale, failed, mismatched, malformed, duplicate or unknown evidence denies
promotion.

The `ENG-06.4-ATTESTATION-PROBE` candidate is explicitly forbidden from promotion. A
successful transport probe proves only that native attestation transport works; it is never
business or T4 certification.

The promotion result intentionally contains no fields able to unlock business development,
Lot46, trading, execution, leverage or withdrawals.

Policy: `config/governance/certification_promotion_v1.json`
Validator: `scripts/governance/validate_certification_promotion.py`

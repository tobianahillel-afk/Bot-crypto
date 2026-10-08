# ENG-09.2 — Lot45 Workflow & Review Redundancy

## Verdict

**REDUNDANCY_CONFIRMED — CONSOLIDATION REQUIRED, CANDIDATE STILL BLOCKED**

This is a read-only process analysis bound to PR #66 head `ec2c4ab16f21b23e062b7fca0bb796c8db4a5133`. It does not
authorize Lot45 remediation, merge, Lot46, or business-development unlock.

## Live exact-head snapshot

- PR #66: open, unmerged, mergeable but unstable.
- Candidate head: `ec2c4ab16f21b23e062b7fca0bb796c8db4a5133`.
- 228 commits, 48 changed files, +7689/-587.
- Workflows on this exact head: **49**.
- SUCCESS: **26**.
- FAILURE: **23**.
- Unresolved non-outdated semantic review findings: **2 P1**.

The old frozen-head 49/49 evidence remains stale for the current head.

## Where the workflow noise comes from

| Class | Workflows | Success | Failure |
|---|---:|---:|---:|
| Lot45 direct | 4 | 2 | 2 |
| Global/transversal | 4 | 2 | 2 |
| Historical mutation (Lots26–44) | 18 | 18 | 0 |
| Historical validation (Lots26–44) | 17 | 3 | 14 |
| Historical evidence/post-merge/frozen | 6 | 1 | 5 |
| **Total** | **49** | **26** | **23** |

Therefore:

- **41/49 workflows = 83.67%** historical fan-out unrelated to validating Lot45's current
  business change as a fresh candidate.
- **19/23 failures = 82.61%** are historical fan-out failures.
- The remaining **4 failures are relevant** and must not be hidden:
  1. Lot45 entry gate;
  2. Lot45 frozen evidence;
  3. institutional code quality;
  4. P0.6 final exact-commit assurance.

Removing historical fan-out would improve signal, not make the candidate green: the four
candidate/global failures would still remain.

## Mutation duplication

The current PR head launches **20 mutation workflows**:

- 18 historical Lot26–44 mutation workflows;
- Lot45 mutation assurance;
- P0.6 extended mutation assurance.

This is the clearest reusable-workflow candidate. Future PR validation should select mutation
targets from impact/domain metadata and run one generic mutation capability, while preserving
per-domain target sets, thresholds and evidence requirements as configuration.

## Other duplicated capabilities

Representative workflow inspection shows repeated execution of the same capability families:

- full pytest / regression across institutional quality, the Lot45 entry gate and final assurance;
- typing/quality assurance repeated between institutional/final gates;
- Bandit and `pip-audit` repeated in institutional quality and the Lot45 entry gate;
- architecture, roadmap and traceability checks repeated by institutional quality and entry gate;
- roadmap validation also has its own standalone workflow.

The engine should execute a generic capability once at the appropriate tier and let later
lifecycle gates consume exact-head evidence instead of paying for the same work repeatedly.

## Review transport is not the review obligation

GitHub currently records **28 review submissions**, and all **28**
are from the Codex connector. The PR body explicitly requires a fresh **Codex** exact-head
review before merge progression.

That requirement mixes two different things:

1. **Semantic obligation — mandatory:** an independent exact-head review must leave no
   unresolved substantive P1/P2 findings.
2. **Transport/provider — must not be mandatory:** Codex, another AI reviewer, or a human
   reviewer may produce the review evidence, provided the review contract is satisfied.

The two current P1 findings remain blockers regardless of provider:

- preserve market identity in standalone Order Flow/CVD artifacts;
- bind nested artifact identity to the certified/source input market.

No future mandatory process should depend on paid/quota-sensitive LLM availability.

## Consolidation sequence

### Phase 1 — stop historical PR fan-out

Do not trigger Lots26–44 validation/mutation/post-merge/frozen workflows on an unrelated new
candidate PR head. Keep those workflows/evidence available for their own lifecycle, manual
audit, or historical verification surfaces.

**Guaranteed effect for a Lot45-shaped PR: 49 → 8 top-level workflows**, a reduction of
**41 workflows / 83.67%**. If the candidate code is unchanged, visible failures fall from
23 to the **4 relevant failures**, removing **82.61%** of failure noise.

### Phase 2 — consolidate mutation

Replace lot-specific PR mutation fan-out with one reusable impact-selected mutation control.

After Phase 1, the candidate/global path still contains two mutation controls
(Lot45 mutation + P0.6 extended mutation). The target is one mutation execution selected by
changed domain and risk.

### Phase 3 — de-duplicate global assurance

Factor full regression, typing, security/dependency, architecture/roadmap and anti-flake into
reusable controls. Lifecycle gates should consume exact-head evidence rather than independently
re-running the same capability.

### Phase 4 — make T4 lifecycle-conditional

Frozen evidence/provenance attestation belongs to a stabilized exact-head certification
candidate. It should not execute on every ordinary development edit, and stale frozen evidence
must never certify a different head.

### Phase 5 — provider-agnostic semantic review

Replace “fresh Codex review required” with a provider-neutral review contract:

- review bound to exact candidate head;
- reviewer identity/implementation recorded;
- substantive P1/P2 count must be zero;
- deterministic CI evidence remains separate;
- no paid LLM/provider/token quota is a mandatory dependency.

## Quantitative target

- **Guaranteed first consolidation:** 49 → 8 workflows (**83.67% fewer**).
- **Post-consolidation design target:** **4–6 routine mandatory top-level checks**, with T4
  certification conditional on a stabilized candidate.
- Six checks would be **87.76% fewer** than 49; four would be **91.84% fewer**.

The 4–6 target is a design target for ENG-09.3, not yet certified evidence.

## Routing

This AWU changes no workflows and no Lot45 code. Implementation is routed to ENG-09.3 (or a
dedicated repair AWU created under it). BUSINESS remains PAUSED and Lot46 remains LOCKED.

# Repository Truth Classification

ENG-00 separates **what is true now** from **what was certified historically** and from
human-facing status summaries.

## Classes

- **IMMUTABLE_HISTORICAL_EVIDENCE** — exact commits/artifacts that prove a past certification.
  They are read-only and outrank later summaries for historical facts.
- **CURRENT_OPERATIONAL_STATE** — the machine-readable state used to decide what an agent may
  do now.
- **NORMATIVE_POLICY** — stable rules, architecture and safety contracts. Normative does not
  imply that every described future capability is implemented.
- **CERTIFIED_GATE_STATE** — a certified transition opening a bounded next scope.
- **DERIVED_OR_HUMAN_STATUS_VIEW** — README, status tables and metadata. These may be stale and
  must never determine work authorization.
- **EXTERNAL_GIT_REALITY** — actual refs/PR state observed from GitHub.
- **CANDIDATE_OR_PR_CONTEXT** — unmerged candidate state, never equivalent to merged truth.

The machine-readable inventory is `engineering/REPOSITORY_TRUTH_REGISTRY.json`.

## Conflict rule

When sources disagree, do not choose the newest-looking prose. Apply the authority relevant
to the question:

- historical certification → immutable historical evidence;
- current work authorization → canonical operational state plus current Git reality;
- system rule/architecture → normative policy;
- human overview → derived view only.

A conflict that affects authorization becomes `STATE_DRIFT` until reconciled.

## ENG-00 boundary

ENG-00.1 classifies sources only. It does not rewrite stale documents.
ENG-00.2 performs bounded reconciliation while preserving historical evidence.

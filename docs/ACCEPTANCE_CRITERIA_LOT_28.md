# Acceptance Criteria — Lot 28 Explanation Core & Why-Not-Trade Layer

## Functional

- exactly fourteen versioned explanation statements are produced for the certified Lots 26–27 inputs;
- exactly three current why-not reasons are produced;
- every statement and reason contains at least one registered source evidence reference;
- every evidence artifact checksum and JSON pointer resolves to the stored observed value;
- every rendered text equals its versioned template applied to stored parameters;
- facts, computed features, inferences, assumptions, supporting evidence, contradicting evidence, uncertainty, rules, vetos, non-applicable items and final consequence remain separate;
- no free-text fallback exists for an unsupported input state;
- the reason-set consequence equals the bundle final consequence;
- no order intent is created.

## Deterministic oracle

- statement count: `14`;
- why-not reason count: `3`;
- dominant reason: `WNT_PERMISSIONS_DISABLED`;
- global state explained: `GLOBAL_CONTEXT_MIXED`;
- alignment explained: `MTF_DIVERGENT`;
- coherence explained: `MTF_INCOHERENT`;
- replay: `MATCH`.

## Negative and tamper tests

- unsupported config schema rejected;
- duplicate or incomplete template registry rejected;
- permission escalation rejected;
- instrument or decision-time divergence rejected;
- non-UTC or future-state mismatch rejected;
- unexpected global/alignment state rejected until a new template version is approved;
- missing reason evidence rejected;
- unknown artifact or invalid checksum rejected;
- invalid JSON pointer or observed value rejected;
- altered rendered text rejected;
- altered reason owner/condition rejected;
- unknown field rejected by the closed schema;
- output checksum or audit linkage tamper rejected.

## Forbidden output

The serialized state must contain none of these tokens:

- `BUY`;
- `SELL`;
- `position_size`.

The layer must not produce a forecast, probability claim, strategy selection, risk approval, signal, order or execution permission.

## Quality

- Python 3.11.9 locked environment;
- Ruff and mypy PASS;
- line coverage at least 95%;
- branch coverage at least 90%;
- critical mutation score at least 80%;
- architecture, ownership and traceability PASS;
- Bandit and dependency audit PASS;
- full repository regression and anti-flake PASS;
- no unowned engineering deviation.

## Safety

- `analysis_only=true`;
- all decision, forecast, probability, signal, risk, routing, execution and trade permissions are `false`;
- `approved_size=0`;
- `no_order_intent_created=true`.

## Promotion gate

Lot 29 remains `PLANNED_LOCKED` until Lot 28 is merged and its post-merge audit passes.

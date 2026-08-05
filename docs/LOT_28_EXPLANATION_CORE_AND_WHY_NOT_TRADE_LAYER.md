# Lot 28 — Explanation Core & Why-Not-Trade Layer

Status: `IMPLEMENTATION_IN_PROGRESS`

Owner: `MarketAnalysisDomain`  
Runtime maximal: `LOCAL_OFFLINE_ANALYSIS_ONLY`

## Objective

Transform the validated descriptive states of Lots 26–27 into a deterministic, structured and evidence-backed explanation of the current context and of the reasons no executable action can be produced.

The layer is not a natural-language reasoning engine. Every statement comes from a versioned template, fixed parameters and explicit JSON pointers into immutable input artifacts.

## Inputs

- `data/audit/global_market_context_aggregator_lot27.json`;
- `data/audit/multi_timeframe_alignment_engine_lot26.json`;
- `config/explanations/explanation_core_why_not_trade_v1.json`.

The v1 template contract is intentionally strict and expects:

- identical instrument and decision time in both inputs;
- validated `GLOBAL_CONTEXT_MIXED` global context;
- explicit `MTF_DIVERGENT` alignment;
- `MTF_INCOHERENT` coherence state;
- every decision, signal, routing and execution permission disabled.

A changed source state requires a new template/config version. The engine never improvises a replacement narrative.

## Structured output

`ExplanationBundleV1` separates:

- `facts_observed`;
- `features_computed`;
- `inferences`;
- `assumptions`;
- `supporting_evidence`;
- `contradicting_evidence`;
- `uncertainty`;
- `rules_triggered`;
- `vetos_triggered`;
- `non_applicable`;
- `final_consequence`;
- `why_not_trade`.

Every `ExplanationStatementV1` contains:

- stable statement ID;
- section;
- reason code;
- template ID;
- rendered text;
- exact template parameters;
- one or more `EvidenceReferenceV1` entries.

Each evidence reference contains an artifact path, artifact checksum, JSON pointer and observed scalar value.

## Why-not reason contract

`WhyNotTradeReasonSetV1` contains exactly three current reasons:

1. `WNT_CONTEXT_MIXED` — global context is not unambiguous;
2. `WNT_MTF_DIVERGENCE` — multi-timeframe divergence remains unresolved;
3. `WNT_PERMISSIONS_DISABLED` — decision, signal, routing and execution capabilities remain disabled.

Each reason records:

- owner;
- unsatisfied condition;
- observed value;
- required value;
- expiry (`null` when no automatic expiry exists);
- condition for reconsideration;
- source evidence;
- proof that no order intent was created.

`WNT_PERMISSIONS_DISABLED` is dominant because the layer cannot authorize execution regardless of descriptive context quality.

## Deterministic golden explanation

The current validated inputs produce fourteen statements and three why-not reasons. Key outputs include:

```text
Global context is GLOBAL_CONTEXT_MIXED with weighted coverage 1.000000.
Multi-timeframe alignment is MTF_DIVERGENT; coherence is MTF_INCOHERENT.
No calibrated confidence interval is available for the heterogeneous descriptive sources.
Executable promotion is blocked because decision, signal, routing and execution permissions are disabled.
No executable action is produced; a future validated promotion gate would be required before reconsideration.
```

## Validation

The validator:

1. confirms the closed schema;
2. validates the template and reason registries;
3. loads only registered input artifacts;
4. recomputes every artifact checksum;
5. resolves every JSON pointer;
6. compares every observed value;
7. rerenders every template from stored parameters;
8. compares reason metadata with the versioned registry;
9. verifies the final consequence and reason-set consequence are identical;
10. verifies state/audit checksums and deterministic replay;
11. rejects forbidden direction or sizing tokens.

## Failure behavior

- missing or incompatible input schema → fail closed;
- instrument or decision-time mismatch → fail closed;
- future or divergent temporal input → fail closed;
- invalid safety flag → fail closed;
- unsupported source state for this template version → fail closed;
- reason code without evidence → reject output;
- missing or invalid JSON pointer → reject output;
- text different from the rendered template → reject output;
- unknown field in a closed object → reject output;
- replay mismatch → block promotion.

## Non-goals

- no forecast or calibrated probability;
- no directional label or position sizing;
- no strategy selection;
- no risk approval;
- no signal or order construction;
- no paper, sandbox or live execution;
- no generative free text;
- no inferred causality beyond the explicit source state and configured rules.

## Safety invariants

```text
analysis_only=true
used_for_decision=false
forecast_generation_allowed=false
probability_claims_allowed=false
signal_generation_allowed=false
risk_approval_allowed=false
order_routing_allowed=false
execution_allowed=false
trade_allowed=false
approved_size=0
no_order_intent_created=true
```

## Definition of done

- immutable contracts and closed schema;
- deterministic golden statements;
- source evidence for every statement and reason;
- exact template rerender validation;
- replay and tamper detection;
- anti-future-state and safety negative tests;
- line coverage at least 95% and branch coverage at least 90%;
- mutation score at least 80% on explanation and validation logic;
- Ruff, mypy, architecture, traceability, security, full regression and anti-flake PASS;
- final report and post-merge audit before Lot 29.

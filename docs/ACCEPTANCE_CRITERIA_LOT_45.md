# Acceptance Criteria — Lot 45

Lot 45 is accepted only when every criterion below is PASS on the exact certified source and final PR head.

## Functional contracts

- Produces `OrderFlowDeltaCVDEngineStateV1`, `OrderFlowDeltaCVDEngineAuditV1`, `OrderFlowStateV1` and `CVDSeriesV1`.
- Aggregates BUY, SELL and UNKNOWN classified trade volume in deterministic event-time windows.
- Preserves count and volume conservation exactly.
- Computes `signed_delta = buy_volume - sell_volume`.
- UNKNOWN volume contributes zero signed delta and zero CVD contribution.
- Computes signed imbalance without dropping UNKNOWN volume from the denominator.
- Computes deterministic delta impulse from current and immediately previous window only.
- Computes CVD in event-time order with an explicit versioned session reset policy.
- Emits classification coverage and confidence-weighted coverage as descriptive diagnostics only.

## Temporal and replay guarantees

- No future event, receive time or future state can influence an earlier window.
- Input order does not affect output: shuffled/out-of-order delivery must replay byte-identically after deterministic event-time sorting.
- Window boundaries are deterministic from event timestamps.
- Session transitions reset CVD exactly according to `lot45-utc-day-session-v1`.
- Runtime timestamps and every published Lot45 timestamp schema accept only real Gregorian calendar dates in canonical microsecond UTC `Z` text; impossible dates and invalid leap days fail closed.
- Canonical Gregorian timestamps before `1970-01-01T00:00:00.000000Z` remain valid inputs; signed Unix-epoch offsets must not narrow the published timestamp domain.
- Every causal timestamp (`event_time`, `receive_time`, `generated_at`) is validated through the canonical Lot45 timestamp parser before causal ordering is evaluated.
- Two complete builds from the same source/config/input must produce identical state, audit, order-flow and CVD payloads/checksums.

## Upstream and executable integrity

- Entry gate merge is exactly bound to the certified Lot45 gate.
- Lot44 frozen state, audit, confidence, config and post-merge checksums are revalidated before calculation.
- Every certified Lot45 Python launch is mediated by the trusted shell wrapper `scripts/lot45_trusted_prelaunch.sh` before Python startup.
- The trusted wrapper resolves the exact claimed `code_commit` and proves bound committed, working and staged paths are unchanged before launch.
- The trusted wrapper inspects `src/` with ignored and untracked paths included; any unexpected object fails closed before Python starts.
- Self-deleting `sitecustomize.py`, `usercustomize.py`, sourceless `.pyc`/`.pyo`, native `.so`/`.pyd`, symlinks, package startup hooks and other ignored/untracked executable artifacts cannot be launched as part of a certified run.
- The in-process executable Python inventory remains a secondary defense and still rejects ignored, untracked and post-freeze staged `*.py` sources.
- Certified launches use an explicit repository `src` path with safe-path enabled, user-site disabled and bytecode writes disabled.
- Duplicate trade ids fail closed.
- Mixed source/venue/instrument/market identities fail closed.
- Stale or causally impossible upstream evidence fails closed.

## Contracts and persistence

- Published JSON schemas are closed objects and require checksum fields.
- Published timestamp schemas preserve exact canonical UTC text while also enforcing valid calendar dates.
- Runtime safety is exact and fail-closed.
- Decimal zero serializes canonically as `"0"`.
- All Lot45 Decimal-derived arithmetic and invariant validation execute in a complete frozen context: precision, `ROUND_HALF_EVEN`, `Emin`, `Emax`, clamp and trap policy are explicit and independent of the caller's ambient Decimal context.
- Final artifacts are persisted only with atomic JSON writes.
- State/audit/order-flow/CVD checksums are canonical and replay-verifiable.

## Safety

- `analysis_only=true`
- `approved_size=0`
- `execution_allowed=false`
- `external_connectivity_allowed=false`
- `market_event_publication_allowed=false`
- `network_ingestion_allowed=false`
- `order_routing_allowed=false`
- `participant_behavior_inference_explicitly_labeled=true`
- `raw_data_mutation_allowed=false`
- `real_credentials_allowed=false`
- `risk_approval_allowed=false`
- `scenario_score_is_signal=false`
- `signal_generation_allowed=false`
- `trade_allowed=false`
- `used_for_decision=false`

## Quality gates

- Dedicated Lot45 line coverage >= 95%.
- Dedicated Lot45 branch coverage >= 90%.
- Dedicated mutation score >= 80%.
- Adversarial certification proves pre-launch rejection of a self-deleting startup source and a valid sourceless startup `.pyc` before Python is started.
- Adversarial tests prove ignored/untracked executable Python source rejection and calendar-invalid timestamp rejection.
- Adversarial tests prove hostile ambient Decimal traps/exponent limits cannot change valid Lot45 calculations or model reconstruction.
- Adversarial tests prove canonical pre-1970 Gregorian timestamps retain deterministic event-time tumbling-window semantics.
- Full repository tests PASS.
- Architecture/roadmap/traceability/engineering/security checks PASS.
- Targeted Lot45 tests repeat at least three times without flake.
- Final exact-head CI matrix contains no failure or in-progress run.
- Final Codex review has no unresolved substantive finding.

## Evidence and promotion

- Dedicated validation artifact/digest is captured.
- Dedicated mutation artifact/digest is captured.
- Generated state/audit/order-flow/CVD and coverage/mutation summaries are frozen from successful artifacts.
- Frozen validator and frozen attestation replay byte-identically.
- PR is merged only after frozen exact-head certification.
- Independent post-merge audit emits exactly `GO_LOT45_POST_MERGE` before Lot 46 may start.

Until that final post-merge verdict exists, Lot 46 remains `PLANNED_LOCKED` and physically absent.
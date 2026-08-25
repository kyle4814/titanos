# Foundation Switch — §XVI Module Mapping

The governing directive lists 16 MAGL modules. Reconnaissance found 5 map
directly onto code that already existed before this session, 8 were
genuinely new and are now built (4 in the original session, 4 more added
in a later cycle once real evidence existed to justify them), and 3
remain honestly unbuilt — named here rather than glossed over, per this
build series' standing practice (see `magl/BUILD_REPORT.md`'s and
`rpa/BUILD_REPORT.md`'s equivalent sections for precedent). Counts
verified by directly recounting each table's rows, not carried forward
from an earlier draft.

## Built this session (genuinely new — no existing analog)

| Module | File | Tests |
|---|---|---|
| `MAGL_006_EPISTEMIC_CLUTCH` (= the mode-switching mechanism the directive separately calls "the flow switch") | `foundation/flow_switch.py` | 45 |
| `MAGL_CT141_003_SIGNAL_COLLAPSE_PROTOCOL` (the SIGNAL_COLLAPSE mode and its exclusive path to RECOVERY, same file) | `foundation/flow_switch.py` | (included above) |
| `MAGL_FOUNDATION_001_SWITCH_HARDENER` | `foundation/switch_hardener.py` | 16 |
| `MAGL_FOUNDATION_004_REALITY_YIELD_LEDGER` | `foundation/reality_yield_ledger.py` | 34 |
| `MAGL_005_999_STATE_SPACE_MAPPER` | `foundation/state_space_mapper.py` | 23 |
| `MAGL_CT141_004_LOW_REGRET_ENGINE` | `foundation/low_regret_engine.py` | 16 |
| `MAGL_FOUNDATION_003_REGRESSION_ENGINE` | `foundation/regression_engine.py` | 13 |
| `MAGL_CT141_002_DEFUSAL_ROUTER` | `foundation/defusal_router.py` | 24 |

**147 new tests, 147 passing** (flow_switch/switch_hardener/reality_yield_
ledger/state_space_mapper/low_regret_engine/regression_engine session);
**+24 more, 171 total**, added a later session for `defusal_router.py` —
the nine-step CT_141 response checklist derived from
`TITANOS_GO_CYCLE_DOCTRINE.md` §IV, `TITANOS_REALITY_YIELD_PROFIT_
ARCHITECTURE.md` §X and `TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md` §8
(merged and deduplicated — see that file's own docstring for why 9, not
the "11-step" figure this repo's own source text for could not be
re-derived). A pure router, reuses `flow_switch.PanicSample`/
`detect_panic`, never executes a step or touches `FlowSwitchStore`.

## Maps directly onto pre-existing code — building new code would duplicate it

| Module | Maps to | Notes |
|---|---|---|
| `MAGL_001_CONTEXT_INGESTION` | `kpm/source-vault/registry.py` | content-addressed, immutable, append-only source archive — exact match to "raw event capture without rewriting history" |
| `MAGL_002_EPISTEMIC_CLASSIFIER` | `kpm/schemas/epistemic_types.py` | 15-value classification, forbidden transitions, evidence-gated upgrades — exact match |
| `MAGL_003_BLACK_ICE_REFLECTOR` | `firewall/gate.py` + `kpm/schemas/epistemic_types.py` | the claim→assumption→counter-claim→evidence→risk→routing pipeline is `evaluate()`'s shape; the directive's output vocabulary maps cleanly: `VERIFIED_FACT`→same, `SUPPORTED_INTERPRETATION`→`EVIDENCE_SUPPORTED_MODEL`, `TESTABLE_HYPOTHESIS`→`SCIENTIFIC_CLAIM_REQUIRING_EVIDENCE`, `SPECULATIVE_MODEL`→`SPECULATIVE_HYPOTHESIS`, `SYMBOLIC_READING`→`SYMBOLIC_DOCTRINE`, `RAW_OBSERVATION`→`PERSONAL_EXPERIENCE` or `EVIDENCE`, `UNKNOWN`→same |
| `MAGL_008_TRUST_VERIFICATION_INTERFACE` | `taal/gate/root_gate.py` | the literal 12-question boundary-reasoning gate, built last session |
| `MAGL_CT141_001_ZERO_TRUST_GATE` | `taal/gate/root_gate.py` | same file — "zero trust gate" and "trust verification interface" are the same mechanism under two names in the directive |

## Genuinely unbuilt — named, not silently skipped

| Module | Why deferred |
|---|---|
| `MAGL_004_ORACLE_SCENARIO_ENGINE` | Multi-future generation with A/B/C/D option branching has no analog anywhere in this repo. `rpa/schema/pilot_simulation.py` is the closest relative (baseline/risk/failure-scenario structure) but is single-scenario, not multi-branch. Real, non-trivial new work. Note: `foundation/state_space_mapper.py` (built) is explicitly NOT this module — it validates caller-declared coordinates, it does not generate or predict anything. |
| `MAGL_007_CONTINUITY_SEED` | Partially covered *operationally*, not as cosmic-library code — the assistant's own memory system (`~/.claude/projects/.../memory/`) already implements "next session should resume without reloading everything," which is this module's literal purpose. Whether that should ALSO become a versioned artifact inside this repository is an open question, not decided here. |
| `MAGL_FOUNDATION_002_PATHWAY_LEDGER` | Partial: `switch_hardener.classify_hardened_switch()` can label something `LEDGER_ENTRY`, and `reality_yield_ledger.py` records its yield assessment — but no dedicated store exists for querying "every lesson currently classified LEDGER_ENTRY" as its own collection. |

## Why this split, not a 16-module build

The directive's own closing rule (§XVII): "DO NOT BUILD THE BIGGEST
SYSTEM. BUILD THE SMALLEST FOUNDATION THAT CAN SAFELY GROW." Building all
16 as literal new modules would have meant either (a) genuine duplication
of `kpm`/`taal`/`firewall` work already done, which every prior session
in this series has treated as a defect to catch, not a feature to repeat,
or (b) padding out the 8 genuinely-new modules with shallow
implementations to hit a count, which this session's own standing
discipline (see `docs/LIMITATIONS.md`, every `BUILD_REPORT.md`'s honest
gaps sections) exists specifically to refuse.

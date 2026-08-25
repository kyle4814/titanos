# Foundation Switch — §XVI Module Mapping

The governing directive lists 16 MAGL modules. Reconnaissance found 6 map
directly onto code that already existed before this session, 3 were
genuinely new and are now built, and 7 remain honestly unbuilt — named
here rather than glossed over, per this build series' standing practice
(see `magl/BUILD_REPORT.md`'s and `rpa/BUILD_REPORT.md`'s equivalent
sections for precedent).

## Built this session (genuinely new — no existing analog)

| Module | File | Tests |
|---|---|---|
| `MAGL_006_EPISTEMIC_CLUTCH` (= the mode-switching mechanism the directive separately calls "the flow switch") | `foundation/flow_switch.py` | 45 |
| `MAGL_CT141_003_SIGNAL_COLLAPSE_PROTOCOL` (the SIGNAL_COLLAPSE mode and its exclusive path to RECOVERY, same file) | `foundation/flow_switch.py` | (included above) |
| `MAGL_FOUNDATION_001_SWITCH_HARDENER` | `foundation/switch_hardener.py` | 16 |
| `MAGL_FOUNDATION_004_REALITY_YIELD_LEDGER` | `foundation/reality_yield_ledger.py` | 34 |

**95 new tests, 95 passing.**

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
| `MAGL_004_ORACLE_SCENARIO_ENGINE` | Multi-future generation with A/B/C/D option branching has no analog anywhere in this repo. `rpa/schema/pilot_simulation.py` is the closest relative (baseline/risk/failure-scenario structure) but is single-scenario, not multi-branch. Real, non-trivial new work. |
| `MAGL_005_999_STATE_SPACE_MAPPER` | No existing multi-dimensional decision-coordinate model. |
| `MAGL_007_CONTINUITY_SEED` | Partially covered *operationally*, not as cosmic-library code — the assistant's own memory system (`~/.claude/projects/.../memory/`) already implements "next session should resume without reloading everything," which is this module's literal purpose. Whether that should ALSO become a versioned artifact inside this repository is an open question, not decided here. |
| `MAGL_CT141_002_DEFUSAL_ROUTER` | Partial: `flow_switch.py`'s mode transitions cover the tempo-change half. The specific 11-step CT_141 response checklist (reduce velocity → preserve raw input → freeze belief → ... → log the event → resume only on exit condition) is not implemented as its own routed sequence. |
| `MAGL_CT141_004_LOW_REGRET_ENGINE` | Selecting a "lowest-regret action" requires an options/regret model that doesn't exist. Real, non-trivial new work — this is closer to a decision-theory component than a schema/validator. |
| `MAGL_FOUNDATION_002_PATHWAY_LEDGER` | Partial: `switch_hardener.classify_hardened_switch()` can label something `LEDGER_ENTRY`, and `reality_yield_ledger.py` records its yield assessment — but no dedicated store exists for querying "every lesson currently classified LEDGER_ENTRY" as its own collection. |
| `MAGL_FOUNDATION_003_REGRESSION_ENGINE` | "If contradicted, downgrade, quarantine, or deprecate" (§XIV step 14) has no automated mechanism yet — `kpm/contradictions/registry.py` records contradictions but nothing currently re-tests a hardened switch against new evidence and acts on the result automatically. |

## Why this split, not a 16-module build

The directive's own closing rule (§XVII): "DO NOT BUILD THE BIGGEST
SYSTEM. BUILD THE SMALLEST FOUNDATION THAT CAN SAFELY GROW." Building all
16 as literal new modules would have meant either (a) genuine duplication
of `kpm`/`taal`/`firewall` work already done, which every prior session
in this series has treated as a defect to catch, not a feature to repeat,
or (b) padding out the 7 genuinely-new modules with shallow
implementations to hit a count, which this session's own standing
discipline (see `docs/LIMITATIONS.md`, every `BUILD_REPORT.md`'s honest
gaps sections) exists specifically to refuse.

# RPA-Ω — Build Report

Built 2026-08-25 at `/home/tech2/cosmic-library/rpa/`. 4 parallel Sonnet
agents for the 8 required schemas + the human jurisdiction gate; the
example MAGL, fixtures, and end-to-end wiring done directly.

## Reconnaissance summary

Checked for the "Operator" concept named in the prior MAGL directive
(bounded execution environment) — confirmed it was never actually built,
only described in prose. `kpm/simulations/` is an empty placeholder. No
pilot/measurement/rollback/value-flow/bottleneck schema existed anywhere
in the repo. Unlike the last two sessions, this directive's 8 schemas were
genuinely new — nothing to avoid duplicating on the schema side. What WAS
reused: `magl/schema/magl_schema.py` + `validate_magl.py` (house pattern),
`kpm/promotion/state_machine.py` (the human jurisdiction gate is a thin
wrapper around it, not a new state machine), `kpm/schemas/epistemic_types.py`
(`ALL_CLASSIFICATIONS`, imported everywhere a confidence tag was needed).

## Files created

| Component | Files | Tests |
|---|---|---|
| Legacy System Map | `rpa/schema/legacy_system_map.py`, `rpa/validators/validate_legacy_system_map.py` | 42 |
| Institutional Bottleneck | `rpa/schema/institutional_bottleneck.py`, `rpa/validators/validate_bottleneck.py` | 19 |
| Value Flow | `rpa/schema/value_flow.py`, `rpa/validators/validate_value_flow.py` | 21 |
| Automation Candidate | `rpa/schema/automation_candidate.py`, `rpa/validators/validate_automation_candidate.py` | 29 |
| Human Jurisdiction Gate | `rpa/gates/human_jurisdiction.py` | 11 |
| Pilot Simulation | `rpa/schema/pilot_simulation.py`, `rpa/validators/validate_pilot_simulation.py` | 20 |
| Before/After Measurement | `rpa/schema/before_after_measurement.py`, `rpa/validators/validate_before_after_measurement.py` | 15 |
| Rollback Contract | `rpa/schema/rollback_contract.py`, `rpa/validators/validate_rollback_contract.py` | 16 |
| Fixtures (8 files) + example MAGL | `rpa/fixtures/*.yaml` | — |
| End-to-end demonstration | `rpa/tests/test_end_to_end.py` | 12 |

**No pre-existing file was modified.** Additive only.

## Files modified

None.

## Tests added / passed / failed

**205 new tests, 205 passing, 0 failing.** Full-repo regression in this
same pass: **488 tests total across the whole repository, 488 passing, 0
failing** — every pre-existing suite re-verified, not assumed.

## Demonstrated: the full §XV loop, for real

LEGACY ARCHITECTURE → MAP → BOTTLENECK → CANDIDATE MAGL → SIMULATION →
HUMAN AUTHORIZATION → PILOT → MEASURE → LEARN, using one coherent fictional
scenario (a legacy invoicing workflow with a key-person dependency) threaded
through all 8 schemas plus the pre-existing MAGL and promotion machinery:

1. `legacy_map.yaml` — 4 nodes, 3 edges, 1 boundary, 1 jurisdiction claim,
   flags the invoice clerk and the legacy system itself as single points
   of failure. VALID.
2. `bottleneck.yaml` — KEY_PERSON_DEPENDENCY finding referencing the map,
   EVIDENCE_SUPPORTED_MODEL (cites the documented 3-week stall), next step
   is an interview, not a fix. VALID.
3. `automation_candidate.yaml` — SMALL_BOUNDED_AUTOMATION with jurisdiction
   scoped to read+notify only, explicitly prohibits approving or modifying
   invoices. VALID.
4. `candidate_as_magl.yaml` — the SAME candidate, compiled into a real
   `magl:` document and validated against `magl/validators/validate_magl.py`
   (built last session) — proving a legacy-upgrade candidate isn't a
   parallel format, it's a real MAGL. VALID, and its jurisdiction fields
   are byte-identical to the candidate's.
5. `pilot_simulation.yaml` — status `APPROVED_FOR_PILOT`, which triggered
   the validator's extra completeness check (non-empty failure scenarios
   each with a detection method, both rollback and measurement refs
   present). VALID.
6. `rollback_contract.yaml` + `before_after_measurement.yaml` — both
   referenced by the pilot simulation, both independently VALID.
7. **Human authorization, run against the real promotion state machine**:
   `rpa/tests/test_end_to_end.py::TestHumanAuthorizationGate` advances the
   candidate MAGL through RAW→DISTILLED→PROVISIONAL→TESTED, then
   `authorize_pilot()` takes it TESTED→QUARANTINED→HUMAN_REVIEW (not yet
   authorized — `confirm_pilot_authorized()` returns False here, asserted
   explicitly), then a separate `store.promote(..., "STABLE", ...)` call
   completes authorization — and a second test proves the same path with
   `reviewed_by == created_by` raises `SelfPromotionForbidden` instead of
   silently succeeding.
8. **Measure → Learn dependency, proven both ways**: appending a
   `conclusion` field to the measurement contract while `after_value`
   fields are still empty is INVALID (LEARN cannot skip MEASURE); the same
   fixture with `after_value`s filled in and the conclusion added is VALID.

## A real bug found while building the demonstration, not hypothetically

The end-to-end test's first version appended `conclusion: "it worked"` at
column 0 to test the pre-measurement rejection rule — but that puts
`conclusion` as a sibling top-level YAML key, not nested under
`before_after_measurement:`, so the validator correctly ignored it as
out-of-scope and returned VALID. The test failure looked at first glance
like a validator bug; it wasn't — running it and reading the actual
result caught a bug in the TEST'S YAML construction, not the schema.
Fixed by matching the fixture's real indentation. Consistent with this
repo's standing lesson (F-005 in `failures/FAILURE_ARCHIVE.md`): a
confidently-wrong finding is worth verifying before trusting, including
your own.

## Known limitations

- Cross-file referential integrity is now enforced by
  `rpa/composition/checker.py::check_chain_integrity()` (mirroring
  `magl/composition/engine.py`), added across three later cycles: the
  original bottleneck/candidate/pilot chain, `measurement_pilot_ref`
  (commit `d8afa32`), and `rollback_candidate_ref` (commit `3741094`).
  Every `_ref` field in the pilot/authorization critical path resolves
  or fails FATAL at the composition boundary. Each schema's own
  single-document validator still deliberately does not resolve these
  refs itself — same "pure function over one document's text" reasoning
  as originally documented, unchanged. Remaining unchecked: `value_flow`
  schema's `system_map_ref` (economic side-channel, off the
  pilot/authorization critical path, not yet picked up).
- `rpa/gates/human_jurisdiction.py`'s `authorize_pilot()` found and worked
  around a real detail in `kpm/promotion/state_machine.py`: there is no
  direct `TESTED -> HUMAN_REVIEW` edge, only the two-hop
  `TESTED -> QUARANTINED -> HUMAN_REVIEW` path. Documented at length in
  the gate's own module docstring rather than silently assumed.
- The zero-extraction `value_flow` schema's `reviewable: false` severity is
  WARNING, not fatal — an honest "this extraction cannot be audited"
  declaration is treated as more valuable than an incentive to omit the
  field entirely, per the agent's documented reasoning. Whether that's the
  right policy for a real financial audit is a human decision, not a
  structural one this validator can make.
- No actual notification/execution capability exists — the entire
  `candidate_as_magl.yaml` example is `lifecycle.status: RAW`. Nothing in
  this codebase can run it. That's correct for this session's scope, not
  an oversight.

## Unresolved contradictions

None found.

## Security gaps

Same standing gaps as the last two sessions' reports (single-reviewer
promotion authority for the final STABLE step, unauthenticated
`reviewed_by`, no cryptographic signature verification) — the human
jurisdiction gate built this session inherits these from
`kpm/promotion/state_machine.py` rather than introducing new ones.

## Human decisions required

1. Whether cross-file referential integrity (map → bottleneck → candidate
   → pilot → rollback/measurement) should be built as a composition-layer
   tool, matching `magl/composition/engine.py` — flagged, not decided.
2. Whether `reviewable: false` in a `value_flow` extraction should be
   treated as fatal in some deployment contexts (e.g. actual financial
   audit) rather than always a warning — a policy decision, not a
   structural one.
3. All standing decisions from prior sessions remain open and untouched:
   F-007 (titan repo git history), the 3,058-file legacy corpus review
   question, four-eyes review for promotion release.

## Next smallest work cell

~~Build a cross-file composition checker for the map→bottleneck→
candidate→pilot chain~~ — **done, built same session as originally
named, this entry just went stale**: `rpa/composition/checker.py`
(`FRONTIER-REFCHECK`, `PARETO_FRONTIER.md` archive, commit `9a63205`,
extended `d8afa32`/`3741094`/`b5cad9a`). Verified present and current
2026-08-26 — confirmed via `ls rpa/composition/` rather than assumed
from this file's own prior text, which is exactly why this correction
was needed: a stale "still to do" note describing already-closed work
is itself a real finding, not just housekeeping.

No new gap identified against this subsystem specifically as of
2026-08-26.

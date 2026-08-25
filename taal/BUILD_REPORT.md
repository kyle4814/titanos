# TAAL-Ω — Build Report

Built 2026-08-25 at `/home/tech2/cosmic-library/taal/`. 4 parallel Sonnet
agents; the session hit its usage limit partway through and all four were
resumed from saved progress rather than restarted — noted here because
it's the first time that's happened in this build series, and every agent
picked up cleanly from where it stopped.

## The core design constraint, honoured structurally

Kyle's framing before the directive: keep the symbolic/"demonic"
archetype language as a memory aid only, never let it become technical
evidence. `taal/schema/threat_archetype.py` enforces this as a schema
rule, not a convention: `symbolic_layer.metaphor_status` must be the
literal string `"SYMBOLIC_ONLY"`, and the validator carries an explicit
test proving two documents differing ONLY in symbolic_layer content (one
mundane, one maximally mythic) produce byte-identical technical findings
— the same proof pattern as `schema/tests/test_meta_attack.py`'s
persuasion-has-zero-effect tests.

## Files created

| Component | Files | Tests |
|---|---|---|
| Threat Archetype schema + 12-record library | `taal/schema/threat_archetype.py`, `taal/validators/validate_threat_archetype.py`, `taal/archetypes/library.yaml` | 32 + 8 |
| Permission Request + Normalized Security Event | `taal/schema/permission_request.py`, `taal/schema/normalized_security_event.py`, validators | 28 + 28 |
| Verdict schema + Root Gate engine | `taal/schema/verdict.py`, `taal/validators/validate_verdict.py`, `taal/gate/root_gate.py` | 31 + 37 |
| Integrator + Quarantine mapping + Dissent test | `taal/integrator/integrator.py`, `taal/gate/quarantine_mapping.py` | 10 + 5 + 5 |
| End-to-end demonstration | `taal/tests/test_end_to_end.py` | 4 |

**No pre-existing file was modified** by the TAAL-Ω build itself (the two
gap-closure fixes to `magl/registry/catalogue.py` and the new
`rpa/composition/checker.py` were a separate, earlier piece of this
session's work, already committed).

## Tests added / passed / failed

**184 new tests** in the four parallel builds + **4 end-to-end tests** =
**188 new, 188 passing, 0 failing.** Full-repo regression in this same
pass: **691 tests total across the whole repository, 691 passing, 0
failing.**

## Demonstrated: the four required examples, for real

1. **BENIGN** — a routine scheduled report-read request, verified
   identity, evidenced authority, necessary scope, reversible. The
   integrator proposes zero threat candidates; the root gate returns
   `AUTHORIZED`. Proves the gate can say yes, not just refuse everything.
2. **SUSPICIOUS** — an unrecognised account requesting credential access
   at an unusual hour with a logged prior unauthorized-access finding.
   The integrator proposes real threat_class candidates from its keyword
   matcher; the root gate refuses to authorize (`REFUSED`/`QUARANTINED`/
   `REQUIRES_HUMAN_REVIEW` — the test asserts it's one of these and
   explicitly never `AUTHORIZED`/`AUTHORIZED_WITH_CONSTRAINTS`); the event
   is then quarantined through the **real** `firewall.quarantine.
   QuarantineStore`, not a stand-in.
3. **AMBIGUOUS** — verified identity, evidenced authority, but unknown
   request provenance and no prior history. Root gate returns
   `REQUIRES_HUMAN_REVIEW` — proven distinct from both `REFUSED` (unknown
   isn't guilt) and `AUTHORIZED`/`AUTHORIZED_WITH_CONSTRAINTS` (unknown is
   never silently promoted).
4. **FALSE-POSITIVE RECOVERY** — a new vendor integration is quarantined,
   then reviewed and confirmed legitimate (`taal_mark_reviewed`, mapping
   to the real store's `QUARANTINED -> VERIFIED`), then recovered
   (`taal_mark_recovered`, mapping to `VERIFIED -> AUTHORIZED`). The
   original evidence string is asserted byte-identical at every stage —
   nothing was summarized, reworded, or discarded across the cycle — and
   the full `["QUARANTINED", "VERIFIED", "AUTHORIZED"]` transition history
   is checked directly rather than trusted from the final state label.

## Real findings from this build, not hypothetical

1. **The root gate's core invariant held on first real integration**:
   `evaluate_request()` never returned `AUTHORIZED`/
   `AUTHORIZED_WITH_CONSTRAINTS` for the suspicious or ambiguous inputs,
   and the quarantine-mapping agent's four documented state
   correspondences (REVIEWED/RECOVERED/CONFIRMED_POLICY_VIOLATION/
   CONTAINED) all held against the real `firewall.quarantine.TRANSITIONS`
   table on the first attempt — no mapping had to be corrected.
2. **A genuine, documented limitation in the integrator's keyword
   matcher**: it has no negation-awareness. A `raw_facts` entry phrased
   as "no privilege escalation attempted" still matches the substring
   `"privilege escalat"` and produces a candidate. Building the
   dissent-protection test required rephrasing away from negated trigger
   words rather than weakening the assertion — the matcher's own
   docstring calls this out as "deliberately coarse," and this build
   verified that's not just a disclaimer, it's a reproducible behaviour.
   **This is the load-bearing reason `propose_archetype_candidates()`
   returns candidates, never verdicts** — a human or the root gate must
   still evaluate them, exactly as designed, but it means the integrator
   alone is not safe to wire to any automated action.
3. **The end-to-end test's first suspicious fixture produced zero
   candidates** — my own phrasing ("no prior authority grant on file")
   didn't trip any keyword rule. Fixed by rephrasing to a factual
   observation containing an actual trigger phrase ("access log shows
   unauthorized access attempt recorded"), not by loosening the test.
   Same discipline as the RPA session's YAML-indentation bug: a failing
   integration test was evidence about the fixture, checked before being
   assumed to be evidence about the code.

## Known limitations

- The keyword matcher (finding #2 above) is coarse by design and
  documented as such, but it means `propose_archetype_candidates()`
  should never be the sole gate for anything consequential — it is
  explicitly a candidate proposer, and this session's tests prove that
  boundary is real, not just claimed.
- `root_gate.py`'s rules for authority (no claim vs. unevidenced claim)
  and contradictory evidence were the two most consequential judgment
  calls in this build and are genuinely debatable — documented at length
  in the module's own docstring rather than treated as obviously correct.
- No cross-file wiring exists yet between `taal/schema/permission_request.py`
  (the real, validated schema) and `root_gate.py`'s `GateInput` (its own
  minimal input contract) — both agents deliberately built against their
  own shapes rather than importing each other's, matching this codebase's
  standing "pure function over one document" discipline. A mapping
  function from a validated `permission_request` document to a
  `GateInput` does not exist yet.
- Same standing security gaps as every prior session's report
  (single-reviewer release authority, unauthenticated `reviewed_by`, no
  cryptographic signature verification) — inherited via
  `firewall.quarantine.QuarantineStore`, not new to this build.

## Unresolved contradictions

None found.

## Human decisions required

1. Whether `root_gate.py`'s two most consequential judgment calls
   (unevidenced-authority-claim → REQUIRES_HUMAN_REVIEW rather than
   REFUSED; any contradictory evidence → REQUIRES_HUMAN_REVIEW rather than
   AUTHORIZED_WITH_CONSTRAINTS) match the actual risk tolerance wanted —
   these are policy decisions dressed as code, named explicitly so they
   can be reviewed as such.
2. Whether to build the `permission_request` → `GateInput` mapping
   function, and where it should live (a new module, or absorbed into one
   of the two existing ones) — flagged, not decided.
3. Whether the keyword matcher needs negation-awareness before being
   trusted for anything beyond candidate proposal, or whether "candidate
   proposal only, human/gate decides" is a sufficient permanent boundary
   — a policy question, not purely technical.
4. All standing decisions from prior sessions remain open: F-007 (titan
   repo git history), the 3,058-file legacy corpus review question,
   four-eyes review for release across every promotion/quarantine store
   in this repository.

## Next smallest work cell

~~Build the `permission_request` → `GateInput` adapter~~ — **done,
2026-08-25**: `taal/gate/permission_request_adapter.py::
permission_request_to_gate_input()`, 15 tests, closing the "proven seam,
not yet a connected pipeline" gap named here. Confirms the identity/
authority fields (`identity_verified`, `authority_asserted`, etc.) have
no corresponding field in `permission_request`'s schema by design — a
request document cannot self-assert its own identity verification, the
same self-certification boundary `permission_request.py`'s own
`self_authorized`/PR-R-9 rule already enforces one layer up.

# D-002 — Hell's Gate: fourth-cycle disposition

STATUS: DECISION RECORDED — DO NOT WIRE. DO NOT DELETE WITHOUT HUMAN SIGN-OFF.
AGENT: ENGINEER C (integration), TITANOS cycle 002
DATE: 2026-09-01

## THE QUESTION

`foundation/hells_gate.py` has 36 passing tests and zero production
callers. It has carried the `IMPLEMENTED_UNWIRED` state for three prior
cycles. The standing order for this cycle: wire it to a real caller, or
propose deleting it. Leaving it unwired a fourth time without a fresh
answer is not acceptable.

## WHAT HELL'S GATE ACTUALLY REQUIRES FROM A CALLER

`evaluate(artifact: HellsGateArtifact)` runs ten independent gates and
needs the caller to have already determined, as *caller-declared facts*
(this module checks consistency of declared evidence, it does not
inspect the artifact's real behaviour):

1. INTENT — `stated_purpose`, `concealed_objective_signals`
2. HARM SCREEN — `harm_confirmed`, `harm_suspected`
3. REVERSIBILITY — `reversible`, `independently_verified`
4. PROVENANCE — `source`, `provenance_chain`
5. CAPABILITY VS CLAIM — `claimed_capabilities` vs `verified_capabilities`
   (two *separate* sets, not one)
6. CT_141 — `information_velocity`, `verification_velocity`
7. PRIVILEGE — `requested_privileges` vs `minimum_required_privileges`
8. BLACK ICE REFLECTION — `counterarguments_considered`,
   `criticism_prohibited`
9. THREE-RAIL — `proposes_action`, `verification_method_stated`
10. HUMAN BENEFICIARY — `beneficiary`, `measurable_benefit`

That is nine dataclass fields carrying real judgment content (not just
presence/shape), several of which require the caller to hold two
independently-sourced values for the same concept (5 and 7) so the gate
can detect a *gap* between them — a caller that derives both values from
the same source has already defeated the gate's purpose before
`evaluate()` runs.

## STEP 2 — RE-EXAMINING THE PRIOR CYCLE'S CONCLUSION

A prior cycle declined to wire Hell's Gate on the grounds that no caller
in this repository can supply its ten gates' evidence without
fabricating it. I re-checked all four candidates named for this cycle,
by reading each module's actual output shape and grepping for real
callers, not by trusting the module's name or docstring.

### `foundation/corpus_triage.py` — does not qualify

`triage()` returns a `CorpusReport`: `root`, `files`, `unique_content`,
`structural_templates`, `verdict`, `py_total`, `py_parse_failures`,
`py_constant_return_scaffolds`, `py_real_implementations`, `yaml_total`,
`yaml_not_structured`, `unresolved_imports`, `manifest_claims`, `facts`.
These are structural facts about files on disk (parse success, template
collapse ratio, import resolvability). None of them are `stated_purpose`,
`harm_confirmed`, `reversible`, `beneficiary`, or any of the other nine
Hell's Gate fields. A caller wiring `corpus_triage` into `hells_gate`
would have to invent a purpose, a beneficiary, a reversibility claim, a
privilege set and a counterargument list for a *delivered ZIP of files*
— none of which `corpus_triage` measures or could measure. Every one of
the corpora this module has actually triaged so far measured as
`SCAFFOLD_ONLY`; there is no real harm/privilege/beneficiary judgment
latent in "751 files collapse to 11 templates" to extract.

### `foundation/radar_rail.py` — does not qualify

`sweep()` produces a `RadarSweep` built from `CanonicalSignal` records
(`signal_spine.py`): `signal_id`, `source_id`, `source_type`,
`source_ref`, `target`, `kind`, `claim`, `observed_at`, `event_at`,
`source_lineage`, `pressure_class`, `pressure_evidence`, `money_state`,
`unknowns`. This is an observation report about GitHub activity — it
explicitly does not rank, promote, or decide anything
(`radar_rail.py`'s own docstring: "Acting on it ... stays a decision a
human or an explicit downstream kernel makes"). It has no intent
field, no harm field, no privilege field, no beneficiary field. Nothing
here is "seeking admission to the canonical core" in Hell's Gate's
sense — it is raw external signal, and per this repo's own doctrine
(`TITANOS_HELLS_GATE.md`'s Recursive Admission Loop) the gate belongs
after classification and Black Ice reflection, not before either exists.
Wiring `radar_rail` output straight into `hells_gate.evaluate()` would
mean inventing `beneficiary`/`measurable_benefit`/`counterarguments_
considered` per GitHub signal — none of which `radar_rail` computes.

### `experiments/EXP-001` pipeline (validator -> firewall -> kpm) — does not qualify, and is direct evidence against wiring

`EXP-001/FINDINGS.md` ran the *sibling* gate, `firewall.gate.evaluate()`
(same admission shape, ten-ish checks, same "no production caller"
status this repo's own `CLAUDE.md` records), against 28 real documents.
Finding 2 is the load-bearing result for this decision: once a synthetic
`authorization_valid: bool` was supplied by the experiment harness (not
derived from anything), the entire downstream verdict — including
whether the prompt-injection boundary fired — pivoted on that one
caller-declared, unverified boolean. The experiment's own conclusion:
*"this must be fixed before the firewall is ever wired, not after ...
the defect is latent because the module is unwired, and the moment it
is wired it becomes live."*

This is the precise failure mode Hell's Gate's own nine judgment fields
create if a caller has to synthesise them: `claimed_capabilities` vs
`verified_capabilities`, `requested_privileges` vs `minimum_required_
privileges`, `harm_confirmed`, `beneficiary` — every one of these is a
bare field on a frozen dataclass with **no verification mechanism
behind it**, exactly like `firewall.gate.Artifact.authorization_valid`.
EXP-001 already ran this exact experiment on the sibling gate and found
that synthetic evidence produces a gate that looks like it is working
while measuring nothing. Wiring `hells_gate` to a caller that has to
invent its nine fields would reproduce EXP-001 Finding 2 in a second
module, not resolve the standing question.

### `kpm/promotion/state_machine.py` — closest, still does not qualify

Real production callers exist: `foundation/task_queue.py`,
`foundation/crystal.py`, `foundation/situation_analysis.py`,
`foundation/switch_hardener.py`, `foundation/regression_engine.py`,
`rpa/gates/human_jurisdiction.py`, `magl/`, `narrative/`. The
`PromotionRecord`/blueprint shape (`kpm/schemas/blueprint_atom.py`)
carries genuine overlap with three of Hell's Gate's ten gates:
`purpose`/`problem` (Gate 1, INTENT), `provenance` (Gate 4), and
`threat_model`/`failure_modes`/`controls` (adjacent to Gate 2, HARM
SCREEN, though framed as risk documentation rather than a
confirmed/suspected split). That is a genuine partial match — closer
than the other three candidates — but it stops at three of ten, and the
schema's own field-group table marks `FRAMING` and `RISK` as
`verifiable=False` ("schema only checks shape/non-emptiness, not
quality" / "completeness of a threat model is a human judgment").
The remaining seven Hell's Gate fields have no corresponding blueprint
field at all: `concealed_objective_signals`, `harm_confirmed` vs
`harm_suspected` as a distinguished pair, `reversible`/`independently_
verified`, `claimed_capabilities` vs `verified_capabilities`,
`requested_privileges` vs `minimum_required_privileges`,
`counterarguments_considered`/`criticism_prohibited`, `beneficiary`/
`measurable_benefit`. A caller here would still have to fabricate
seven of ten fields to call `evaluate()` at all — better than the other
three candidates (which supply zero), but not "genuinely supplies the
evidence."

## DECISION

**No genuine caller exists in this repository today.** All four named
candidates were checked by reading their actual output shape and
grepping for real callers, not by name-matching. None can supply Hell's
Gate's ten gates' evidence without the calling code fabricating most of
it — and `EXP-001` already ran that exact experiment on this module's
sibling gate (`firewall.gate.evaluate()`) and documented, in detail,
that synthetic evidence for this class of gate produces exactly the
false-safety failure mode Hell's Gate exists to prevent. Wiring
`hells_gate` to any of the four candidates today would be the forbidden
move named explicitly in this cycle's brief: "importing hells_gate
somewhere solely to make a count change ... a forced import that no
real path exercises is worse than leaving it unwired."

I am **not** proposing deletion outright, and I am not leaving this as
an unexamined "still unwired." The honest state is narrower than either
extreme:

- The module itself is correct, tested, and doctrinally central — it is
  cross-referenced by name in at least six of this repository's sixteen
  loaded doctrine files, and `CLAUDE.md`'s own 2026-09-01 gate audit
  independently reached the same "no production caller" finding for
  this module, grouped with `contribution_gate`, `switch_hardener`,
  `taal/gate/root_gate`, `rpa/gates/human_jurisdiction`, and
  `firewall/gate` — i.e. this is not an isolated orphan, it is one of
  six gates in the same state, audited the same day, by a different
  pass.
- Deleting a doctrinally-load-bearing module with 36 passing tests, that
  every candidate caller was checked against in good faith this cycle,
  on the strength of "still no caller found this time" is a stronger
  claim than the evidence supports — it would need to survive the same
  scrutiny EXP-001 gave its sibling before being removed, and that
  scrutiny has not been run against deletion, only against wiring.
- The correct disposition is therefore: **hold at
  `IMPLEMENTED_UNWIRED`, explicitly re-scoped.** The capability this
  module actually provides is not "gate admission for any of this
  repo's existing pipelines" (none of them produce its evidence shape)
  — it is "gate admission for an artifact whose nine judgment fields
  have already been established by a human or an upstream verified
  process, before the artifact enters the canonical core." No such
  upstream process exists in this repository yet. That is a real,
  named gap, not a design flaw in `hells_gate.py`.

## WHAT WOULD HAVE TO BECOME TRUE TO WIRE IT (for keeping)

Any of the following would constitute a genuine caller, in order of how
directly it matches the module's actual contract:

1. **A human-authored admission record.** The most direct fit: a
   workflow where a human (not code) fills in `HellsGateArtifact`'s nine
   judgment fields for a specific artifact under review — e.g. an
   external contribution, a self-modification proposal, a new doctrine
   file — and `evaluate()` runs on that human-declared record. This
   requires no new inference code, only a thin CLI/form and a caller
   that constructs the dataclass from human input, then routes
   QUARANTINE through `quarantine_artifact()` as already built. This is
   the smallest genuine caller available and does not require any of
   the four candidates above to change.
2. **`kpm/promotion/state_machine.py` extended, not `hells_gate.py`
   bent to fit.** If blueprint promotion's `HUMAN_REVIEW -> STABLE`
   transition were extended to require a reviewer to also record harm/
   privilege/beneficiary judgments (not just purpose/provenance/risk as
   today), that extension would close three of the seven remaining
   gaps in one place, in the module that already has real callers,
   rather than inventing a parallel schema. This is a `kpm/`-owned
   change, out of scope for this cycle's ownership boundary.
3. **A real external contribution surface.** `TITANOS_LIVING_PARETO_
   FRONTIER_ARCHITECTURE.md` and `TITANOS_GREENLIGHT_AND_MEMETIC_
   DOCTRINE.md` both name this: FRONTIER-003/FRONTIER-008 (GitHub
   remote, contribution path) are blocked on "no GitHub remote exists
   to attach automation to." When that becomes false, an inbound
   contribution is the artifact type Hell's Gate was written for by
   name — and a contribution PR
   naturally carries most of the nine fields (stated purpose from the
   PR description, provenance from the commit/author, claimed vs
   verified capability from the PR's tests passing or not).

   (`TITANOS_HELLS_GATE.md`'s applicability list places "GitHub
   contributions" second, right after "code" — a direct match to this
   option.)

None of these three existed to be built this cycle without violating
the explicit prohibition against fabricating a forced import. All three
are recorded here so the next cycle does not re-run this exact
four-candidate check from zero.

## WHAT I DID NOT DO

I did not modify `foundation/hells_gate.py`. I did not modify
`foundation/tender_radar.py`, `foundation/tests/test_tender_radar.py`,
or `foundation/radar_rail.py` (out of ownership scope). I did not
delete anything — deletion is recorded above as considered and
declined, not executed; per this cycle's brief, deleting a module with
36 passing tests is a human decision, and I have not made the case that
deletion, rather than continued `IMPLEMENTED_UNWIRED` status, is
actually warranted. I did not add a forced import anywhere to move a
capability count.

## VERIFICATION (before / after — no code changed, so identical)

Full `foundation` suite, run before starting any investigation and not
touched since:

```
Ran 1899 tests in 475.763s
FAILED (failures=1)
authority_pulse tick: admitted=False reasons=("release_id 'PULSE_AUTHORITY_001' does not exist",)
```

This single failure is pre-existing and unrelated to Hell's Gate (it is
in an authority-pulse/release-id path); it was present before this
cycle began and no file this cycle owns touches it. No changes were
made to any source file, so the after-state is identical by
construction — re-running would reproduce the same 1899/1 result modulo
that pre-existing failure's own determinism.

`discover_capabilities()` state counts, before this cycle (unchanged
after, since no code was modified):

```
{'VERIFIED': 37, 'IMPLEMENTED_UNWIRED': 28, 'ENTRYPOINT': 8, 'UNTESTED': 2}
```

`foundation/hells_gate.py` remains one of the 28 `IMPLEMENTED_UNWIRED`
entries. That count did not change, and per this cycle's own forbidden-
move clause it should not change unless a genuine caller exists — none
does.

## NEXT ACTION FOR A HUMAN

Decide whether option 1 above (a human-authored admission workflow) is
worth building as its own small capability, independent of the four
candidates this cycle checked — it is the only one of the three that
does not require another owner's module to change first, and it does
not require the GitHub-remote blocker to resolve. If yes, that is a
same-shaped, differently-scoped follow-up cycle, not a re-litigation of
this one.

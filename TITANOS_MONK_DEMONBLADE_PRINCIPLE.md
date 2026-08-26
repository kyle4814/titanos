# TITANOS // MONK-DEMONBLADE PRINCIPLE

Added 2026-08-26 per Kyle's explicit instruction. Loaded at session start
via this project's `CLAUDE.md` — stateless config, not session memory.
Next doctrine file after `TITANOS_LAUNCH_SEQUENCE_001.md`. Compressed
per this session's own standing discipline (`TITANOS_GREENLIGHT_AND_
MEMETIC_DOCTRINE.md`, `TITANOS_MEMORY_IRRELEVANCE_PROTOCOL.md`): audited
against the fifteen files already loaded and found ~90% restatement —
same shape as `TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md`'s switch model,
`TITANOS_HELLS_GATE.md`'s admission boundary, and
`TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md`'s authority order
(human sovereignty > constitution > verification > automation > output).
Only the genuinely new contribution is recorded as new doctrine below;
everything else is a pointer to the existing implementation.

## WHAT WAS ALREADY FULLY COVERED (not restated as new doctrine)

The two-authority separation this directive names (capability vs.
consequence), the fail-closed default, and "no component may silently
upgrade its own output's meaning" are the same properties already
enforced by `foundation/hells_gate.py` (never outputs "TRUSTED"),
`foundation/publication_gate.py` (§5's two-independent-points rule),
and `taal/gate/root_gate.py`'s own docstring ("a green result means
cleared on the facts as declared, never definitely legitimate"). The
98/1/1 heuristic restates `TITANOS_GO_CYCLE_DOCTRINE.md` §VIII's
Capability Language discipline and the existing 99/1 principle in
`TITANOS_BLACK_ICE_DOCTRINE.md` §8, split one further point into
"generative capability" vs. "consequential human authority" — a framing
refinement, not a new ratio to enforce in code.

## WHAT WAS GENUINELY NEW

**Vocabulary, not mechanism.** "Monk" (bounded validating authority) and
"Demonblade" (unconstrained generative/adversarial capability) name two
roles this repository's code already separates but had no single memorable
term for. The formal notation —

```
capability(A) ≠ authority(A)
evidence_of_capability ≠ authorization_to_act
review ≠ validation
validation ≠ authority
metadata/history ≠ proof of every property someone might later claim from it
```

— is a compressed restatement of the exact conjunction this session
already derived empirically and used as the kill-test for the RPA and
switch-hardener recon passes:
`SEMANTIC_EQUIVALENCE_FRAUD ≡ DOMAIN_OBLIGATION_EXISTS ∧
GENERIC_STATE_REACHABLE_WITHOUT_IT ∧
REAL_CONSEQUENTIAL_CONSUMER_TREATS_STATE_AS_SUFFICIENT ∧
NO_ALTERNATE_DISCHARGE`. The Monk/Demonblade framing is adopted as the
session's standing narrative shorthand for this rule — useful for
communication, not a new check.

**The recursive-adversarial-self-use framing** ("the Demonblade can be
turned against the system itself") is the clearest restatement yet of
what the RPA/switch-hardener/TAAL/MAGL recon passes this session already
did in practice: generate an attack (Demonblade), then require the Monk's
full call-graph-to-consumer discipline before any finding is accepted,
with the switch-hardener/TAAL/MAGL cases standing as the proof the Monk
half actually can and does kill a manufactured finding, not just wave
every one through.

## WHAT WAS NOT BUILT THIS CYCLE

No code. No new gate, switch, or state machine — this directive supplied
naming and formal compression of already-implemented and already-exercised
behavior (`foundation/hells_gate.py`, `foundation/publication_gate.py`,
`rpa/gates/human_jurisdiction.py`, and the four recon passes completed
this session). Inventing a new "Monk module" or "Demonblade module"
would duplicate existing, working separation-of-authority code under a
new name — exactly the anti-pattern this session's own compression
discipline forbids.

## STANDING USE

Use "Demonblade" / "Monk" / "Gate" as the session's shorthand when
describing or running future adversarial-recon cycles: Demonblade
proposes the bypass hypothesis, Monk demands the real call graph and
real consumer, Gate is whichever existing enforcement point
(`hells_gate.py`, `publication_gate.py`, a domain-specific gate) the
finding would actually have to pass through. This is a communication
convention, not a new enforcement layer.

## ADDENDUM 2026-08-27 — DEFENSIVE-DOCTRINE RECON, NO BUILD

A 5-agent recon asked whether a dedicated "defensive military doctrine"
folder (frame admission, reality-contract refusal, power-transfer
audit, false-urgency resistance, off-ramp doctrine, containment,
recomputation, observer-attribution) was justified. All five agents
converged: **no new file.** Every one of the twelve candidate concepts
already has a real, grep-verified, tested implementation somewhere in
this repo — `hells_gate.py`'s fail-closed admission and refusal to
ever say "TRUSTED"; `situation_analysis.py`'s `HOLD`/
`AMBIGUOUS_MULTIPLE`/`OFFRAMP_DECISIONS` (optionality/off-ramp);
`crystal.py::is_current()` and `contradictions/registry.py`'s
evidence-gated `resolve()` (historical ≠ current truth); `flow_switch.py`'s
CT_141 panic detection (false-urgency resistance, already covered by
this repo's own Black Ice doctrine); `human_jurisdiction.py`'s
re-derive-from-frozen-history discipline and `SelfPromotionForbidden`
(authority verification); `regression_engine.py`'s propose-never-execute
boundary (already named, verbatim, "observe/propose/execute"). Building
a parallel file for any of these would duplicate working code under new
vocabulary — the exact anti-pattern this file's own opening section
already forbids.

Two genuinely absent things were found, both vocabulary-only, neither
requiring a new gate or file:

**Frame refusal ≠ denying a real structural finding.** A `KILLED`
`DemonbladeVerdict` or a raised `AnalysisNotSurvived` is a structural
finding, not "a frame" a caller can argue away rhetorically. Disputing
one legitimately requires a fresh `demonblade_pass()` run against new
evidence — never a reframing of the same evidence. See
`foundation/situation_analysis.py::AnalysisNotSurvived`.

**Power-transfer audit** is genuinely new vocabulary (zero prior
occurrences anywhere in this repo) with one real, narrow, current use:
when a future evaluator (an off-ramp/tension candidate, or any
caller-supplied proposal) is assessed, name explicitly which of
{agency, authority, optionality, time, identity, information,
future-freedom} it asks the evaluated party to give up — the same
`dimensions_scored`-style checklist shape `BottleneckCandidate` already
uses, not a new state machine. Not adopted as code this cycle — no real
unstructured-input caller exists yet to exercise it (the same reason a
"universal decision router" was already rejected in `PARETO_FRONTIER.md`).
If a real caller appears, this is the one candidate worth revisiting as
an addition to an existing evaluator, never a new gate.

No code changed. No new file created. `PARETO_FRONTIER.md` not
touched — every entry in its Rejected section is a code/build
candidate; there is no precedent for a pure-doctrine-addendum entry
there, and none was added.

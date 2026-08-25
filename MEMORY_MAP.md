# Memory Map

Priority item 1 of `TITANOS_MEMORY_IRRELEVANCE_PROTOCOL.md`'s build
directive — built before items 2-7 per this repo's own standing
Next-Lever Sequencer rule (a lower-priority item is never legitimate
while a higher one is unresolved). This file classifies everything this
repository currently loads or could load into that doctrine's five
tiers, and names the one real structural limitation found while doing
it, honestly, rather than silently working around it.

## The measured problem (real, not hypothetical)

`CLAUDE.md` currently `@`-imports 10 doctrine files unconditionally —
**1,665 lines, loaded at the start of every single session**, regardless
of what that session's task actually is:

```
 300 TITANOS_GO_CYCLE_DOCTRINE.md
 261 TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md
 148 TITANOS_PARETO_FRONTIER_RECURSION_ENGINE.md
 148 TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md
 134 TITANOS_HELLS_GATE.md
 131 TITANOS_GREENLIGHT_AND_MEMETIC_DOCTRINE.md
 127 TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md
 126 TITANOS_AKASHIC_NARRATIVE_ENGINE.md
 117 CLAUDE.md (the index itself)
 101 TITANOS_LAYER0_RECURSIVE_PARETO_FRONTIER.md
  72 TITANOS_NEXT_LEVER_SEQUENCER.md
```

By this doctrine's own definition (§2), essentially all of this content
is **Tier 3 (Indexed Doctrine)** — architecture rationale, design
principles, decision records — which §2 explicitly says must be
"retrieved selectively... NEVER LOAD ALL DOCTRINE BY DEFAULT." Measured
against its own rule, this repository's boot sequence currently violates
it: all ten files load as Tier 0 cost every session, whether or not the
session's task touches narrative atoms, MAGL composition, or any of the
other domain-specific doctrine.

## The honest limitation (named, not worked around)

This is a **platform constraint, not a design choice this repo made**:
Claude Code's `CLAUDE.md` `@`-import mechanism loads every imported file
unconditionally at session start — there is no native "load this file
only if the task touches X" primitive available to a project-level
config file. A `BOOT_CONTEXT_SELECTOR` (this doctrine's priority item 3)
that actually gated *which* files get `@`-imported would require either
(a) a platform capability that does not currently exist, or (b) removing
the `@`-imports entirely and replacing them with plain-text pointers that
`/boot` or a task instructs a session to `Read` selectively — which
trades automatic loading for manual discipline, and risks a session
simply never reading a doctrine file it needed. **Not solved this
cycle** — recorded as the honest state, not silently patched over with
a half-working selector that would look done without being done.

## Tier classification of what exists today

### Tier 0 — Invariants (small, operational, testable — the correct boot load)

Everything in this list is already **enforced in code**, not just
written as doctrine — that is what makes it legitimately Tier 0 rather
than Tier 3 restated:

- Fail-closed on unknown (`foundation/publication_gate.py`,
  `foundation/hells_gate.py` — default `QUARANTINE`, never `TRUSTED`)
- No delete surface on any store (`firewall/quarantine.py`,
  `kpm/promotion/state_machine.py`, `foundation/reality_yield_ledger.py`,
  `foundation/crystal.py`, `magl/registry/catalogue.py`)
- Two-point enforcement on load-bearing invariants (`foundation/
  publication_gate.py::authorize_publish()` re-derives from evidence
  rather than trusting a cached flag)
- No self-certification (`kpm/promotion/state_machine.py::
  SelfPromotionForbidden`)
- CT_141: SIGNAL_COLLAPSE has no panic-based exit
  (`foundation/flow_switch.py::MODE_TRANSITIONS`)
- Symbolic content has zero effect on technical enforcement
  (`firewall/gate.py`, `taal/schema/threat_archetype.py`, tested)
- ABC-enforced mandatory hooks (`foundation/layer0_worker.py` — a
  subclass missing `check_existing`/`verify`/`preserve_provenance`/
  `update_state` cannot be instantiated)
- `UNKNOWN` is a valid, non-defaulted output state (narrative promotion
  states, epistemic classifications, Hell's Gate gates)

This list is intentionally short. **This doctrine's own rule for Tier 0
applies to itself**: "if it cannot affect a decision, validation, state
transition, test, or execution boundary, it does not belong in Tier 0."
None of the nine `TITANOS_*.md` doctrine files' prose belongs here —
their prose is the *rationale* for these invariants, which is Tier 3.

### Tier 1 — Live state (the minimum "what is happening now")

- `NEXT_MOVE.md` — the single standing recommendation
- `PARETO_FRONTIER.md` — ranked candidate moves, current status
- `HUMAN_DECISIONS.md` — open judgment calls
- Latest full-repo test count (currently 915, `foundation/BUILD_REPORT.md`
  and seven sibling `BUILD_REPORT.md` files carry the per-subsystem detail)

These are already correctly small, current, and read by `/boot` — no
gap found here.

### Tier 2 — Executable knowledge (the preferred durable form)

Every `.py` file under `schema/`, `firewall/`, `kpm/`, `magl/`, `rpa/`,
`taal/`, `foundation/`, `narrative/` and their `tests/` — 915 tests
across 8 suites. This is already this repository's dominant form of
memory, by construction (every prior cycle's stated discipline was
"compile the lesson into code, not prose") — no gap found here either.

### Tier 3 — Indexed doctrine (should be selective, currently is not)

All ten `TITANOS_*.md` files. This is where the measured problem above
lives. Honest status: **written as Tier 3, loaded as Tier 0**, because
of the platform limitation named above.

### Tier 4 — Provenance archive (not loaded by default — correctly so)

`failures/FAILURE_ARCHIVE.md`, superseded `PromotionStore`/
`RealityYieldLedger`/`CrystalStore`/`QuarantineStore` entries (retained,
never deleted, per every store's no-delete-surface rule), git history
itself. Not loaded at boot; retrieved on demand (regression
investigation, audit). No gap found here.

## What this map does NOT recommend doing

It does not recommend deleting or shrinking any of the ten doctrine
files — their content is the actual governing rationale for the Tier 0
invariants above, and `TITANOS_GO_CYCLE_DOCTRINE.md` §X (the Corpus
Engine) already establishes that preserving the path, not just the
conclusion, matters. The finding here is narrower: **the loading
mechanism, not the content, is what doesn't yet match the Memory
Irrelevance Protocol's own Tier model.**

## Next lever (recorded, not built this cycle)

`PARETO_FRONTIER.md` FRONTIER-009: investigate whether `CLAUDE.md`'s
`@`-imports can be replaced with a lighter always-loaded Tier-0-only
file (a distilled, code-referencing invariant list — the seed of which
is the bulleted list above) plus plain-text pointers to the ten doctrine
files for `/boot` or a task to `Read` selectively when the active
task's domain requires it. This is priority item 3 (Boot Context
Selector) in the Memory Irrelevance Protocol's own build order —
correctly sequenced *after* this map (item 1), not before it.

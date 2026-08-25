# Pareto Frontier — Capability Map

Not a backlog. Per `TITANOS_ADDENDUM_FRONTIER_AS_CAPABILITY_MAP.md`
(loaded via `CLAUDE.md`), this file is the navigation surface between
what this repository can demonstrably do (code + tests) and what it can
next become (the smallest credible delta). `/boot` loads it. Distinct
from `HUMAN_DECISIONS.md` (judgment calls only a human can resolve) and
from `INTUITION.md` (low-commitment discovery — nothing there is
authorized work until it passes the Frontier Gate below and moves here).

**Staleness is a real risk, named not hidden.** An entry not touched in
a long time should be re-verified against real repository state before
being trusted, not assumed still accurate.

---

## Frontier Gate

No candidate enters "Active" without answering all seven. If it can't
answer these yet, it stays in `INTUITION.md`, not here.

1. **CURRENT** — what the repository can demonstrably do right now.
2. **GAP** — the specific missing capability.
3. **LEVER** — why closing this gap is disproportionately valuable.
4. **FIRST STEP** — the smallest implementation or proof.
5. **PROOF** — how the new capability becomes verified.
6. **UNLOCK** — what becomes reachable afterward.
7. **REUSE** — what existing work this builds on rather than duplicates.

## Active

### FRONTIER-009 — Boot Context Selector for `CLAUDE.md` doctrine imports
- **CURRENT:** `MEMORY_MAP.md` (built) measured 1,700+ lines across
  doctrine files loading unconditionally at every session boot — now
  16 `@`-imports (grown from 12 at measurement time), count re-verified
  2026-08-25 via `FRONTIER_009_RECON_001`. Tier-3 content paying Tier-0 cost.
- **GAP:** no mechanism loads only the doctrine relevant to the active
  task.
- **CAUSAL GAP RE-EXAMINED (`FRONTIER_009_RECON_001`):** no session has
  ever failed to reliably do anything *because* of this — the current
  system correctly loads all doctrine, every time. The cost is verbosity,
  not a correctness failure. The chain "without X, the system cannot
  reliably do Y, because Z" cannot honestly be written: X's absence
  produces no observed Y failure. This entry's own `effort`/`risk`
  fields already concluded the fix trades a loud cost (verbose boot) for
  a silent one (a session missing doctrine it needed) — net negative.
  **Verdict: D — UNNECESSARY. Stays OPEN, not built, not reordered.**
- **LEVER:** reduces boot context size with no functional change.
- **FIRST STEP:** genuinely uncertain — see below.
- **PROOF:** would need a regression test proving a session can still
  discover a doctrine file it needs despite not auto-loading it.
- **UNLOCK:** cheaper, faster session boots as the doctrine stack grows
  further.
- **REUSE:** `MEMORY_MAP.md`'s tier classification.
- **effort:** MEDIUM-HIGH — no native lazy-`@`-import capability exists
  in Claude Code; the only implementation path is removing `@`-imports
  entirely and replacing them with plain-text pointers a session reads
  selectively, which trades automatic loading for manual discipline and
  risks a session silently missing doctrine it needed (a silent failure
  mode, worse than a loud one). **risk:** LOW-MEDIUM for this reason —
  not yet clearly a net win, which is why this remains OPEN rather than
  promoted to "smallest first move now."

### FRONTIER-008 — Per-subsystem seed/manifest packaging
- **CURRENT:** `firewall/`, `schema/`, `kpm/`, `magl/` all have a
  verified `ADOPT.md` (2026-08-25/26) — every quickstart's *code*, not
  just its test command, independently re-run and matched. `kpm/
  ADOPT.md`'s first draft caught two real inaccuracies before shipping;
  `magl/ADOPT.md` reused its own `test_end_to_end.py`'s exact
  demonstrated path rather than inventing one, and it also ran clean
  first try. 4 of 8 subsystems (`rpa/`, `taal/`, `foundation/`,
  `narrative/`) still lack this doc.
- **GAP:** template proven four times; not yet replicated to the rest.
- **LEVER:** MEDIUM-HIGH — real now that `kyle4814/titanos` is public
  and CI-green.
- **FIRST STEP:** done (`firewall/`, `schema/`, `kpm/`, `magl/`). Next:
  replicate to the remaining 4.
- **PROOF:** `firewall/ADOPT.md`'s quickstart commands independently
  re-run and matched, not just written.
- **UNLOCK:** `TITANOS_GREENLIGHT_AND_MEMETIC_DOCTRINE.md`'s Seed/
  Manifest chain (PACKAGE step) has a real first instance, not a
  speculative field list.
- **REUSE:** `firewall/BUILD_REPORT.md`'s content as source material for
  the threat-model/limitations sections; externalizes it, doesn't
  duplicate it.

## Blocked

### FRONTIER-005 — Five-Record query views, Gold Ledger, Isomorphism contract
- **CURRENT:** FRONTIER-004 (`NarrativeAtomStore`) is now built. Two
  real narrative atoms exist (`NA-INGEST-001`/`NA-INGEST-002`,
  `narrative/tests/test_real_ingestion_recursion_guard.py`, commit
  `5c73498`) — real, not synthetic, but thin.
- **GAP:** views/ledger/contract over content that barely exists yet.
- **blocked_by:** partially resolved — FRONTIER-004 dependency is
  satisfied; the "real ingestion source" dependency is technically
  non-zero but not yet substantial enough to build query views/a Gold
  Ledger against without the result being speculative. Not force-
  unblocked; stays Blocked until more real content exists.
- Items (B)/(C)/(F) of `TITANOS_AKASHIC_NARRATIVE_ENGINE.md` §XVIII,
  deliberately deferred — "do not build everything at once."

## Archive (built)

One line each — full reasoning lives in the commit that built it. Kept
here, not deleted, per this file's own Archivist principle; removed
from the active scan path per this addendum's compaction rule.

| ID | Capability | Commit |
|---|---|---|
| FRONTIER-RG | Bounded recursive execution ancestry (recursion guard) | `93b3e89` |
| FRONTIER-004 | Narrative Atom Store (`narrative/store/narrative_atom_store.py`) | `d5537c1` |
| FRONTIER-MEMBRANE | Source Vault -> Narrative Atom bridge (`narrative/intake/source_vault_bridge.py`) | `4ac4ef6` |
| FRONTIER-000 | Narrative Atom schema + validator | `d14e128` |
| FRONTIER-006 | Layer 0 Worker Contract (ABC-enforced) | `f416cd0` |
| FRONTIER-007 | Crystalline Memory (`foundation/crystal.py`) | `7ecf615` |
| FRONTIER-MAP | Memory Map / boot-load tier audit | `f5c2f34` |
| FRONTIER-010 | Sentinel_141 Level 1 Pulse Sweep | `b25b680` |
| FRONTIER-012 | Bounded Task Queue Workflow | `f5de342` |
| FRONTIER-013 | Queue ↔ Layer0Worker execution seam | `0b1efba` |
| FRONTIER-014 | Closed-loop reality proof (real worker) | `190b119` |
| FRONTIER-015 | Explicit run deferral + recovery handoff | `44c9b18` |
| FRONTIER-011 | `BUILD_REPORT.md` for schema/firewall/narrative | `e816905` |
| FRONTIER-001 | Reusable secret/credential scanner | `1b03480` |
| FRONTIER-002 | `permission_request` → `GateInput` adapter | `632e774` |
| SIGIL | Capability Sigil (`foundation/sigil.py`, `SIGIL.md`) | `e3ce475` |
| FRONTIER-FSCHEMA | `PARETO_FRONTIER.md` structural schema validator (`foundation/sentinel.py::check_frontier_schema`) | `cbcb73f` |
| FRONTIER-REFCHECK | RPA cross-file referential integrity checker (`rpa/composition/checker.py`) | `9a63205`, extended `d8afa32`, `3741094`, `b5cad9a` |
| FRONTIER-CONCLUDE | Coded Conclusion Gate (`foundation/conclusion_gate.py`) | `c53411f` |
| FRONTIER-CONCLUDE-ENFORCE | Conclusion Gate enforced at `Layer0Worker.run()` (mandatory, not optional) | `8c91b81` |
| FRONTIER-MANIFEST | Runtime dependency manifest (`requirements.txt`, PyYAML pinned) | `b2ce4b1` |
| FRONTIER-COMM-SWITCH | External Communication switch, prerequisite only (`foundation/communication_gate.py`) — no retrieval capability implemented | `ff7af45` |
| FRONTIER-NARRATIVE-REFCHECK | Narrative atom cross-atom referential integrity checker (`narrative/composition/checker.py`) | `67c3507` |
| FRONTIER-INVARIANT-SPECIMEN | First proven invariant durably registered in `SIGIL_LEXICON.md` (`SIGIL.REF_INTEGRITY`, transferred rpa->narrative) | `5fd5dc7` |
| FRONTIER-NO-DELETE-INVARIANT | Second registered invariant (`SIGIL.NO_DELETE_SURFACE`), proven across 8 independent stores, stronger than the control specimen | `e560129` |
| FRONTIER-ABSENT-EDGE-INVARIANT | Third registered invariant (`SIGIL.ABSENT_ILLEGAL_EDGE`), proven across 6 independent state machines, independence verified by import-check test | `e8e1cf2` |
| FRONTIER-NO-CACHED-DECISION | Fourth registered invariant (`SIGIL.NO_CACHED_DECISION`), correctly scoped to 2 domains after recon disproved a false 3-domain claim; also fixed an audit gap in an existing test | `95906bb` |
| FRONTIER-EPISTEMIC-FREEZE | Closed a real, reproduced epistemic-state collapse: froze 5 append-only record types (Claim, AtomRecord, PromotionRecord, QuarantineRecord, FlowSwitchRecord) that were bypassable via direct attribute assignment | `3dcb258` |
| FRONTIER-HISTORY-FREEZE | Closed a real, LIVE exploit: the same 5 types' `history` field was still a mutable list under freezing -- converted to tuple, closing a forged-entry bypass of `rpa/gates/human_jurisdiction.py`'s pilot-authorization gate | `8e0e12d` |
| FRONTIER-003 | CI workflow real and green (`kyle4814/titanos` created public, pushed, `.github/workflows/tests.yml` fired for the first time and passed, 8/8 subsystems) | `6fb29fa` (workflow) + live push 2026-08-25 |
| FIRST-PING | First proven `WORLD -> TITANOS -> WORLD` exchange: real GitHub Actions run ingested + classified through the existing (pre-built) digestion pipeline, self-sourced not human-supplied. See `FIRST_PING.md`. No new code. | (this commit) |

## Rejected / not on the frontier

- **Full `core/`/`workers/`/`ledgers/` directory restructure** — would
  duplicate existing structure (`foundation/`/`magl/`/`rpa/`/`taal/`
  already are the shapes proposed) or be empty theater (typed worker
  directories with no code). Rejected as the *next move*, not as a
  future possibility — if a genuine need for typed worker processes
  emerges, build that need directly, don't pre-build scaffolding.

## How to use this file

1. Check here before proposing new work — an entry may already exist
   with its trade-offs worked out.
2. A candidate must pass the Frontier Gate (all 7 questions answered)
   before it's added under Active.
3. When built, move the entry's one-line summary to the Archive table
   and note the commit — don't leave stale full-prose entries active.
4. Re-verify a long-untouched entry against real repository state
   before trusting it.

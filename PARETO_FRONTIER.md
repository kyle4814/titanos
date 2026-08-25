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

## Blocked

### FRONTIER-003 — CI workflow (`.github/workflows/`)
- **CURRENT:** test command is already simple and uniform (`python3 -m
  unittest discover` per subsystem), no build step, no secrets needed.
- **GAP:** no workflow file, and no GitHub remote to attach one to.
- **LEVER:** "CI is the heartbeat" once real — HIGH value, but a
  workflow file with nothing to trigger it is empty theater today.
- **blocked_by:** `HUMAN_DECISIONS.md` item 1 (no GitHub repo target
  named yet).

### FRONTIER-008 — Per-subsystem seed/manifest packaging
- **CURRENT:** each subsystem now has a `BUILD_REPORT.md` (internal
  audit trail); none has an external "how to adopt/fork/remove this"
  document (thesis, quickstart, failure cases, threat model, fork
  guide, contribution path).
- **GAP:** no packaging template.
- **LEVER:** MEDIUM-HIGH once publication is real.
- **blocked_by:** same as FRONTIER-003 — a fork guide has nowhere to
  point without a GitHub remote.

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

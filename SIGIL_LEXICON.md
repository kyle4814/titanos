# Sigil Lexicon

A compressed index into proven repository concepts — not a second
source of truth. **The sigil is not the architecture.** Canonical
resolution always runs: `Stable_ID → Glyph → Canonical Meaning →
Source → Proof → Status → Version`. Source precedence: `CODE > TESTS >
PROOF > DOCTRINE > SIGIL`.

Distinct from `SIGIL.md` (`foundation/sigil.py`'s computed capability
tier — `TIER:Tn | IRON:.. | ...`). This file indexes *concepts*; that
one indexes *maturity*.

## Uniqueness law

One Stable_ID → one canonical meaning. One glyph → one canonical
meaning. A meaning change requires a new version/supersession entry,
never a silent mutation. Ambiguity or collision → expand to canonical
text, never guess. Every glyph retains an ASCII Stable_ID fallback —
rendering failure must never make the architecture undecodable.

## Seeded entries (already-proven concepts only)

| ID | Glyph | Name | Meaning | Class | Status | Source | Proof | Version |
|---|---|---|---|---|---|---|---|---|
| SIGIL.EXECUTION_ANCESTRY | ⛓ | execution ancestry | protected execution lineage carried across a process boundary | L4 invariant | ACTIVE | `foundation/recursion_guard.py` | `foundation/tests/test_recursion_guard.py` (13 tests) | 1 |
| SIGIL.PROCESS_BOUNDARY | ↳ | process boundary | the point where a child/spawned execution begins | L4 invariant | ACTIVE | `foundation/recursion_guard.py::child_env()` | same as above | 1 |
| SIGIL.RECURSIVE_REENTRY | ⟳ | recursive re-entry | the same protected operation appearing again in active ancestry | L4 invariant | ACTIVE | `foundation/recursion_guard.py::check()` | same as above | 1 |
| SIGIL.BOUNDED_BLOCK | ⊘ | bounded block | prohibited repetition blocked before descendant multiplication | L4 invariant | ACTIVE | `foundation/recursion_guard.py::GuardDecision.BLOCKED_REPEAT/BLOCKED_DEPTH` | same as above | 1 |
| SIGIL.PROVEN | ✓ | proven | evidence-backed property (code + test, not claim) | L5 proof | ACTIVE | (cross-cutting) | this session's targeted/regression runs | 1 |
| SIGIL.LIMITATION | ⚠ | limitation | a known, honestly stated boundary of a proven property | L5 proof | ACTIVE | `TITANOS_RECURSION_GUARD_001.md` §LIMITATION | — | 1 |
| SIGIL.VERIFIED_CHANGE | Δ | verified change | a repository mutation confirmed by targeted + regression proof | L3 capability | ACTIVE | (cross-cutting) | commit `93b3e89` | 1 |
| SIGIL.DURABLE_STATE | ▣ | durable state | committed, reconciled repository state (not chat context) | L1 domain | ACTIVE | `PARETO_FRONTIER.md`, `SIGIL.md`, `NEXT_MOVE.md` | (repo-native, no single test) | 1 |
| SIGIL.MIN_CAUSAL_SEAM | ⌁ | minimum causal seam | the smallest single point requiring inspection to resolve an ambiguity | L2 component | ACTIVE | (methodological, this session's own recurring practice) | — | 1 |

## Evolution contract (future, not yet implemented)

On a future proven architectural change: extract the changed concept →
compare against existing Stable_IDs → if it matches an existing entry,
update its refs/proof/version; if it's genuinely new and proven, add an
entry; if unproven, do not promote it; if it supersedes an existing
entry, retain the old entry marked `SUPERSEDED` with an alias, never
delete; if ambiguous, escalate rather than guess. **This is a
reconciliation contract for a human/model to follow by hand** — no
automated scanning code exists yet. Claiming otherwise would be exactly
the "no glyph exceeds its evidence" violation this file exists to
prevent.

## Architecture levels (reference)

L0 SYSTEM · L1 DOMAIN · L2 COMPONENT · L3 CAPABILITY · L4 INVARIANT · L5 PROOF

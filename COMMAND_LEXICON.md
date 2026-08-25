# Command Lexicon

A specification, **not a runtime engine**. Nothing in this repository
executes or resolves the symbols below — no parser exists, and none is
built here (see Atomic Move, below). This document exists because the
same execution chain has now repeated across 12+ consecutive commits in
this repository's real history (`git log`, `93b3e89` through `5c73498`),
stable in ordering, stable in preconditions, stable in stop condition —
compressing it here reduces repeated prose, nothing more.

**Distinct from `SIGIL_LEXICON.md`**: that file indexes proven
*concepts* (execution ancestry, bounded block, ...). This file indexes
one proven *execution chain* (a sequence of steps), a different kind of
object.

**Distinct from `.claude/commands/`**: `boot.md` and `go.md` in that
directory are this repository's actual working command mechanism —
real, deterministically expanded by Claude Code at invocation. This
lexicon does not replace or duplicate them; it documents a *smaller*,
sub-command-level pattern that recurs *inside* a `/go`-style cycle, not
a new invocation surface.

## The one proven chain

```
⌕ RECON → Δ ATOMIC_DELTA → ✓ TARGETED_PROOF → R8 FULL_REGRESSION
→ PROCØ PROCESS_CLEAN → DOC+ DOCUMENT_RECONCILE → C COMMIT_EXACT
→ ▣ DURABLE_HANDOFF → STOP
```

Evidence: this exact shape (recon → minimum implementation → focused
tests → 8-subsystem regression → process-residue check where
subprocess spawning was involved → frontier/doctrine reconciliation →
exact commit → compact report) appears in every commit message from
`93b3e89` onward, in this order, every time — a real, repeated,
stable-ordered pattern, not a proposed abstraction.

## Command definitions

Each entry: `CANONICAL_NAME` / `EXPANSION` / `PRECONDITIONS` /
`EXPECTED_OUTPUT` / `STOP_BOUNDARY` / `EVIDENCE_REQUIREMENT`.

### ⌕ RECON
- **Expansion:** Inspect actual repository state before any edit.
  Classify relevant components EXISTS / PARTIAL / MISSING /
  UNNECESSARY. Reuse existing contracts; do not assume a capability
  exists or is missing without checking.
- **Preconditions:** none (always safe to run).
- **Expected output:** a classification, and the smallest evidenced gap.
- **Stop boundary:** stop once the seam is sufficiently evidenced —
  do not broad-recon stable, unrelated architecture.
- **Evidence requirement:** each classification cites a file/grep/test
  result, not an assumption.

### Δ ATOMIC_DELTA
- **Expansion:** implement exactly the smallest change RECON justified.
  No new framework, no speculative generalization, no unrelated cleanup.
- **Preconditions:** ⌕ RECON complete, gap evidenced.
- **Expected output:** one coherent code change.
- **Stop boundary:** stop at the scoped delta; do not expand mid-build.
- **Evidence requirement:** the change traces directly to RECON's finding.

### ✓ TARGETED_PROOF
- **Expansion:** run exactly the tests covering the changed property
  (new + directly adjacent existing tests).
- **Preconditions:** Δ ATOMIC_DELTA complete.
- **Expected output:** pass/fail with exact counts, not a summary claim.
- **Stop boundary:** on failure, stop and find the minimum causal seam
  before continuing — never patch around a failing targeted test.
- **Evidence requirement:** actual test runner output, not "should pass."

### R8 FULL_REGRESSION
- **Expansion:** run all 8 subsystems' suites via the established
  isolated-subprocess-per-subsystem method (`python3 -m unittest
  discover -s <subsystem> -p "test_*.py"` per subsystem, never a single
  in-process cross-subsystem `discover()` — see `foundation/sigil.py`'s
  own docstring for why that collides on same-named sibling `tests`
  packages).
- **Preconditions:** ✓ TARGETED_PROOF green.
- **Expected output:** 8/8 exit codes, each subsystem's own test count.
- **Stop boundary:** any subsystem failing stops the chain; classify
  CAUSED_BY_THIS_DELTA vs. pre-existing before continuing.
- **Evidence requirement:** exit codes recorded per subsystem, not "ran fine."

### PROCØ PROCESS_CLEAN
- **Expansion:** verify no persistent orphaned process remains,
  specifically where this cycle spawned subprocesses (`pgrep -f
  unittest` or equivalent). A single matching PID must be *inspected*
  (`ps -p <pid>`) before being trusted as a real orphan — `pgrep`
  transiently matches its own short-lived invocation.
- **Preconditions:** applicable only when this cycle spawned
  subprocesses (R8, or any `subprocess.run` call in the delta).
- **Expected output:** Ø, or an inspected, classified non-Ø result.
- **Stop boundary:** a genuine persistent orphan stops the chain — kill
  it, find the causal seam, do not proceed to commit.
- **Evidence requirement:** the actual `pgrep`/`ps` output, not "should be clean."

### DOC+ DOCUMENT_RECONCILE
- **Expansion:** update only the durable truth surfaces this delta
  actually changed — `PARETO_FRONTIER.md` (move OPEN→Archive),
  `NEXT_MOVE.md`, `SIGIL.md` (only if a dimension genuinely moved),
  `CLAUDE.md` (only if a new doctrine file was added), the relevant
  subsystem `BUILD_REPORT.md`. Do not touch files this delta didn't affect.
- **Preconditions:** R8 (and PROCØ where applicable) green.
- **Expected output:** exactly the files with real, evidenced content changes.
- **Stop boundary:** do not mechanically update every durable file "for completeness."
- **Evidence requirement:** each doc change cites the specific proof it reflects.

### C COMMIT_EXACT
- **Expansion:** `git status`/`git diff`, classify every changed file
  (CORE/TEST/DOC/UNRELATED), stage only the verified cycle delta,
  commit with a message stating what was built, what was reused, what
  was proven, what failed and was fixed along the way.
- **Preconditions:** DOC+ complete (or explicitly not required).
- **Expected output:** one commit, exact hash.
- **Stop boundary:** unrelated staged changes are reported, never
  swept into the commit.
- **Evidence requirement:** post-commit `git status` confirms clean or
  explicitly classifies the remainder.

### ▣ DURABLE_HANDOFF
- **Expansion:** compact report — ground, delta, proof, limitation,
  frontier/sigil movement, commit hash, next atomic move — sufficient
  for a fresh session to continue without replaying this transcript.
- **Preconditions:** C COMMIT_EXACT complete (or chain stopped at ⌁).
- **Expected output:** the report itself.
- **Stop boundary:** this ends the cycle.
- **Evidence requirement:** every claim in the report traces to a
  preceding step's actual output, not restated intent.

### ⌁ BLOCKED
- **Expansion:** stop immediately with the exact causal blocker —
  what's missing, why the chain cannot safely continue, what would
  resolve it. Never a vague "issue found."
- **Preconditions:** any step above fails or cannot be evidenced.
- **Stop boundary:** terminates the chain at the point of failure.

## Chain law

`A → B` = sequence (B requires A's output). No `⇢` dependency-without-
sequence, `|` option, `⊘` exclusion, or `⛓` gate operators are defined
yet — the one proven chain observed in this repository is a strict
linear sequence with a single early-exit (`⌁ BLOCKED`, reachable from
any step). Do not add branching operators speculatively; add them when
a real chain in this repository's history actually branches.

## Context inheritance

This lexicon does not track state itself — `NEXT_MOVE.md` (single
standing recommendation) and `PARETO_FRONTIER.md` (ranked candidates)
already do, and `DOC+`/`▣` above explicitly reference them rather than
duplicating a second tracking mechanism.

## Speed claim

None made. This document claims exactly: the same 8-step chain has
recurred, in the same order, across 12+ real commits. It does not
claim token savings, reasoning speed, or execution reliability
improvements — no baseline-vs-lexicon comparison has been run. If that
comparison is ever run, record it here with the actual measurement, not
before.

## Atomic move taken this cycle: A

Specification only. No parser/resolver was built (Atomic Move D
declined) — nothing in this repository's actual tooling consumes these
symbols; `.claude/commands/boot.md`/`go.md` remain the only real,
runtime-resolved command surface. A symbolic parser here would have no
caller and no test oracle beyond invented examples.

<!-- STATE_CLAIMS: NONE -->
# Next Move

Exactly one recommendation for the next cycle. Not a queue — superseded
entries move to `PARETO_FRONTIER.md` rather than accumulating here.

## This file no longer states system state, and that is deliberate

The `STATE_CLAIMS: NONE` marker at the top is a contract, not decoration.
`foundation/system_manifest.py` honours it and skips the staleness check
for this file. Any commit hash below appears inside a HISTORICAL
narrative about a past incident, never as an assertion about the current
repository. **If a future edit adds a real state claim here, remove that
marker** — leaving it in place while asserting current state would be a
deliberate lie, and no automated check can prevent that one.

**Rewritten 2026-09-01 to remove a defect class rather than patch it a
third time.**

Previous versions of this file recorded HEAD, ahead/behind counts, test
totals and pulse status in prose. Every version went stale, and the file
itself documents two prior incidents at length: one where it asserted
HEAD `3f2bb79` and "9 commits ahead, nothing pushed" after the work had
been pushed and HEAD had advanced five commits; another where a fresh
engineer auditing the repository found it claiming "0 ahead, 0 behind"
against a repository 37 commits ahead.

A third recurrence was detected automatically on 2026-09-01 by
`foundation/system_manifest.py`, which compares any commit hash cited
here against real history and reported that all seven cited commits were
unknown to `HEAD`.

Three incidents of one class is not bad luck. The cause is structural:
**this file was a second source of truth for facts a program can
compute.** So it no longer carries them.

- **For system state**, run `python3 -m foundation.system_manifest`. It
  computes HEAD, worktree cleanliness, test inventory, ledger contents,
  receipt head, pulse findings and open human decisions from disk every
  time, and stores nothing it could later lie with.
- **For test status**, run `./run_all_tests.sh`. One command, one
  summary line, per-suite timings.
- **For launch criteria**, run `python3 -m foundation.launch_report`,
  which derives `READY` / `READY_WITH_LIMITATIONS` / `NO_GO` rather than
  letting anyone choose it.

What remains below is the only thing none of those can produce: a
judgement about what to do next.

---

## Recommendation

**Decide whether an autonomous entrypoint gets scheduled.**

This is a human decision and it is the only thing standing between the
measured `autonomy_ratio` of `0.0000` and a real non-zero figure.
Everything it depended on now exists and is proven by execution:

- `foundation/autonomous_window.py` runs bounded cycles, checkpoints
  after each one, resumes on restart, and stops for one of five named
  reasons.
- `foundation/checkpoint.py` writes atomically and refuses a forged
  checkpoint rather than resuming from it.
- `foundation/autonomy_loop.py` holds a kill switch, refuses a dirty
  tree, rolls back on failed verification, and commits only a single
  pathspec.
- `foundation/write_scope.py` makes a write boundary checkable in code
  rather than promised in a prompt.

The recommendation remains **do not schedule yet**, for one measured
reason: the window observes and checkpoints but performs no repair, and
`autonomy_loop` still handles exactly one finding class. A scheduled
process that can only correct a number in a README does not earn
standing authority to commit unattended. See `HUMAN_DECISIONS.md` for
the full case, the loop's own safety bounds, and the exact cron line if
that judgement is disagreed with.

## The engineering lane, if no human decision is available

Two blue-team exposures remain open and are documented rather than
fixed, both with reasons:

1. **Commit-subject keyword gaming** — `code_pressure.classify_subject`
   is a keyword regex over attacker-controlled text. Requires push
   access to the target repository, and the module already declares
   subject-line evidence as weak. Closing it properly means diff
   statistics, which cost one API request per commit against a 60/hour
   unauthenticated budget.
2. **Homoglyph substitution** — undetected by `untrusted_text.py`, which
   says so in its own docstring. Verified orthogonal to authority: title
   text never feeds a verdict, so an undetected homoglyph cannot move a
   classification.

Neither dominates the human decision above. Both are recorded in
`REMAINING_LIMITATIONS.md`, which is generated.

## How to check whether this file has gone stale again

It no longer cites a commit, so the automatic check has nothing to catch
— which is the point. Judge it on whether the recommendation still
matches reality:

```sh
python3 -m foundation.launch_report    # unmet criteria
python3 -m foundation.autonomy_metric  # is anything scheduled yet?
```

If `autonomy_ratio` is no longer `0.0000`, the recommendation above has
been acted on and this file needs a new one.

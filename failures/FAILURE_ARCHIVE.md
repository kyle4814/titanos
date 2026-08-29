# TitanOS — Failure Archive

**Generation:** 002
**Status:** OPEN — this archive is never closed
**Scope:** Generation 001 covers 2026-08-19 → 2026-08-24 (F-001…F-010).
Generation 002 covers 2026-08-28 → 2026-08-29 (F-011…F-014).

**Gap disclosed rather than hidden:** this file went unwritten between
2026-08-25 and 2026-08-29 while the repository kept producing real,
reproduced, fixed defects. Those four are recorded below, recovered from
git history. An archive that claims to be "never closed" and then stops
being written is itself the failure class this repository hunts — a
claim outliving its evidence — so the lapse is stated here rather than
quietly backfilled.

This archive exists because an architecture that only records its successes
is an advertisement, not a record. Every entry below is a real defect in
real code, most of them found by tests rather than by review — which is
itself the most useful finding in the archive.

Each entry states what failed, how it was found, why it mattered, and what
remains unresolved. Entries are **never deleted**. If a failure is later
fixed, the entry is amended with the fix, not removed.

---

## F-001 — Cross-tenant data destruction, invisible to read-side testing

**Status:** FIXED · **Severity:** critical · **Found by:** a test, not review

In-memory repositories keyed records on the bare `id`, not
`(organisationId, id)`. Every *read* filtered by organisation afterwards,
so the isolation test suite passed and the stores looked correct.

But *writes* collided. Organisation B upserting a record whose raw id
matched one of Organisation A's **silently destroyed A's record** — no
error, no audit entry, no trace of the row that vanished.

**Why it matters more than a read leak:** a read leak exposes data. This
*destroyed* it, and destroyed it in a way that read-side isolation testing
structurally could not detect. The test that caught it was a write-side
test somebody had to think to write.

**Learned:** an isolation guarantee proven only on reads is half a
guarantee. Test the write path separately and adversarially.

**Fix:** composite `(organisationId, id)` keys via a NUL-separated key
function.

---

## F-002 — The fix for F-001 silently disabled another guard

**Status:** FIXED · **Severity:** high · **Found by:** a test

After F-001 was fixed, the audit store's append-only duplicate guard still
called `has(event.id)` — checking a *bare* id against a now
*composite-keyed* map. The lookup could never match, so the guard silently
stopped firing. Duplicate audit ids became silently acceptable.

**Learned:** a keying change is a cross-cutting change. Every call site
that constructs a key must be migrated together, and "the tests still
pass" is only reassuring if a test covers the guard you just broke. Here
one did. That was luck as much as design.

---

## F-003 — A module that could not load at all

**Status:** FIXED · **Severity:** high

`withAudit.ts` — the wrapper that makes audit coverage structural — used
TypeScript constructor parameter properties. The runtime executing the
tests (`node --experimental-strip-types`) is *strip-only*: it erases type
annotations but performs no code transformation, so parameter properties
are a hard `SyntaxError` at load time.

The module type-checked cleanly and was completely unloadable. The agent
that wrote it terminated before running its own tests, so nobody found out
until the full suite was run together for the first time.

**Learned:** `tsc --noEmit` passing does not mean the code runs. Two
different toolchains, two different answers. Run the thing.

---

## F-004 — Pipeline non-determinism beneath a provably-deterministic function

**Status:** FIXED · **Severity:** high · **Found by:** the verification audit

`scoreOpportunity()` is a pure function: `ageDays` is passed in, never read
from the clock. It has property tests proving determinism, and they pass.

One level up, `detectOpportunities()` called `Date.now()` directly to
compute that `ageDays`. So the **composed pipeline was non-deterministic**
while every unit test underneath it was green. Identical inputs produced
different scores on every run, and no scoring test could ever have caught
it — by construction.

**Learned:** determinism is a property of the *composition*, not of the
leaf function. Purity at the bottom of a call stack proves nothing about
the stack. Inject the clock at the boundary.

---

## F-005 — Two confidently-wrong adversarial findings

**Status:** REJECTED (findings were false) · **Severity:** meta

An adversarial audit reported two critical defects, both marked
"REPRODUCED":

- that the tenant key used a literal space separator, reopening F-001
- that the ingestion dedupe key joined fields with `""` (no separator)

**Both were false.** The separators are real control bytes — `U+0000` and
`0x01` respectively — which render invisibly when source is read as text.
Verified by `od -c` on the actual bytes and by executing collision tests:
no collision in either case.

**Why this is archived as a failure rather than discarded:** acting on
F-005's first finding would have meant "fixing" correct code, and the most
likely fix — swapping the separator — could have *introduced* the very
collision it claimed to find. A confidently-wrong finding is more
dangerous than a missed one, because it directs effort at working code and
carries the authority of having been "reproduced."

**Learned:** verify by executing, not by reading. Control characters are
invisible in most tooling. An adversarial reviewer needs its own
adversarial reviewer.

---

## F-006 — The system's central security claim was false

**Status:** OPEN · **Severity:** critical · **Found by:** adversarial audit, reproduced independently

TitanOS Obelisk claims, in its own source comments and in three commit
messages, that an unevidenced opportunity is *unconstructable*:
`makeOpportunity()` throws when handed empty evidence.

That guard fires **only inside that one factory function**. The actual
trust boundary — `OpportunityRepository.upsert()` — performs no validation
at all. A plain object literal with `evidenceIds: []` and
`score.evidenceConfidence: "HIGH"` hand-set:

- persists cleanly through the audited repository
- outranks genuinely evidenced opportunities
- is **not** flagged as risk in the daily briefing (which only triggers on `LOW`)
- is recorded in the audit log as an ordinary, indistinguishable write

Reproduced directly:

```
persisted unevidenced opportunity? -> true
evidenceIds: 0 | confidence: HIGH | composite: 99
```

**Why it matters:** the governing doctrine states that when the system
cannot establish legitimate authority, it must not be able to compute it
into existence. It currently can. The property is enforced at an *optional
constructor* nobody is obliged to use, while the real boundary accepts and
faithfully audits fabricated authority as legitimate.

**Unresolved.** Until `upsert()` validates, any public claim about
unconstructable unevidenced opportunities is false and must not be
published.

---

## F-007 — Secret committed to git history

**Status:** OPEN (credential rotated; history uncleaned) · **Severity:** critical

A live production secret (`INTERNAL_API_SECRET` for
`api.titanos.tech/internal/orders`) was committed in plaintext and remained
in the repository from its **first commit** onward.

- Current working tree: clean.
- Git history: present in 3 commits, including the initial commit.

The credential has been rotated; the old value now returns HTTP 401,
verified. So the live exposure is closed.

**What remains unresolved:** the repository's history demonstrably carries
secrets. One confirmed instance means the history is *unaudited*, not that
it is clean. 556 commits exist; a full-history scan has not completed.

**Learned:** removing a secret from a file does not remove it from
history. `git grep` on HEAD returning nothing is not evidence of anything.

---

## F-008 — A published site whose changes were invisible

**Status:** FIXED · **Severity:** medium · **Found by:** the site owner, repeatedly

Three consecutive passes reported "shipped and verified." Each verified by
grepping the built HTML for text strings. The bytes always shipped
correctly.

But grep proves *words* changed, not that the *page* changed. Every agent
dutifully reused existing design tokens, so the design stayed
pixel-identical while copy changed underneath. The verification method was
structurally blind to the only thing the owner was looking at.

It took the owner saying "literally 0 difference" three times before the
page was actually rendered in a browser and looked at.

**Learned:** verify the artifact a human will actually experience. A
passing check that cannot fail in the way that matters is not a check.

---

## F-009 — Validator crashed under uncaught RecursionError on deep alias chains

**Status:** FIXED · **Severity:** high · **Found by:** an adversarial test, not review

`schema/tests/test_false_negatives.py`'s alias-fan-out test threw a
20-layer self-referencing anchor chain at `validate_artifact()`. PyYAML's
own `compose()`/construct machinery is recursive, so the chain blew the
Python call stack with an uncaught `RecursionError` *before* the
validator's own `MAX_NODES`/`MAX_DEPTH` ceiling ever got to run — the
ceiling was correct but the code path meant to reach it never did.

**Why it matters:** a crash that propagates past `validate_artifact()` is
worse than a rejection — a caller with a bare `try/except ValueError`
around the call would let this exception escape as an unhandled 500,
which in many deployment shapes fails OPEN (request retried elsewhere,
error swallowed by a supervisor, etc.) rather than closed.

**Fix:** `RecursionError` is now caught explicitly around both the compose
and construct stages and converted to `MalformedYamlError` -> `INVALID`,
same as any other structural rejection.
Test: `schema/tests/test_false_negatives.py::TestYamlAliasAndAnchorTricks::test_alias_fanout_is_bounded_not_silently_expanded`.

---

## F-010 — Validator crashed on non-string YAML keys, found against the real 3,058-file corpus

**Status:** FIXED · **Severity:** medium · **Found by:** running against real data, not a synthetic test

Running `legacy/classify.py` against the actual, unmodified 3,058-file
legacy YAML corpus (not a hypothetical one) crashed with
`TypeError: '<' not supported between instances of 'bool' and 'str'`. A
real file in the corpus used a boolean-shaped key (e.g. `true:`), which
YAML permits. `sorted(set(data.keys()) - known)` then tried to compare a
`bool` against `str` keys and raised.

**Why it matters:** this is the same class as F-009 (validator failing
open via an uncaught exception) but found by exercising real-world data
rather than adversarial imagination — a reminder that the two methods
find different bugs and neither substitutes for the other.

**Fix:** two layers. (1) a new rule R-12 flags non-string keys explicitly
as `INVALID`. (2) `validate_artifact()` now wraps its entire body in a
try/except that converts *any* unforeseen exception to a structured
`INVALID` result (rule R-0), so a future unknown input shape fails closed
by construction rather than requiring the next specific bug to be
anticipated in advance.
Tests: `schema/tests/test_real_corpus_regressions.py` (5 tests, written
directly from this incident).

---

## Cross-cutting observations

1. **Nine of ten defects were found by tests, adversarial execution, or
   rendering — not by review.** Reading code found almost nothing; running
   it found nearly everything. F-009 and F-010 add the sharpest version of
   this yet: F-009 came from an adversarial test, F-010 from running
   against real, unmodified production data — two different discovery
   methods, two different real bugs, neither would have found the other.
2. **Two defects were introduced by fixes to other defects** (F-002 by
   F-001). Change is a defect source.
3. **The most dangerous findings were the confident-but-wrong ones**
   (F-005), not the missed ones.
4. **Green tests coexisted with a non-deterministic pipeline (F-004) and a
   false central security claim (F-006).** Suite-green is not
   system-correct.

---

---

# Generation 002 — 2026-08-28 → 2026-08-29

Every entry below was **reproduced before it was fixed**, and the fix was
verified by mutation (inject the defect → an independent check fires →
restore → it passes) rather than by a green suite alone. Commit hashes
are real and `git show`-verifiable.

## F-011 — Capability scored by file existence, so six empty files scored full marks

**Status:** FIXED · **Severity:** high · **Found by:** attacking the
measurement instead of trusting it

`foundation/sigil.py`'s capability dimensions awarded points on
`Path.exists()`. A scratch directory containing six EMPTY files with the
right names, plus two trivial marker strings, scored
`ORCH:10 | MEMORY:10` — byte-identical to the real repository.

**Why it matters:** `TITANOS_SIGIL_CAPABILITY_INDEX.md` requires each
dimension be "derived from a concrete, inspectable fact — never a
caller-supplied number." File existence is effectively caller-suppliable.
The index that reports what this repository can do could be satisfied by
`touch`.

**Fix:** `_defines(path, *symbols)` — the module must exist AND define
every named symbol. Deliberately not applied to markdown documents, where
existence genuinely is the signal. Two-sided proof: real repo scores
unchanged; hollow fixture collapses. A real bug in the first draft (a
`^` anchor that reported a fully-populated TestCase file as empty) was
caught by the real-repo half of that same two-sided check.
Commit `55af138`.

## F-012 — Eight empty BUILD_REPORT.md files could buy a tier

**Status:** FIXED · **Severity:** high · **Found by:** generalising F-011

Same defect class, strictly worse consequence: `_dimension_iron()` and
`check_subsystem_build_reports()` both scored on bare existence. Eight
EMPTY `BUILD_REPORT.md` files scored `IRON:10` and produced ZERO
findings — and `iron_score` is a required conjunct for tier T6 in
`compute_tier()`.

**Why it matters:** the live hourly check's own finding text already
claimed the report carried "limitations/human-decisions/next-work-cell
sections". It asserted more than it verified.

**Fix:** `has_substantive_build_report()` (heading AND body), shared by
both surfaces so they cannot drift apart. Specific section *names* were
deliberately not required — the eight real reports carry 8–12 headings
with differing names, so a fixed-name rule would encode one week's
phrasing as law. Commit `49ef042`.

## F-013 — A load-bearing safety claim enforced by nothing

**Status:** FIXED · **Severity:** high · **Found by:** asking which
execution path a capability could take, not whether it was permitted

`foundation/autonomy_loop.py` "never pushes" was claimed in FOUR places —
its module docstring, the commit message it writes, `.claude/commands/
boot.md`, and `HUMAN_DECISIONS.md` item 14, whose entire argument that
scheduling is comparatively low-risk *rests* on it. It was enforced by
ZERO tests. `_git()` forwards arbitrary arguments to `git`; the only
thing preventing a push was that no call site passed one.

**Why it matters:** this repository's own Critical Function Switch-Gate
doctrine states that a reminder is not an enforcement mechanism. A
safety property that four documents depend on was resting on the absence
of a call site.

**Fix:** `TestGitCapabilityIsStructurallyConfined` — AST-based, not
grep-based, so a mention in a docstring is not mistaken for a call. All
three bypass routes proven caught by mutation: an injected literal
`push`; a runtime-computed verb evading static analysis; a second
`subprocess.run` routing around the wrapper entirely. Commit `b943dc0`.

## F-014 — A safe-looking STOPPED result concealing a staged mutation

**Status:** FIXED · **Severity:** high · **Found by:** auditing the
trajectory instead of the terminal state

With a rejecting pre-commit hook, `run_one_cycle()` returned
`STOPPED_FIX_VERIFICATION_FAILED` — a result that reads as "nothing
happened, human must intervene" — while `git status --porcelain` showed
`M  README.md`. Column 1 means **staged**. The loop had written the fix
AND staged it, then reported a stop.

**Why it matters:** the loop invoked via `run_one_cycle()` writes no
receipt-log entry, so there was no durable record either. A human's next
unrelated `git commit` would have silently absorbed an autonomous edit
into their own authorship. Every existing test asserted the terminal
`CycleResult`; none asserted the trajectory. A safe final state is not a
safe trajectory.

**Fix, which narrowed capability rather than widening it:** `git add` was
removed entirely in favour of a pathspec commit, which leaves the index
untouched when the commit fails (verified directly: failed pathspec
commit yields ` M`, never `M `). Every post-write failure path now
restores README.md byte-for-byte by plain file write — deliberately not
`git checkout`/`restore`/`reset`, since undoing damage must not require
widening the capability set that bounds the loop. The authorized verb set
narrowed from `{status, add, commit}` to `{status, commit}`.
Mutation proof: reverting to the old shape tripped TWO independent gates
at once — F-013's capability test fired on `['add']` and the new
trajectory test fired on the dirty tree. Commit `64d1aee`.

## Measured yield — the one before/after this generation actually has

README test-count drift had been repaired **by hand 7 times** across this
repository's real git history, three of them in a single session, while a
built, tested, authorized actuator for exactly that repair sat unreached
because no protocol step named it.

*How to re-derive that number, stated precisely because a vaguer version
of this line was itself already drifting when written:*
`git log -p --follow README.md | grep -c "^+.*tests across"` returns
**9** as of commit `6adba6e` — 7 hand edits plus the 2 autonomous ones
below. Subtract the commits whose SUBJECT begins `[autonomy-loop]`:
`git log --oneline | grep -c "\\[autonomy-loop\\]"` returns **2**.
(Use `--oneline | grep`, not `git log --grep`, which also matches message
bodies and returns 3 here — commit `3b697e3` discusses the actuator
without being one of its commits. That off-by-one was found while
writing this line, which is the third time in this generation that a
stated verification method disagreed with the number it was supposed to
support.) Both integers move as the file changes; the method is the
durable part.

After the actuator was routed into `.claude/commands/boot.md` (commit
`3b697e3`), it fired in production twice — commits `474cd2a` and
`6adba6e` — each time recomputing the real count, rewriting only the
verbatim span, re-running the detector to verify, and committing itself.
Hand edits since routing: **zero**.

This is a within-repository measurement, not a claim about other
systems. It is recorded because the before-count (7) and after-count (0)
are both independently recoverable from git history by anyone.

## Cross-cutting observations — Generation 002

5. **Four of four defects this generation were defects in
   SELF-MEASUREMENT, not in features.** F-011 and F-012 were claims about
   capability that the measurement did not check; F-013 was a safety
   claim with no enforcement; F-014 was a result that misreported what
   the trajectory had done. Generation 001's lesson was "running it finds
   what reading it misses." Generation 002's is narrower and sharper:
   **the thing most likely to be wrong is what the system says about
   itself.**
6. **Two independent gates caught one regression** (F-014's mutation
   tripped F-013's capability test as well). Redundant enforcement is
   not redundant.
7. **Every fix this generation either preserved or reduced authority.**
   F-014 removed a git verb. None added a capability, and the one
   candidate that would have (scheduling the loop unattended) was
   recorded as an open human decision instead of taken.

---

*Entries are appended, never removed. A fixed failure keeps its entry.*

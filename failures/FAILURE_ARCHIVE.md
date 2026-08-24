# TitanOS — Failure Archive

**Generation:** 001
**Status:** OPEN — this archive is never closed
**Scope:** failures observed in the TitanOS build sessions of 2026-08-19 → 2026-08-24

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

*Entries are appended, never removed. A fixed failure keeps its entry.*

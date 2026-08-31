# EXP-001 — What this does NOT prove

## Sample size

28 documents: 16 READMEs, 10 security advisories, 2 derived edge cases.
That is a small corpus. Twelve claims were extracted from it in total, so
every statement about classification behaviour rests on twelve data
points. No rate, ratio or percentage in `FINDINGS.md` should be treated as
an estimate of anything.

## Selection bias

The selection rule was fixed before fetching and the exclusions are
recorded, which prevents *post-hoc* cherry-picking. It does not make the
corpus representative. The candidates are well-known, heavily-reviewed,
permissively-licensed projects — the most carefully written documents on
GitHub, not typical ones. Their claims are largely accurate, so the
corpus is biased *toward* the system looking well-behaved.

The licence filter compounds this: it excluded 6 of 25 candidates, and
what survives is not a random sample of open source.

## Public READMEs are not adversarial actors

This is the most important limitation. **Nothing in this corpus was trying
to defeat anything.** A README that says "battle-tested" is marketing, not
an attack. No document attempted prompt injection, provenance forgery,
homoglyph substitution, schema confusion, or authority spoofing.

A pass here does not generalise to hostile input. It generalises to
approximately nothing about hostile input. The single document that
tripped `looks_like_injection` did so because READMEs contain installation
imperatives, not because anyone tried.

## What Arm B is and is not

Arm B wraps real content hashes in a valid schema envelope so the gates
behind the schema check can run at all. That is a probe of the gate chain,
not a simulation of an attack. Finding 2 shows the chain grants authority
on an unverified boolean; it does **not** show that anyone can supply that
boolean, because nothing calls `evaluate()` in production. Reading Finding
2 as an exploit would be overclaiming, and the finding says so.

## Two documents are synthetic

`DERIVED:truncated` and `DERIVED:empty` are constructed, labelled as
such, and are not evidence about real-world documents. They exist because
the payload requires a malformed case and fabricating a "real" one would
have been dishonest.

## Not reproducible byte-for-byte

Upstream READMEs and the advisory feed change. Re-running Arm A will
produce different `content_hash` values and possibly different exclusions
(licences get relicensed, default branches get renamed). Per-document
hashes are what make any individual result checkable. Arm B is
deterministic given Arm A's output.

## The claim extractor is blunt

A regex over capability-marker words, chosen because a better extractor
would have been new capability and this cycle forbids that. It will have
missed claims that avoid those words and caught sentences that merely
contain them. Twelve claims from 28 documents is a property of the regex
as much as of the corpus.

## One run, one machine, one moment

No repetition, no second observer, no cross-checking against a different
implementation. Network conditions, GitHub's API state and upstream
content at one point in time.

## The receipt proves what happened, not what is true

`RECEIPT.json` records that this run occurred, with hashes of its inputs
and outputs. It is not evidence that any claim in the corpus is true, that
any finding is correctly diagnosed, or that the pipeline is sound.

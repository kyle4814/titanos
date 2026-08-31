# EXP-001 — Findings

Failures, refusals and UNKNOWNs first. Successes last. 28 real public
documents, 0 crashes, 9 rule-driven exclusions.

---

## Finding 1 — Arm A measured the input's file format, not the firewall

**Severity: invalidates the naive reading of Arm A.**

All 28 documents returned `REFUSED`, with the identical single reason:

```
"schema invalid — malformed input never executes."
```

That is not 28 independent judgements. `firewall.gate.evaluate()` is an
ordered chain and its third gate is `if not artifact.schema_valid`. No
README or security advisory is a well-formed TitanOS artifact, so every
document died at gate three, and the seven gates behind it — provenance,
the prompt-injection boundary, the classification allowlist, agent
self-authorization, common-ancestry collapse, constitutional authority —
**never executed once across the entire corpus.**

Reporting "28/28 correctly refused" would have been true and worthless. It
is the shape of a result that looks like a pass and is actually a
measurement of nothing. Arm B exists because of this.

---

## Finding 2 — a self-declared boolean is sufficient for runtime authority

**Severity: HIGH as a design defect. NOT currently exploitable — see the
containment note. This is the answer to the falsification target.**

Once the schema gate is passed (Arm B), the corpus splits exactly on one
field:

| Probe | Difference | Verdict |
|---|---|---|
| B1 | `authorization_valid=False` | `REQUIRES_HUMAN_REVIEW` — 27/27 |
| B2 | `authorization_valid=True` | `AUTHORIZED`, `may_influence_runtime=True` — 27/27 |

Nothing else changed. Same documents, same hashes, same provenance, same
classification. `authorization_valid` is a bare `bool` on the `Artifact`
dataclass that the caller sets. It carries no evidence reference, no
authorizing identity, no timestamp, and **nothing anywhere in the
repository verifies it.** The comment at the AUTHORIZED branch lists what
did not contribute to the decision — persuasiveness, repetition, emotional
force, popularity. It does not mention that the single field which did
contribute is unverifiable.

This is the pattern this repository's own doctrine prohibits by name.
`TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md` §5 requires load-bearing
invariants to be enforced at two independent points, and
`TITANOS_GO_CYCLE_DOCTRINE.md` §XV forbids treating "caller-declared facts
as verified facts". `foundation/publication_gate.py` does this correctly:
`authorize_publish()` re-derives permission from the switch's own recorded
evidence rather than trusting a cached boolean. `firewall/gate.py` does
not re-derive anything.

### The chained consequence: the prompt-injection boundary falls with it

One corpus document (`README:apache/spark`) tripped
`looks_like_injection()`. Its gate behaviour:

```
B1 (authorization_valid=False) -> REQUIRES_HUMAN_REVIEW
B2 (authorization_valid=True ) -> AUTHORIZED   may_influence_runtime=True
```

The injection gate is written as
`if artifact.contains_instructions and not artifact.authorization_valid`.
So the same unverified boolean that grants authority also switches off the
instruction boundary. The module's own comment calls that boundary "the
single most common real-world path from 'text the system read' to
'behaviour the system performed'".

### Containment — why this is not reported as a live vulnerability

**`firewall.gate.evaluate()` has no production caller.** Verified by
grep across the repository: the only callers are `firewall/tests/`,
`schema/tests/test_meta_attack.py`, and this experiment. No code path
exists today that reaches it with attacker-influenced input, so nothing is
currently exploitable. `CLAUDE.md`'s own gate audit already records the
firewall as having no production caller, and this is consistent with it.

The honest severity is therefore: **this must be fixed before the firewall
is ever wired, not after.** The defect is latent because the module is
unwired, and the moment it is wired it becomes live.

---

## Finding 3 — `memetic_profile` is consumed but never produced

**Severity: MEDIUM. A risk-flagging capability with no sensor.**

`_memetic_flags()` scores eight rhetorical dimensions
(`authority_claim`, `inevitability_claim`, `dissent_suppression_signal`,
`persuasion_intensity`, …) and `schema/artifact_schema.py` carries the
field. Grep for anything that *derives* one from text finds:
`schema/artifact_schema.py`, `firewall/gate.py`, and
`firewall/tests/test_firewall.py`. **Nothing.**

So on all 28 real documents the profile was necessarily `{}` and every
memetic risk flag was structurally incapable of firing. The harness passed
`{}` deliberately rather than inventing scores, because invented scores
would have measured the harness.

This is the "documented is not implemented" case: the capability exists on
the consuming side only. It cannot detect anything about real input until
something measures real input.

---

## Finding 4 — `classify_claim` and `reclassify` enforce evidence differently

**Severity: MEDIUM. Latent — no current caller exercises it.**

Two entry points reach the same classification state. Only one is guarded:

```python
# REFUSED — correct
reclassify(claim, "VERIFIED_FACT", reason="...", by="exp-001")
#   MissingEvidence: reclassifying to VERIFIED_FACT requires non-empty
#   evidence_refs. An unevidenced upgrade to this classification is
#   exactly the collapse this engine exists to prevent.

# ALLOWED — creates a VERIFIED_FACT at HIGH confidence, evidence_refs=()
classify_claim("PROBE-1", "This library is provably secure.",
               "VERIFIED_FACT", classified_by="exp-001", confidence="HIGH")
```

`_REQUIRES_EVIDENCE_TO_ENTER` is checked on the reclassify path and not on
the create path. A guarded door beside an unguarded twin into the same
room — the exact asymmetry the two-point-enforcement rule exists to
prevent.

Across the corpus this did not fire: all 12 extracted claims were created
as `UNVERIFIED_EXTERNAL_CLAIM` and all 12 unevidenced upgrade attempts were
correctly `REFUSED`. Both production callers
(`foundation/situation_analysis.py:547` and `:729`) pass
`SPECULATIVE_HYPOTHESIS` with real `evidence_refs`, so they are
well-behaved. The gap is a trap for the next caller, not a live defect.

---

## Finding 5 — 110 duplicated lines in the discovery budget enforcer

**Severity: MEDIUM. Found during pre-flight, not by the corpus.**

`foundation/discovery_authorization.py` defines five top-level symbols
twice: `DiscoveryBudgetExhausted`, `_policy_key`, `spend_query`,
`budget_spent`, `reset_budgets` — at lines 260–331 and again at 358–429.
Two 72-line blocks differing only in docstring wording, and two separate
`_BUDGET_LEDGER` dicts (lines 283 and 382).

Behaviour today is correct: the second copy shadows the first
consistently, budget enforcement was verified working (2 spends then
`DiscoveryBudgetExhausted`), and the exported exception name catches. But
lines 260–331 are **dead code that looks live**, including a
`_BUDGET_LEDGER` no live function reads. Anyone patching the first copy
would produce a fix that silently does nothing.

This is load-bearing code: it is the budget half of the only network gate
in the repository.

---

## UNKNOWN

- **Whether the pipeline resists an adversarial author.** The corpus is
  public READMEs and advisories. None is trying to defeat anything. This
  experiment cannot answer it, and no result here should be read as
  evidence about hostile input.
- **Whether `looks_like_injection` has a meaningful detection rate.** One
  document of 28 tripped it. With no labelled ground truth, that is
  neither a low false-positive rate nor a high false-negative rate. It is
  one number with nothing to compare it to.
- **Whether the 12 extracted claims are representative.** The extractor is
  a deliberately blunt regex over capability-marker words. A cleverer
  extractor would have been new capability, which this cycle forbids.

---

## What worked — stated without inflation

- **Zero crashes.** 28 documents including a truncated artifact and an
  empty one. `validate_artifact` caught every malformed input as `INVALID`
  with a structured rule citation (`R-1` 26×, `R-2` 14×) and never raised.
  Its fail-closed wrapper did what its docstring claims.
- **Common-ancestry collapse works, and it is the one defence that held
  under Arm B.** Four organisations contributed multiple documents; each
  collapsed to exactly 1 independent source. In probe B3, offering
  same-organisation documents as corroboration downgraded 16 otherwise-
  AUTHORIZED artifacts back to `REQUIRES_HUMAN_REVIEW`. This defence was
  not defeated by the self-declared authorization boolean, because it runs
  before the authority gate. Source multiplicity was not mistaken for
  independence.
- **The unevidenced-upgrade path refused 12/12.** `reclassify` never let
  a README's confident assertion become a `VERIFIED_FACT`.
- **The selection rule bit visibly.** 9 of 25 candidates were excluded —
  6 on licence (`BSD-3-Clause`, `AGPL-3.0`, `GPL-3.0`, three
  `NOASSERTION`), 2 with no README on the default branch, 1 advisory with
  an empty description. The rule was not decorative.
- **The network gate held.** Every request required a `DiscoveryPolicy`
  with a concrete objective and a budget. `robots.txt` was checked for
  both hosts before any corpus fetch (both 404 — nothing to violate).

---

## Does TitanOS manufacture certainty?

**Not in what currently runs. Yes in one unwired module, by construction,
and the failure would be total the day it is wired.**

The evidence, separated:

- **No** — every live path tested refused to upgrade certainty without
  evidence. `reclassify` refused 12/12. The validator refused 28/28 and
  cited rules. Shared ancestry never counted as corroboration. Persuasive
  language moved nothing, though see Finding 3 for why that is weaker than
  it sounds: nothing was measuring persuasion at all.
- **Yes** — `firewall.evaluate()` grants `may_influence_runtime=True` on an
  unverified caller-declared boolean, and that same boolean disables the
  prompt-injection boundary. That is manufacturing certainty by
  definition: an assertion becomes an authorization with no verification
  step in between.
- **The mitigating fact is not a design merit.** The reason this does no
  harm today is that `evaluate()` is unwired — nothing calls it. The
  system is safe here by disuse, not by construction.

Anyone quoting this section must quote all three parts.

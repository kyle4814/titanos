# Foundation Switch — Build Report

Built 2026-08-25 at `/home/tech2/cosmic-library/foundation/`. 2 parallel
Sonnet agents for the two genuinely-new, independent components
(`flow_switch.py`, `reality_yield_ledger.py`); `switch_hardener.py` and
the module mapping (`MAPPING.md`) built directly, since both required
close judgment about which of the directive's 16 modules duplicate
existing code — exactly the kind of call this session's discipline says
shouldn't be delegated blind.

## What this module is, precisely

Not a 16-module system. Three small, independently-tested mechanisms plus
an honest map of where the other 13 named modules stand — 6 already exist
elsewhere in this repo, 7 remain genuinely unbuilt. See `MAPPING.md` for
the full breakdown and reasoning.

**2026-08-25, same-day addendum:** `publication_gate.py` added under
`TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md` — the first of that doctrine's
§2 critical-function list (publication / private-public boundary
crossing) to actually get hard-gated code rather than remaining a
reminder. 22 tests, including a direct proof that a caller cannot bypass
`authorize_publish()` by hand-constructing a `PublicationDecision` with
`action_permitted=True` — the function only ever re-derives permission
from the switch's own declared evidence. The other 18 functions named in
that doctrine's §2 list (code execution, credential access, deletion,
deployment, ...) remain ungated as code — named here so they're not
mistaken for closed.

## Files created

| Component | Files | Tests |
|---|---|---|
| CT_141 Flow Switch (panic detection + mode state machine) | `foundation/flow_switch.py` | 45 |
| Switch Hardener (10-gate check + thin `kpm.promotion` reuse) | `foundation/switch_hardener.py` | 16 |
| Reality Yield Ledger | `foundation/reality_yield_ledger.py` | 34 |
| Module mapping | `foundation/MAPPING.md` | — |
| Situation Analysis — Monk/Demonblade pass, bottleneck/tension/off-ramp hypotheses, MAGL bridge | `foundation/situation_analysis.py` | see `foundation/tests/test_situation_analysis*.py`, `test_bottleneck_hypotheses.py`, `test_tension_and_offramp.py` |
| Historical Findings bridge (RPA validation-bypass finding → `ContradictionRegistry`, writer-to-reader only, no promotion call) | `foundation/historical_findings.py` | see `foundation/tests/test_historical_findings.py` |

**2026-08-26 addendum:** `historical_findings.py` is a one-way writer
into `ContradictionRegistry` — it deliberately does not call
`PromotionStore.promote()` and is not wired to `demonblade_pass()`'s
own `contradiction_candidates` output (that composition was attacked
and rejected as semantic laundering — single-sided unsupported-claim
findings are not the two-claims-cannot-both-be-true collisions
`ContradictionRegistry` itself is defined around). See the module's own
docstring for the full reasoning, and `PARETO_FRONTIER.md`'s
`FRONTIER-SITUATION-ANALYSIS-SLICE`/`FRONTIER-WORLD-PING-SLICE`/
`FRONTIER-TECTONIC-TENSION-SLICE`/`FRONTIER-CONTRADICTION-REGISTRY-WRITER`
entries for the full build history. This table's original entries below
predate this addendum and are otherwise unchanged.

**95 new tests, 95 passing.** Full-repo regression in this same pass:
**786 tests total across the whole repository, 786 passing, 0 failing**
(95 new + 691 pre-existing re-verified). This count is now stale — the
repository's own root `README.md` and `PARETO_FRONTIER.md` are the
places to check for the current total, not this line; re-run
`python3 -m unittest discover -s foundation -p "test_*.py"` rather than
trusting either number.

## The load-bearing properties, each actually tested

- **`PANIC = information_velocity > verification_velocity`** — both edge
  cases tested explicitly (zero-verification-with-positive-information IS
  panic; zero-zero is NOT panic, since nothing is happening).
- **`SIGNAL_COLLAPSE` has no panic-based exit and no direct edge back to
  `NORMAL`/`HIGH_COMPLEXITY`** — enforced at TWO independent points: the
  `MODE_TRANSITIONS` table (absence of the edge, same discipline as
  `firewall/quarantine.py`), and `recommend_transition()` itself, so a
  caller can't route around the store's enforcement by following the
  recommendation function instead of calling `.transition()`.
- **The hardening gates cannot be bypassed by good news elsewhere** — a
  candidate lesson with 9 passing gates and 1 failing gate (duplication,
  human-agency, or any other) is refused by `harden()` outright; the
  underlying record stays at `TESTED`, verified directly, not inferred.
- **A hardened switch cannot be self-reviewed** — inherited unchanged from
  `kpm.promotion.state_machine.SelfPromotionForbidden`, not
  re-implemented, tested explicitly to confirm the inheritance actually
  works through the wrapper.
- **Reality yield rejects forward-looking evidence regardless of how
  large or impressive the claimed value is** — the load-bearing test
  mirrors this session's other "persuasiveness doesn't change the
  outcome" tests (`schema/tests/test_meta_attack.py`,
  `firewall/tests/test_firewall.py`): an entry with large
  `VERIFIED_BENEFIT`/`INFORMATION_GAIN` numbers but evidence text reading
  "this will generate significant value once deployed at scale" is
  rejected on the evidence text alone.
- **The ledger records bad news as readily as good news** — a deeply
  negative net yield is accepted and stored, recommending
  `THROTTLE_OR_TERMINATE`; nothing in `record()` blocks a negative
  assessment from being written.

## Known limitations

- `switch_hardener.run_hardening_gates()` takes every gate answer as a
  caller-declared boolean/string — it cannot itself verify provenance,
  generate a red-team argument, or detect a duplicate. This is the same
  boundary every validator in this codebase holds (checks the SHAPE and
  CONSISTENCY of declared fields, does not manufacture them) but it's
  worth restating here because the whole point of this module is
  epistemic rigor, and a caller who fabricates "PASS" answers defeats it
  completely. The module's own docstring says this plainly.
- 7 of the directive's 16 named modules are genuinely unbuilt (Oracle
  scenario engine, 999 state-space mapper, continuity seed as repo
  artifact, defusal router's specific 11-step sequence, low-regret
  engine, a dedicated pathway-ledger query store, and a regression
  engine that automatically re-tests hardened switches against new
  contradicting evidence). See `MAPPING.md`.
- `flow_switch.py`'s `PanicSample` takes velocity numbers as
  caller-supplied floats — nothing in this module measures actual
  information/verification throughput anywhere in this codebase. The
  panic detector is correct given its inputs; nothing currently feeds it
  real inputs.

## Unresolved contradictions

None found.

## Security gaps

Same standing gaps as every prior session (single-reviewer promotion
authority, unauthenticated `reviewed_by`, no cryptographic signature
verification) — `switch_hardener.py` inherits these from
`kpm.promotion.state_machine`, not new to this build.

## Human decisions required

1. Whether `MAGL_007_CONTINUITY_SEED` should become a versioned artifact
   inside this repository, given the assistant's own memory system
   already serves this purpose operationally — a real design question
   about where that responsibility should live, not decided here.
2. Whether the 7 genuinely-unbuilt modules are worth building at all, or
   whether the 3 built this session plus the 6 mapped ones already
   constitute a sufficient foundation — the directive's own closing rule
   ("smallest foundation that can safely grow") argues for waiting until
   a concrete need surfaces rather than building speculatively.
3. All standing decisions from prior sessions remain open: F-007 (titan
   repo git history), the 3,058-file legacy corpus review question,
   four-eyes review for release across every promotion/quarantine store
   in this repository.

## Next smallest work cell

Wire `flow_switch.PanicSample` to something that actually measures real
information/verification velocity — even a crude proxy (e.g. counting
claims made vs. tests run in a given work session) would let the panic
detector observe real conditions instead of only caller-supplied
hypotheticals, and would be the first genuinely LIVE component in this
otherwise entirely schema/ledger/gate-shaped foundation.

---

## Addendum 2026-08-30 — the receipt / value / offer trio

Three modules, built across two sessions, forming one boundary: what an
investigation may claim, what a number may claim, and what may be sold.

| Module | Refuses | Tests |
|---|---|---|
| `receipt.py` | `DEFECT_ADMITTED` without a PROVEN claim; without a named beneficiary; a PROVEN claim with empty evidence; any price field | 25 |
| `value_model.py` | a figure on a `NOT_MEASURED` input; a product containing an unmeasured factor; an aggregate stronger than its weakest input; an undeclared factor | 30 |
| `business_receipt.py` | an authored verdict/confidence/offer; a bare figure as impact; two sources of truth for one field | 19 |

**The one-way law, enforced structurally rather than promised.**
`value_model` does not import `receipt`; `receipt` does not know
`value_model` exists. `derive_business_receipt()` is the only meeting
point, and it has no parameter for verdict, confidence, offer, next
action, or value state — a test enumerates the signature and asserts
their absence. Two tests fix the direction from both ends: a $900,000
fully-`MEASURED` exposure on a receipt with no beneficiary still returns
`NO_REMEDIATION_OFFER_RECOMMENDED`, and `VALUE: NOT MEASURED` on a proven
defect with a named beneficiary still returns `REQUEST_REMEDIATION`.

**Deliberately not merged into `crystal.py`.** A Crystal is an internal
epistemic note; a Receipt is customer-facing with a beneficiary test and
an offer gate. Merging would put commercial fields on the internal
record — the exact contamination the firewall exists to prevent. A
Receipt may cite a crystal id in `evidence_refs`.

**Claim status is not `ALL_CLASSIFICATIONS`.** The KPM vocabulary answers
"what kind of knowledge is this"; `CLAIM_STATUSES` answers "how strongly
did this investigation establish this claim". Orthogonal axes; reusing
the KPM enum would have forced every claim into a category that does not
describe evidential strength.

### Verification

Mutation battery, four mutations, all convicted, all restored and
md5-verified: deleting the `NOT_MEASURED`-carries-a-figure refusal (1
failure); computing the product despite a blocked factor (5 errors);
letting the strongest rather than weakest input govern (5 failures);
allowing both impact paths at once (1 failure). Full foundation suite
1119/1119; all 10 subsystem suites green; `pulse_sweep` raw findings 0.

**A restore that appeared to fail, and did not.** The first battery
reported failures after restoring byte-identical files. Cause: stale
`__pycache__` — this filesystem's mtime granularity let CPython reuse
mutant bytecode against restored source. Recorded because it is a live
trap for any future mutation work here: **clear `__pycache__` between
mutation and restore**, and never trust a post-restore green (or red)
without it. The battery was re-run with cache clearing; one earlier
mutation's failure count was inflated by the contamination (reported 6,
true count 1) and is corrected above.

### Limitations

- No `VALIDATED_REALIZED` capture path exists. The state is in the
  vocabulary and honoured by the arithmetic, but nothing observes value
  after a remediation, so no receipt can legitimately carry it yet.
- The derivation supports products only. Sums and quotients are not
  built and should not be added speculatively.
- The free-text impact path leaves `value_state` at `NOT_MEASURED` even
  for genuine prose measurements. Deliberate asymmetry — unstructured
  text carries no checkable source state — but it will read as a
  contradiction to anyone who skims the two fields together.

### Next smallest work cell

Nothing here has met a real customer. The trio's honesty is proven
against adversarial tests, not against anyone's willingness to pay for a
receipt that says `NO_DEFECT`. That is the open question, and it cannot
be closed inside this repository.

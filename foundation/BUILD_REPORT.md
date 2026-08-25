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

**95 new tests, 95 passing.** Full-repo regression in this same pass:
**786 tests total across the whole repository, 786 passing, 0 failing**
(95 new + 691 pre-existing re-verified).

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

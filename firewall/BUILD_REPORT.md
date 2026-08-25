# Firewall — Build Report

Retroactive report — written 2026-08-25 in response to
`foundation/sentinel.py::pulse_sweep()` repeatedly flagging this
subsystem as missing the audit-trail document every sibling subsystem
carries (`PARETO_FRONTIER.md` FRONTIER-011).

## What this subsystem is

The Epistemic Firewall: the rejection engine governing what may reach
runtime policy, plus the two mechanisms that give its verdicts real
teeth — a quarantine state machine, and dissent preservation so the
firewall cannot degrade into a censor.

## Files

| Component | File | Purpose |
|---|---|---|
| Rejection engine | `firewall/gate.py` | `evaluate()` — narrower than "is this true"; governs only what may acquire runtime authority. An artifact refused here stays readable and archived, it simply cannot govern. |
| Quarantine store | `firewall/quarantine.py` | `QuarantineStore` — closes the gap between a `QUARANTINED` verdict (a claim) and an actual contamination state machine (a mechanism); the pattern every later append-only, no-delete store in this repository (`kpm/promotion/state_machine.py`, `foundation/reality_yield_ledger.py`, `foundation/crystal.py`, ...) copies. |
| Dissent preservation | `firewall/dissent.py` | Prevents the mirror-image failure mode to over-permissiveness: disagreement being mislabelled as contamination. |

## Tests

`firewall/` (via `python3 -m unittest discover -s firewall -p
"test_*.py"`): 36 tests, passing as of 2026-08-25.

## Design pattern this subsystem originated

The "verdict is a claim, a store is a mechanism" distinction —
explicitly named here as closing the same shape as F-006 (an earlier
session found doctrine asserting an invariant that only an *optional*
constructor argument enforced) one layer up. Every later
promotion/quarantine-shaped store in this repository (`kpm/`,
`foundation/`) follows the same two properties this module established:
an explicit transition table with illegal edges simply absent, and no
delete surface.

## Known limitations

Same standing security gaps as every store of this shape elsewhere in
the repository: single-reviewer authority, unauthenticated
`reviewed_by`, no cryptographic signature verification — named
repeatedly across `foundation/BUILD_REPORT.md` and others as an
unresolved, repository-wide item, not unique to this subsystem.

## Human decisions required

Four-eyes review policy for release across every promotion/quarantine
store in this repository — a standing, repository-wide open item
already tracked in `HUMAN_DECISIONS.md`, not specific to this
subsystem.

## Next smallest work cell

None currently identified against this subsystem specifically — every
later subsystem that needed quarantine or gate behaviour has reused
these modules rather than finding a gap in them.

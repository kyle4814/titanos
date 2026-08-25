# Next Move

Single concrete candidate for the next `GO`/`/go` cycle. Updated at the
end of every material cycle — see `TITANOS_LIVING_PARETO_FRONTIER_
ARCHITECTURE.md` §XVI/§XVII. Not a queue; exactly one recommendation at a
time. Superseded entries move to `PARETO_FRONTIER.md`'s status field
rather than being deleted here.

---

**As of 2026-08-25, cycle following the FRONTIER-011 close-out:**

Unchanged recommendation below — this cycle closed FRONTIER-011 (the
one item three consecutive cycles had already identified as the
highest-evidence, zero-risk documented gap but deferred each time in
favour of other frontier work): wrote `BUILD_REPORT.md` for `schema/`,
`firewall/`, `narrative/`, verified by `pulse_sweep()` dropping from 3
findings to 0. Also fixed one stale test (`test_sentinel.py`'s
real-repo assertion had pinned itself to the very gap this cycle closed
— replaced with a synthetic-repo test that proves the check's detection
behaviour without going stale as this repository's own state improves).
Same independent-audits-don't-displace-each-other's-recommendation
pattern as every prior cycle.


## Recommended: FRONTIER-001 — Reusable secret/credential scanner

Unchanged from the prior cycle's recommendation — still open, still the
highest-evidence candidate (it would have auto-caught the
`legacy/manifests/*.json` path-leakage finding), still not yet built.
This cycle built `FRONTIER-000` (narrative atom schema) instead, because
the incoming directive (`TITANOS_AKASHIC_NARRATIVE_ENGINE.md`) explicitly
asked for its own single highest-lever missing connection audited fresh,
and the audit's answer for THAT doctrine's scope was the atom schema, not
the scanner — the two audits are independent, and neither displaces the
other's standing recommendation. See `PARETO_FRONTIER.md`'s full
reasoning for both.

**Not yet authorized to build.**

## Also on the frontier, not recommended this cycle

FRONTIER-002 (permission_request→GateInput adapter), FRONTIER-003 (CI
workflow, blocked), FRONTIER-004 (Narrative Atom Store — the state
machine driver for the schema just built), FRONTIER-005 (Five-Record
views / Gold Ledger / Isomorphism contract — blocked on FRONTIER-004 and
on real narrative content actually being ingested, which hasn't happened
yet). See `PARETO_FRONTIER.md`.

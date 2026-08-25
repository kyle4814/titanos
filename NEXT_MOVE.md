# Next Move

Single concrete candidate for the next `GO`/`/go` cycle. Updated at the
end of every material cycle — see `TITANOS_LIVING_PARETO_FRONTIER_
ARCHITECTURE.md` §XVI/§XVII. Not a queue; exactly one recommendation at a
time. Superseded entries move to `PARETO_FRONTIER.md`'s status field
rather than being deleted here.

---

**As of 2026-08-25, cycle following the Queue<->Worker seam build:**

Unchanged recommendation below — this cycle built FRONTIER-013 (the
explicit `foundation/queue_worker_adapter.py` bridge between
`task_queue.run()` and `Layer0Worker.run()`), closing the seam named by
`MAGL_FND_003` without modifying either existing, already-tested module.
Found and fixed one real pre-existing bug along the way (`eligible_
tasks()` treated unknown dependencies as vacuously satisfied instead of
fail-closed) — caught by writing the seam test matrix, not by this
cycle's own new code. Reality pass via `sentinel.pulse_sweep()` found
zero new issues. Same independent-audits-don't-displace-each-other's-
recommendation pattern as every prior cycle.


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

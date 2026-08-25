# Next Move

Single concrete candidate for the next `GO`/`/go` cycle. Updated at the
end of every material cycle — see `TITANOS_LIVING_PARETO_FRONTIER_
ARCHITECTURE.md` §XVI/§XVII. Not a queue; exactly one recommendation at a
time. Superseded entries move to `PARETO_FRONTIER.md`'s status field
rather than being deleted here.

---

**As of 2026-08-25, cycle following the permission_request adapter build:**
FRONTIER-002 is now BUILT — `taal/gate/permission_request_adapter.py::
permission_request_to_gate_input()`, 15 tests, closing `taal/
BUILD_REPORT.md`'s named next-work-cell. Real seam finding: the identity/
authority `GateInput` fields have no corresponding `permission_request`
field by design — a request document cannot self-assert its own
verification, mirroring the schema's existing `self_authorized`
rejection rule one layer up.

## Recommended: FRONTIER-004 — Narrative Atom Store (state machine driver)

Now the highest-evidence open candidate: LOW effort, LOW risk, the
pattern to copy already exists three times in this repository
(`kpm/promotion/state_machine.py`, `foundation/flow_switch.py`,
`firewall/quarantine.py`). See `PARETO_FRONTIER.md` for full reasoning.

## Also on the frontier, not recommended this cycle

FRONTIER-003 (CI workflow, blocked on GitHub remote), FRONTIER-005
(Five-Record views / Gold Ledger, blocked on FRONTIER-004 and real
ingested content), FRONTIER-008 (per-subsystem seed/manifest packaging,
blocked on GitHub remote), FRONTIER-009 (Boot Context Selector, effort
MEDIUM-HIGH with an uncertain net win). See `PARETO_FRONTIER.md`.

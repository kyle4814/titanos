# Next Move

Single concrete candidate for the next `GO`/`/go` cycle. Updated at the
end of every material cycle — see `TITANOS_LIVING_PARETO_FRONTIER_
ARCHITECTURE.md` §XVI/§XVII. Not a queue; exactly one recommendation at a
time. Superseded entries move to `PARETO_FRONTIER.md`'s status field
rather than being deleted here.

---

**As of 2026-08-25, cycle following the secret scanner build:**

FRONTIER-001 is now BUILT — `foundation/secret_scanner.py::scan()`,
after 7 consecutive cycles as the standing highest-evidence
recommendation. Wired directly to `foundation/publication_gate.py`'s
existing `secret_scan_evidence` field via `ScanReport.
to_evidence_string()`. Real check against this repository: 0
HIGH-confidence findings.

## Recommended: FRONTIER-002 — `permission_request` → `GateInput` adapter

The next-highest standing candidate now that FRONTIER-001 is closed —
see `PARETO_FRONTIER.md` for full reasoning (closes the third instance
of the "proven seam, not yet a pipeline" pattern named in
`taal/BUILD_REPORT.md`).


## Also on the frontier, not recommended this cycle

FRONTIER-003 (CI workflow, blocked on GitHub remote), FRONTIER-004
(Narrative Atom Store), FRONTIER-005 (Five-Record views / Gold Ledger,
blocked on FRONTIER-004 and real ingested content), FRONTIER-008
(per-subsystem seed/manifest packaging, blocked on GitHub remote),
FRONTIER-009 (Boot Context Selector). See `PARETO_FRONTIER.md` for full
reasoning on each.

# Next Move

Single concrete candidate for the next `GO`/`/go` cycle. Updated at the
end of every material cycle — see `TITANOS_LIVING_PARETO_FRONTIER_
ARCHITECTURE.md` §XVI/§XVII. Not a queue; exactly one recommendation at a
time. Superseded entries move to `PARETO_FRONTIER.md`'s status field
rather than being deleted here.

---

**As of 2026-08-25, cycle following `PARETO_FRONTIER.md`'s creation:**

## Recommended: FRONTIER-001 — Reusable secret/credential scanner

**Why this one, not FRONTIER-002:** both are open, both are low-risk and
fully reversible, but FRONTIER-001 has a real, already-proven use (it
would have caught the `legacy/manifests/*.json` path-leakage finding
automatically instead of by an ad hoc grep pass) and plugs directly into
an existing gate (`publication_gate.PublicationSwitch.secret_scan_evidence`).
FRONTIER-002 is real but currently has zero evidence any workload has
actually needed it yet — building it now would be justified by
completeness, not by a demonstrated gap. Per the Next-Lever Sequencer:
prefer the move with real evidence behind it.

**Contract, if built:**
- `foundation/secret_scanner.py::scan(paths: Iterable[Path]) -> ScanReport`
- Reuses the exact pattern set already exercised for real during the
  publication-readiness pass (see `legacy/DECISION_PACKET.md`'s
  redaction note and commit `9fd2d74`) — not a new invention, a
  formalization of something already proven to work.
- `ScanReport` structured (never bare bool), listing every hit with
  file/line/pattern-matched (never the matched secret itself in the
  report — report the finding, not the payload).
- Test plan: known-good fixture files (clean), known-bad fixture files
  (each pattern class deliberately present), and a regression test
  re-running the scan against this actual repository's current tracked
  files, asserting zero hits (mirrors the real scan already run once).

**Not yet authorized to build** — this file records the recommendation;
building it is the next `GO`/`/go`, not this cycle.

## Also on the frontier, not recommended this cycle

See `PARETO_FRONTIER.md` for FRONTIER-002 (permission_request→GateInput
adapter, low urgency) and FRONTIER-003 (CI workflow, blocked on
`HUMAN_DECISIONS.md` item 1).

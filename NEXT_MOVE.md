# Next Move

Single concrete candidate for the next `GO`/`/go` cycle. Updated at the
end of every material cycle — see `TITANOS_LIVING_PARETO_FRONTIER_
ARCHITECTURE.md` §XVI/§XVII. Not a queue; exactly one recommendation at a
time. Superseded entries move to `PARETO_FRONTIER.md`'s status field
rather than being deleted here.

---

**As of 2026-08-25, cycle following the Capability Sigil build:**
Built `foundation/sigil.py` + `SIGIL.md` — computed capability index,
current result `TIER:T6 | IRON:10 | LATTICE:6 | PROOF:8 | SIGHT:10 |
FRONTIER:10 | ORCH:10 | MEMORY:10 | REALITY:10`. **Real bug found and
fixed during this build**: the PROOF dimension's own test-running logic
recursively forked without bound (it shells out to run `foundation`'s
suite, which contains this very module's tests, which call
`compute_sigil()` again) — caught by watching process count climb past
50 forked processes, not by review. Fixed with an explicit recursion
guard (`RECURSION_GUARD_ENV`) plus a subprocess timeout as a second
safety net; verified clean with `ps aux` after the fix, zero leftover
processes.

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

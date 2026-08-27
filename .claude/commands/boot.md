---
description: TitanOS boot sequence — reload invariants, verify state against reality, report before any GO cycle
---

Execute the TitanOS boot sequence for this repository. This is a
verification pass against REAL state, not a recitation of doctrine —
every step below requires an actual tool call, not an assumption from
conversation memory. Follow `TITANOS_GO_CYCLE_DOCTRINE.md`'s Zero-Trust
Reconnaissance principle (§V) throughout: a module list or a prior
summary is not proof of anything; verified behavior is.

1. **LOAD OBELISK INVARIANTS** — Read `doctrine/doctrine-002.yaml`,
   `doctrine/POLE_REVERSAL_DOCTRINE.yaml`, and
   `magl/constitution/OBELISK_INVARIANTS.yaml`. Note any invariant marked
   `NOT_ENFORCED` or `PARTIAL` — those are live constraints on what "GO"
   may safely do next, not historical trivia.

2. **VERIFY CT_141** — Run the flow-switch test suite:
   `python3 -m unittest discover -s foundation/tests -p "test_flow_switch.py"`.
   Confirm it passes. This is the literal verification that the panic
   axiom (`PANIC = information_velocity > verification_velocity`) is
   still mechanically enforced, not just documented.

3. **RESTORE BLACK ICE ZERO-TRUST POSTURE** — Run
   `python3 -m unittest discover -s firewall/tests` and
   `python3 -m unittest discover -s taal/gate/tests`. Confirm both pass.
   This verifies the gate that refuses ungrounded authorization is
   actually intact, not merely present as a file.

4. **LOAD CURRENT STATE + PROVENANCE** — Read every `BUILD_REPORT.md`
   under `schema/`, `firewall/` (if present), `kpm/`, `magl/`, `rpa/`,
   `taal/`, `foundation/`. Read `HUMAN_DECISIONS.md` — the consolidated
   list of every judgment call left to a human across every session; do
   not treat an item there as blocking unless it actually blocks the
   move you're about to make. Run `git log --oneline -15` to see what
   actually landed most recently, not what a conversation summary claims
   landed. Run the full repository test suite (every `*/tests/` directory
   discovered via `python3 -m unittest discover`) and record the real
   pass/fail count.

4b. **CHECK PULSE CONTINUITY** — a real hourly cron job
   (`foundation/cron_pulse.py`) runs `foundation/sentinel.py::pulse_sweep()`
   independent of any Claude session and appends to
   `foundation/pulse_log.jsonl`. Call
   `foundation.sentinel.read_pulse_continuity(REPO_ROOT)` (read-only,
   bounded to the last 20 records, fails soft if the log is missing or a
   line is malformed) and report `available`, `latest_timestamp`,
   `records_considered`, `stale` (flags if the last record is >3h old —
   the cron clock may have stopped), and any
   `meaningful_findings`/`warnings`. A finding here is evidence to look
   at, not something already authorized to act on — same rule as every
   other Sentinel finding.

4c. **CHECK MOUTH + DEPENDENCY-PRESSURE CONTINUITY** — the same cron
   entry also runs two mouths (`foundation/mouth_pypi.py`,
   `foundation/mouth_github_releases.py`) and
   `foundation/dependency_pressure.py`, each appending to its own jsonl
   log. Call `foundation.mouth_common.read_mouth_log_continuity(log_path)`
   (same bounded/fail-soft/stale-after-3h contract as 4b, independent
   implementation — different payload shape, not shared code) against
   `foundation/mouth_pypi_pyyaml_releases_log.jsonl`,
   `foundation/mouth_github_pyyaml_releases_log.jsonl`, and
   `foundation/dependency_pressure_log.jsonl` (the last one may not
   exist yet — `available=False` there just means no dependency
   pressure has ever fired, not a fault).

5. **CHECK WHAT ALREADY EXISTS** — Read `magl/BUILD_REPORT.md`'s and
   `foundation/MAPPING.md`'s "next smallest work cell" / "genuinely
   unbuilt" sections specifically — these are the standing, named,
   not-yet-closed gaps from prior GO cycles. Read `PARETO_FRONTIER.md`
   (ranked candidate moves, some already scoped in full — Active/Blocked
   sections only; the Archive table is history, not the scan path) and
   `NEXT_MOVE.md` (the single standing recommendation from the last
   cycle) — do not re-derive a frontier from scratch if one is already
   recorded and still fresh; do re-verify it rather than trust it blindly
   if its `added` date is old. `INTUITION.md` holds unproven observations
   with no authority — worth a glance, never a substitute for the
   frontier. `SIGIL.md` holds the last computed capability index
   (`TIER:Tn | IRON:.. | ...`) — orientation, not authority; re-run
   `foundation/sigil.py::compute_sigil()` rather than trusting a stale
   snapshot if it's been a while. Do not treat a capability as missing
   without checking these first.

6. **IDENTIFY ACTIVE OBJECTIVE** — From step 4-5's findings, state the
   current objective in one sentence. If multiple `BUILD_REPORT.md` files
   name unresolved next-steps, state all of them, not just the most
   recent file's.

7. **MAP CURRENT BOTTLENECK** — Apply the leverage hierarchy from
   `TITANOS_NEXT_LEVER_SEQUENCER.md`: is there a blocker (rung 1, e.g. a
   failing test, an unresolved human-decision gate)? An unverified
   critical assumption (rung 2)? Only if rungs 1-2 are clear, look at
   reuse (rung 3) and repair (rung 4) opportunities before any new-build
   candidate (rung 5+).

8. **CALCULATE HIGHEST-LEVER SEQUENTIAL MOVE** — Per the Sequential Law:
   a lower-rung move is illegitimate while a higher, unresolved rung
   remains available, even if the lower-rung candidate is well-specified.
   State the single move that follows.

9. **CHECK REVERSIBILITY + REALITY YIELD** — For the move identified in
   step 8: is it reversible? What would the reality-yield ledger record
   as evidence for it (verified benefit / error reduction / reusability /
   information gain), not projected value?

10. **REPORT** — in exactly this format, no padding:

```
BOOT STATUS:
CORE:
STATE:
OBJECTIVE:
BOTTLENECK:
HIGHEST LEVER:
NEXT MOVE:
GO / HOLD / HUMAN DECISION:
```

If the report is `HOLD`, name which kind, using
`foundation.sentinel.classify_hold()` (built 2026-08-27) rather than
leaving it undifferentiated: `TERMINAL_HOLD` (nothing is being sought),
`BLOCKED_HOLD` (a named blocker exists), `BUDGET_HOLD`, `AUTHORITY_HOLD`,
`SIGNAL_WAIT_HOLD` (a lawful public channel — e.g. the "Bring a
bottleneck" issue template — is already open and the only missing thing
is an external actor using it; not fetchable, so never INPUT_STARVED_HOLD),
or `INPUT_STARVED_HOLD` (a concrete objective exists, internal levers
are exhausted, and no discovery is currently authorized to look
outside the repository for it — see `foundation/discovery_authorization.py`
and `HUMAN_DECISIONS.md` item 12 for what bounded discovery is actually
authorized, and note it still has no fetcher to exercise it).

Do not begin a GO cycle automatically after this report — `/boot` ends at
the report. A GO cycle begins only when the operator separately says
`GO`.

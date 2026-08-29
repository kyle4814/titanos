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

   Also report `compacted`, `raw_finding_count`, and `truncated_findings`
   (added 2026-08-28). `compacted=True` means CT_141's throttle actually
   fired for at least one sweep in the window and `meaningful_findings`
   is a truncated view, not the whole picture — do not report a finding
   count from a compacted window as if it were complete.

4b-ii. **CHECK THE PULSE'S FAILURE RECEIPT** — the crontab entry
   redirects with `>> foundation/cron_pulse.err.log 2>&1`, so that file
   is the only place a traceback lands if the one unattended process
   this repository runs dies. `read_pulse_continuity()` can tell you
   *that* the clock stopped (`stale=True`); this tells you *why*. Call
   `foundation.sentinel.read_cron_stderr(REPO_ROOT)` (built 2026-08-28;
   read-only, byte-bounded, fails soft) and report `available`, `failed`,
   `size_bytes`, and the `tail` if `failed`. Three distinct states, do
   not collapse them: `available=False` (no redirect configured — a fresh
   clone, and *not* evidence the pulse is healthy), `available=True,
   failed=False` (the redirect exists and the process has never failed —
   the normal state), `failed=True` (real failure output, retrievable).
   This is retrieval, not diagnosis — nothing classifies or acts on the
   error.

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

   For `dependency_pressure_log.jsonl` specifically, that call answers
   only "is this clock alive" — it returns `latest_status=None` for
   every record it will ever see there, because a dependency-pressure
   record is a `Finding` payload, not a `MouthObservation`. To see what
   the log actually *said*, also call
   `foundation.dependency_pressure.read_dependency_pressure_log(log_path)`
   (built 2026-08-28 to close exactly this gap; same bounded/fail-soft
   contract). Report `findings`, `errors`, and `actionable`. `actionable=True`
   means at least one finding's `recommended_next_action` is not
   `NONE_REQUIRED` — evidence for a human decision about
   `requirements.txt`, never an authorization to change the pin.

5. **CHECK WHAT ALREADY EXISTS** — Read `magl/BUILD_REPORT.md`'s and
   `foundation/MAPPING.md`'s "next smallest work cell" / "genuinely
   unbuilt" sections specifically — these are the standing, named,
   not-yet-closed gaps from prior GO cycles. Read `PARETO_FRONTIER.md`
   (ranked candidate moves, some already scoped in full — Active/Blocked
   for what is open; the Archive table is history, not the scan path) and
   `NEXT_MOVE.md` (the single standing recommendation from the last
   cycle) — do not re-derive a frontier from scratch if one is already
   recorded and still fresh; do re-verify it rather than trust it blindly
   if its `added` date is old.

   **Then read `PARETO_FRONTIER.md`'s "Rejected / not on the frontier"
   section — it is part of the scan path, not history.** This step used
   to say "Active/Blocked sections only", which routed a fresh worker
   around the entire killed-idea register. That register is where prior
   cycles record what was already prosecuted and killed AND the exact
   evidence that would reopen each one (e.g. a second `autonomy_loop.py`
   actuator; new external mouths/sensors, all blocked on the same
   missing in-repository consumer). Without it a fresh worker cannot
   tell "not yet considered" from "considered and killed on evidence",
   so it re-litigates settled work and spends a cycle rediscovering a
   conclusion the repository already paid for.

   The Rejected entries are not vetoes on your judgement — each one
   names its own re-entry condition. Reopening a killed candidate is
   legitimate exactly when its stated condition is met by new evidence,
   and not merely because it seems appealing again. Check the condition
   before proposing; if it is met, say so explicitly and cite the new
   evidence. `INTUITION.md` holds unproven observations
   with no authority — worth a glance, never a substitute for the
   frontier. `SIGIL.md` holds the last computed capability index
   (`TIER:Tn | IRON:.. | ...`) — orientation, not authority; re-run
   `foundation/sigil.py::compute_sigil()` rather than trusting a stale
   snapshot if it's been a while. Retrieve the recorded snapshot
   structurally rather than by eyeballing the markdown:
   `foundation.sigil.read_recorded_sigil(REPO_ROOT)` (built 2026-08-28;
   read-only, no subprocess, instant, returns `None` if nothing is
   recorded). It returns a `RecordedSigil`, deliberately **not** a
   `Sigil` — a stored markdown value is not measured capability, and
   only `compute_sigil()` produces the latter. Pass it straight in as
   `reconcile_sigil(REPO_ROOT, previous=recorded)` when a cycle actually
   changed capability; that call runs every subsystem's test suite (~40s)
   so it stays a deliberate step, not an every-boot default. This is the
   mechanism that catches sigil drift — the failure mode that has already
   occurred twice here (CLAUDE.md stuck at `TIER:T7` after the real value
   had fallen to T3; `SIGIL.md`'s evidence table still claiming 1212
   tests), both times caught by a human noticing, not by the machine. Do not treat a capability as missing
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

10b. **ADJUDICATE THE BOARD (optional; only if this cycle built one)** —
   if the cycle produced a governed surface board, call
   `foundation.sentinel.evaluate_continuation(surfaces,
   state_revalidated=..., new_wake_evidence=..., candidates_found=...)`
   to decide whether governed work remains. Pure function, no I/O,
   ~0.02 ms — never a reason to skip it, and never a reason to invent a
   board just to have something to call it with. Distinct from
   `classify_hold()`, which names WHICH KIND of hold; this decides
   whether the board is closed at all.

   You prepare the snapshot; the governor never invents it. Pass
   `candidates_found` explicitly — `()` positively asserts the cycle
   found nothing; omitting it is refused, because silence is not a claim.

   Exactly three outcomes, none of which authorises anything:
   - **raises `UnaccountedCandidates`** = NO_VERDICT. The board is not
     lawfully formed. Report the missing proof. Do **not** report GO and
     do **not** report HOLD — neither is earned.
   - **`proceed=True`** = CONTINUE. `unresolved_surfaces` names the open
     work; that becomes the `NEXT MOVE` line above.
   - **`proceed=False`** = HARD_STOP. No governed work remains; report
     HOLD and name the wake conditions that would reopen it.

   A verdict is a report, never an authorisation. Nothing is built,
   committed, pushed, installed, armed, or scheduled as a consequence.

   **What this step is, precisely:** a documented session protocol, the
   same kind as steps 4b/4b-ii/4c/5 and the `classify_hold()` branch
   below. It is *not* a code-level call: nothing in the codebase enforces
   that a session performs it, and no test goes red if it is skipped.
   That limit is real and is stated here rather than papered over --
   see `PARETO_FRONTIER.md`'s own stricter "real consumer" standard,
   which this repository's practice and its written doctrine have not
   yet reconciled.

Do not begin a GO cycle automatically after this report — `/boot` ends at
the report. A GO cycle begins only when the operator separately says
`GO`.

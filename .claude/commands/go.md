---
description: TitanOS Reality-Yield /go cycle — autonomous highest-lever build, reality-bound
---

Execute one `/go` cycle per `TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md`
§XIV. This command autonomously reconnoiters, selects, builds, tests, and
records — it does not ask "what should I work on" unless a genuine
human-authority decision is required (irreversible action, credentials,
capital, constitutional change). Read that file's opening note before
proceeding: this repository currently has no external ping surface, so
step 4 below usually resolves to ordinary GO-Cycle work, not literal
profit-architecture construction — do not fabricate a customer, a
transaction, or a market signal that doesn't exist. Applying Agent
Delta's own standard to this command's premise is itself step 0.

Execute in order, each step a real action, not a description:

1. **`/boot` the vault** — run the `/boot` command's ten steps in full
   (invariants, CT_141 verification, Black Ice posture, current state,
   what already exists) before anything else. Do not skip this because
   context from earlier in the session feels current — re-verify.

2. **Inspect current reality-yield architecture** — read
   `foundation/reality_yield_ledger.py` and any prior ledger entries;
   read `foundation/MAPPING.md`, `magl/BUILD_REPORT.md`,
   `rpa/BUILD_REPORT.md`, `taal/BUILD_REPORT.md`'s "next smallest work
   cell" / "human decisions required" sections specifically — these are
   the standing, named, not-yet-closed gaps from prior cycles.

3. **Find the highest-sequential lever** — apply
   `TITANOS_NEXT_LEVER_SEQUENCER.md`'s hierarchy. Check rung 1 (any
   failing test or unresolved blocker right now?) and rung 2 (any
   critical assumption from a prior `BUILD_REPORT.md` that was flagged
   but never verified?) before considering rung 3+ (reuse, repair, new
   build). A lower rung is not a legitimate choice while a higher,
   unresolved rung is available.

4. **Identify the smallest external ping, honestly** — per the doctrine
   file's opening note, if no real external ping surface exists for the
   candidate lever, say so plainly rather than inventing one, and either
   pick a different candidate that IS internally verifiable (a test, a
   cross-file integrity check, a hardening pass) or explicitly build the
   measurement/interface that would be needed to create a first real ping
   — never simulate a ping and record it as if real.

5. **Run Alpha** — reconnaissance: what exists, what's duplicated,
   what's genuinely missing, current signals, bottlenecks, broken
   dependencies. Must not recommend a rebuild without proving the
   existing component can't be extended.

6. **Run Beta** — for the leading candidate(s): beneficiary, value, the
   smallest ping (or smallest internal verification if no external ping
   exists), measurement, cost, reversibility, failure condition.

7. **Run Gamma** — generate only options connecting to existing
   architecture, with measurable success criteria; rank by
   `(leverage × reality access × reversibility × reusability) / (cost × time × risk × complexity)`;
   keep the top options only.

8. **Run Delta** — attack the leading candidate: what assumption hasn't
   been earned, is this revenue/progress or projection, does this
   duplicate something, can it be tested cheaper, what must be true for
   it to work. Delta may veto; a veto must produce `FAILURE_REASON`,
   `MISSING_EVIDENCE`, `SAFER_TEST`, or `KILL_RECOMMENDATION` — never a
   bare "this is a problem."

9. **Apply CT_141** if information/urgency is outrunning verification at
   any point in the above — throttle, don't accelerate (see
   `foundation/flow_switch.py`).

10. **Select one build** — the single highest lever that survived Delta.

11. **Implement the minimum safe piece** — smallest contract that
    satisfies it; prefer existing state machines/abstractions/wrappers
    over new frameworks.

12. **Test it** — real, running tests; boundary and adversarial
    conditions, not just the happy path.

13. **Record reality-yield metrics** — if this touched
    `foundation/reality_yield_ledger.py`-shaped work, record honestly,
    including negative or null results; never mark unknown or simulated
    yield as profitable.

14. **Harden only what was earned** — promote through the real state
    machine (`kpm/promotion/state_machine.py` / `foundation/
    switch_hardener.py`) if and only if the ten hardening gates pass.

15. **Update the vault** — the relevant `BUILD_REPORT.md`/`MAPPING.md`,
    and this session's memory if durable.

16. **Output the next four levers** — per §IX (ARE): Option A highest
    lever, B fastest reality test, C lowest regret, D do nothing/preserve
    optionality — each with what/expect/reality-must-return/cost/
    break-risk/success/failure-teaches/reversibility.

17. **Halt** at the human gate. Do not continue to a second cycle
    automatically — `/go` is one cycle; the operator invokes it again for
    the next.

Final output must end with the doctrine's required report tail (from
`TITANOS_NEXT_LEVER_SEQUENCER.md`):

```
CURRENT STATE:
VERIFIED PROGRESS:
NEW LEVER CREATED:
CURRENT BOTTLENECK:
NEXT HIGHEST-LEVER MOVE:
WHY THIS COMES NEXT:
DEPENDENCIES:
RISKS:
REVERSIBILITY:
REALITY YIELD:
GO / HOLD / HUMAN DECISION:
```

# RUNBOOK — Opportunity Cycle (Sonnet-operable)

One entry point: `foundation.swarm_contract.run_swarm_task()`. Never call
`opportunity_cycle`, `tender_radar`, or `discovery_authorization`
directly for an opportunity/tender sweep — this envelope is the whole
interface. If a step below tells you to do something this module
doesn't support, stop and ask; do not reach past the envelope into the
modules it wraps.

## 1. Dry run (always do this first)

```python
from pathlib import Path
from foundation.swarm_contract import SwarmTaskDescriptor, run_swarm_task

descriptor = SwarmTaskDescriptor(
    objective="observe open tenders for widget supply contracts",
    state_dir=Path("/tmp/opp_state"),
    ledger_path=Path("/tmp/opp_ledger.jsonl"),
)
result = run_swarm_task(descriptor)
print(result.show_the_math())
```

Expected output: `status=DRY_RUN_OK`, all counts `0`, nothing written to
either path (verify with `ls` if you want proof — nothing will exist).
This is always safe to run, any number of times, with no authorization.

## 2. Going live

Requires **two** explicit fields, not one:

```python
descriptor = SwarmTaskDescriptor(
    objective="observe open tenders for widget supply contracts",
    state_dir=Path("/tmp/opp_state"),
    ledger_path=Path("/tmp/opp_ledger.jsonl"),
    live=True,
    authorized_by="Kyle Graham",   # a real name, not a placeholder
)
result = run_swarm_task(descriptor)
```

`live=True` alone is refused (`status=AUTHORITY_HOLD`,
`refused_by="LIVE_REQUIRES_AUTHORIZED_BY"`). This is not a bug to work
around by filling in a fake name — `authorized_by` must be a real human
name because it is recorded as who made this specific run happen.

Expected output on success: `status=LIVE_OK`, `sweep_status` from the
real feed, `signal_count`/`controlling_party_count`/
`ledger_records_written` reflecting what was actually observed, and
`qualified=0 contracts=0 cash=0` — **always**, on every run, live or dry.
A discovered tender notice is observed demand, not a lead, a contract,
or cash. If a result ever shows a nonzero value in any of those three
fields, that is not evidence of success — stop and treat it as a bug
report, because the code structurally refuses to construct such a
result (`SwarmTaskResult.__post_init__` raises `AssertionError`).

## 3. Reading the result

`result.status` is always one of:

| status | meaning | what to do |
|---|---|---|
| `DRY_RUN_OK` | validated, nothing executed | inspect `result.reason` for the plan, then decide whether to go live |
| `LIVE_OK` | sweep + pipeline actually ran | read `signal_count` etc.; this is the only status where real work happened |
| `VALIDATION_REFUSED` | malformed descriptor, refused before any action | read `result.refused_by` — it names the exact field; fix that field and retry |
| `AUTHORITY_HOLD` | a real authority gate was hit | read `result.requires_human` — it names the gate; do not retry with a workaround, get the named human input and retry with it supplied |
| `BUDGET_EXHAUSTED` | the discovery budget for this objective was already spent (this process) | wait, or use a differently-worded objective; not an error, not a reason to retry immediately in a loop |
| `INTERNAL_ERROR` | last-resort catch, an exception was converted into a structured result | read `result.reason` (`type: message`); this means something genuinely unexpected happened — do not paper over it, escalate |

`result.refused_by` and `result.requires_human` are always populated
together with any non-`*_OK` status — never guess from a bare message.

## 4. What each failure state actually means

- **`VALIDATION_REFUSED`** — you built a `SwarmTaskDescriptor` the
  envelope refuses to act on: empty objective, missing/colliding paths,
  a budget field above this repository's own standing ceiling
  (`DEFAULT_MAX_QUERIES=5`, `DEFAULT_MAX_WALL_CLOCK_SECONDS=60`,
  `DEFAULT_MAX_RESULTS=10`), or an objective matching a known-unbounded
  pattern ("find anything interesting", "every repository", etc.). Fix
  the named field. Never raise the ceiling to make the refusal go away —
  raising it is a human decision (see §6).
- **`AUTHORITY_HOLD`** — either `live=True` with no `authorized_by`, or
  the underlying discovery scope was denied by
  `communication_gate.py`. Both name the gate in `requires_human`. This
  is not a retryable error; it is the system correctly declining to act
  without a human-facing authorization that hasn't been supplied.
- **`BUDGET_EXHAUSTED`** — `discovery_authorization.spend_query()`
  refused before opening a socket. This is expected behaviour under
  repeated live runs against the same objective within one process —
  not a crash, not evidence anything is broken.
- **`INTERNAL_ERROR`** — an exception the envelope didn't anticipate was
  caught at the outer boundary rather than propagating as a bare
  traceback. Treat this the same as any other unhandled bug: reproduce,
  read `result.reason`, escalate — do not retry blindly.

## 5. Running the tests

```
python3 -m unittest foundation.tests.test_swarm_contract
```

Expected: all tests pass, offline, no network access required. If any
fail, do not "fix" the test to make it pass — the tests encode the
safety contract this runbook describes; a failing test means the
contract broke.

## 6. What this runbook must NEVER be extended to include

- **No instructions for calling `opportunity_cycle.run_cycle()`,
  `tender_radar.sweep()`, or `discovery_authorization` directly.** The
  envelope is the interface. If it's missing a capability you need, that
  is a request to extend `foundation/swarm_contract.py`, not a reason to
  route around it.
- **No instructions for raising `max_queries`/`max_wall_clock_seconds`/
  `max_results` above the repository's standing defaults.** That
  ceiling is a human decision (see `TITANOS_CRITICAL_FUNCTION_SWITCH_
  GATE.md`), not a per-task parameter to negotiate around by editing
  `discovery_authorization.py`'s constants.
- **No instructions for passing `_fetch_fn_for_tests` in a production
  run.** It exists for the offline test suite only. Passing it live
  replaces the real fetch with fabricated bytes — never do this outside
  `foundation/tests/test_swarm_contract.py`.
- **No instructions for sending anything outbound** (email, webhook,
  API write, contact form). This envelope has no such capability and
  none should ever be added to it under this runbook's authority —
  outbound communication to a real third party is Authority Gate #2 in
  `.claude/commands/next.md` and requires a human, every time, no
  exception.
- **No instructions for treating a nonzero `qualified`/`contracts`/
  `cash` as a success signal.** They cannot be nonzero by construction;
  a runbook edit that describes what one "means" would be describing an
  impossible state.
- **No scheduling / cron / loop instructions.** Whether this envelope
  runs on a schedule is a human decision recorded in
  `HUMAN_DECISIONS.md`, not something this runbook authorizes by
  omission.

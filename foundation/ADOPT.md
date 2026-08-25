# Adopting `foundation/`

External-facing packaging doc — FRONTIER-008's seventh instance, same
template as the six before it. This is the largest subsystem (17
modules) — depth here is deliberately proportionate, not uniform: full
quickstarts for the two hard-gated critical functions
(`TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md`'s first two real
implementations), an index with pointers for the rest. Distinct from
`foundation/BUILD_REPORT.md`, `MAPPING.md` (internal audit trail /
module map).

## Thesis

The repository's cross-cutting mechanisms: panic detection (CT_141),
hard-gated critical functions (publication, admission), capability
self-measurement (the Sigil), health sensing, recursion safety, and
provenance compression (Crystal). Not a single coherent library — a
collection of independently-tested, independently-useful modules that
happen to share a house style (fail-closed on unknown, two-point
enforcement, append-only stores where state matters).

## Quickstart — CT_141 panic detection

```python
from foundation.flow_switch import PanicSample, detect_panic

# information_velocity/verification_velocity are CALLER-DECLARED --
# this module reasons about the two numbers, it does not measure them
sample = PanicSample(information_velocity=10.0, verification_velocity=2.0,
                      timestamp="2026-08-26T00:00:00Z")
detect_panic(sample)   # -> True: producing far faster than verifying

quiet = PanicSample(information_velocity=0.0, verification_velocity=0.0,
                     timestamp="2026-08-26T00:00:00Z")
detect_panic(quiet)    # -> False: nothing happening is not panic
```

## Quickstart — the publication switch, fail-closed on unknown

```python
from foundation.publication_gate import PublicationSwitch, evaluate, authorize_publish

switch = PublicationSwitch()   # every field starts at its fail-closed default
evaluate(switch).action_permitted   # -> False: nothing was declared

switch = PublicationSwitch(
    target_repo="github.com/org/repo", secret_scan_passed=True,
    secret_scan_evidence="0 real findings, verified 2026-08-26",
    license_present=True, readme_present=True, classification="PUBLIC",
    human_authorized_by="a real name", human_authorization_note="public push authorized",
    reversibility_acknowledged=True,
)
authorize_publish(switch)   # -> True only if evaluate() independently agrees;
                             # a caller cannot bypass evaluation by hand-
                             # constructing a Decision with action_permitted=True
```

## The rest of this subsystem, by pointer

| Module | What it does | Where to look |
|---|---|---|
| `hells_gate.py` | General admission boundary (ADMIT/QUARANTINE/REJECT/HUMAN_REVIEW_REQUIRED, default QUARANTINE, never "TRUSTED") | `foundation/tests/test_hells_gate.py` |
| `sigil.py` | Capability self-measurement, recomputed from evidence, never manually set | `SIGIL.md`, `SIGIL_LEXICON.md` |
| `sentinel.py` | Read-only repo health pulse sweep, CT_141-compacted | `foundation/tests/test_sentinel.py` |
| `crystal.py` | Durable problem/hypothesis/evidence/result compression | `FIRST_PING.md` for a real worked example |
| `recursion_guard.py` | Ancestry-stamped subprocess boundary, prevents unbounded forking | `TITANOS_RECURSION_GUARD_001.md` |
| `secret_scanner.py` | Pre-publication credential/secret scan | used for real in `FIRST_PING.md`'s predecessor cycle |
| `switch_hardener.py`, `reality_yield_ledger.py`, `layer0_worker.py`, `communication_gate.py`, `queue_worker_adapter.py`, `task_queue.py`, `conclusion_gate.py`, `sentinel_worker.py` | See `MAPPING.md` and per-module docstrings | `foundation/tests/` (one file per module) |

## Failure cases

- `evaluate(PublicationSwitch())` (all defaults) never raises — it
  returns `action_permitted=False` with `reasons` explaining exactly
  which fields were missing. Fail-closed on unknown is the whole point.
- `authorize_publish()` independently re-derives permission from the
  switch's own evidence — it does **not** accept a pre-built
  `PublicationDecision(action_permitted=True)` from the caller. Hand-
  constructing a permitted-looking Decision and passing it in does
  nothing; only `evaluate()`'s own computation counts.
- `hells_gate.py` never outputs the literal string `"TRUSTED"` anywhere
  — enforced by a test scanning its own output vocabulary, not just
  documented.

## Threat model

- **In scope:** bypassing publication authorization via a hand-built
  Decision object (defended — see above), unbounded recursive subprocess
  spawning (`recursion_guard.py`, closed a real bug found by watching
  process count climb past 50 in under three minutes during `sigil.py`
  development).
- **Out of scope:** `communication_gate.py` has no door — it answers
  "is external communication authorized" but nothing in this repository
  calls a real network operation based on its answer. Not a gap; a
  deliberate lock with no door yet.

## Limitations

No persistence layer across any store in this subsystem. No
cryptographic signing. `sigil.py`'s PROOF dimension genuinely shells out
to run every subsystem's test suite — expect the full computation to
take real wall-clock time (tens of seconds), not be instant.

## Changelog

- 2026-08-25: `publication_gate.py`, `hells_gate.py`, `flow_switch.py`,
  `switch_hardener.py`, `reality_yield_ledger.py`, `sentinel.py`,
  `sigil.py`, `crystal.py`, `recursion_guard.py`, `layer0_worker.py`
  built across the session.
- 2026-08-25: `FlowSwitchRecord.history` frozen (tuple, not list) —
  same `EPISTEMIC_INTEGRITY_002` fix applied across all five affected
  record types in this repository.
- `foundation/`'s own suite: 418 tests as of 2026-08-26 (includes
  `sigil.py`'s real-repo integration test, which is why this suite runs
  slower — ~27s — than any sibling subsystem's).

## Fork guide

Most modules here are standalone; `hells_gate.py` imports `flow_switch.py`
(CT_141 check) and routes containment through `firewall.quarantine`;
`sigil.py` imports `sentinel.py` and `recursion_guard.py`. Run
`python3 -m unittest discover -s foundation -p "test_*.py"` to confirm
the fork is intact (418 tests as of 2026-08-26, real-repo integration
tests included — expect ~30s, not instant).

## Integration interfaces

Each module exports its own dataclass pair (a "Switch"/evidence type and
a "Decision"/result type) following the same shape:
`evaluate(switch) -> Decision`, plus a re-deriving `authorize_*()` where
the function is a hard-gated critical function per
`TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md`.

## Contribution path

None yet — see `firewall/ADOPT.md`'s note; same repository-wide state.
`.github/workflows/tests.yml` runs this subsystem's suite on every push/
PR to `kyle4814/titanos`.

## Machine-readable manifest

```yaml
subsystem: foundation
public_modules:
  - foundation.flow_switch
  - foundation.publication_gate
  - foundation.hells_gate
  - foundation.sigil
  - foundation.sentinel
  - foundation.crystal
  - foundation.recursion_guard
  - foundation.secret_scanner
  - foundation.switch_hardener
  - foundation.reality_yield_ledger
  - foundation.layer0_worker
  - foundation.communication_gate
  - foundation.queue_worker_adapter
  - foundation.task_queue
  - foundation.conclusion_gate
  - foundation.sentinel_worker
runtime_dependencies: [PyYAML]
depends_on_subsystem: [firewall, kpm]
test_command: python3 -m unittest discover -s foundation -p "test_*.py"
test_count: 418
known_limitation: communication_gate.py has no door -- lock only, nothing calls it
provenance: foundation/BUILD_REPORT.md, foundation/MAPPING.md
```

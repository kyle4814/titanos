# TITANOS_COMMUNICATION_SWITCH_001

## INVARIANT

No external communication capability may execute merely because code
exists. `foundation/communication_gate.py::authorize_communication()`
requires an explicit, named human authorization for one declared scope
before it returns True — and even then, its True return value is
consumed by nothing, because no network-capable component exists
anywhere in this repository.

## PROOF

- `foundation/communication_gate.py` — `CommunicationSwitch`,
  `CommunicationDecision`, `evaluate()`, `authorize_communication()`,
  mirroring `foundation/publication_gate.py`'s proven two-point
  enforcement shape (§5 of `TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md`).
- `foundation/tests/test_communication_gate.py` — 19 tests, all passing.
- Full 8-subsystem regression: 8/8 passing, 1135 tests.
- Zero-dependency invariant re-audited against this specific file: no
  `requests`/`urllib`/`socket`/`http.client`/`boto3` import anywhere in
  it, confirmed by both the Obelisk-pattern grep and a structural test
  (`TestNoProductionNetworkImport`).

## APPLICABILITY

Governs exactly one capability: `EXTERNAL_COMMUNICATION`, with three
declared but unimplemented future scopes (`READ_URL`, `READ_API`,
`RECEIVE_WEBHOOK`). Any future component proposing a real network
operation should check `authorize_communication()` first — but building
that future component is explicitly out of scope for this doctrine
file and was not done here.

## LIMITATION AS WRITTEN (2026-08-27) — NOW SUPERSEDED

The original text read: "**NO EXTERNAL COMMUNICATION CAPABILITY HAS BEEN
IMPLEMENTED OR ENABLED.** ... This repository still makes zero network
connections, imports zero network-capable dependencies, and passes the
Obelisk Test exactly as it did before this cycle. The switch existing
does not mean a door exists behind it — no retrieval, send, or receive
mechanism has been built, and this switch's `action_permitted=True`
result is not consumed anywhere."

## CURRENT STATUS (corrected 2026-09-01)

Every sentence above is now false, and the invariant at the top of this
file was false with it. A door was built behind the switch and this
file was never updated.

- `foundation/mouth_common.py::fetch_feed()` imports `urllib.request`
  and makes real network requests. Five mouths and `target_mapping.py`
  call it.
- For several cycles it did so **without consulting this switch at
  all**. The gate was armed and had no consumer. This file, and the
  matching paragraph in `CLAUDE.md`, are why that went unnoticed: the
  documents guarding the door insisted there was no door.
- Wired 2026-09-01. `fetch_feed()` now calls
  `discovery_authorization.authorize_discovery()` — which re-derives
  through `authorize_communication()` — before every request, and
  refuses outright without a `DiscoveryPolicy` naming a concrete
  objective and budget. Adversarial proof:
  `foundation/tests/test_network_control_plane.py`.

The Obelisk Test's *dependency* half still holds (`yaml` remains the
only third-party dependency, every suite runs offline). Its *zero
network imports* half does not, and `SIGIL.md` records that as the
cause of the `T7 -> T3` tier drop and `REALITY:10 -> 6`.

**The standing lesson.** A doctrine file that asserts an absence must be
re-checked when the thing it says is absent gets built, or it becomes
active camouflage for the gap it was written to prevent.

# Adopting `taal/`

External-facing packaging doc — FRONTIER-008's sixth instance, same
template as the five before it. Distinct from `taal/BUILD_REPORT.md`
(internal audit trail).

## Thesis

TAAL-Ω: a security event pipeline — normalize a raw signal, propose
threat archetype candidates against a 12-record library, evaluate
through a root gate that outputs exactly one of `AUTHORIZED` /
`QUARANTINED` / `REQUIRES_HUMAN_REVIEW` / `REFUSED`, with false-positive
recovery preserving all original evidence. The one deliberate design
constraint enforced structurally, not by convention: symbolic/archetype
"demonic" language is a memory aid only — `symbolic_layer.metaphor_
status` must literally equal `"SYMBOLIC_ONLY"`, and a real test proves
two documents differing only in symbolic content produce byte-identical
technical findings. Metaphor cannot leak into evidence.

## Quickstart — the benign path, real and verified

```python
from taal.integrator.integrator import RawSignal, normalize, propose_archetype_candidates
from taal.gate.root_gate import GateInput, evaluate_request

signal = RawSignal(
    signal_id="sig-1", source_type="ACCESS_REQUEST",
    entity="reporting-service", observed_action="requested read access",
    affected_resource="quarterly_sales_summary",
    raw_facts=("scheduled monthly report generation job",),
)
event = normalize(signal)
candidates = propose_archetype_candidates(event)
assert candidates == ()   # a routine scheduled read proposes no threats

decision = evaluate_request(GateInput(
    request_id="req-1", requester="reporting-service",
    action="READ", resource="quarterly_sales_summary",
    scope="declared_dataset", duration="15m",
    identity_verified=True, authority_asserted=True,
    authority_evidence=("service account role: reporting-readonly",),
    scope_declared_necessary=True, reversible=True,
    provenance_status="VERIFIED",
    supporting_evidence=("monthly job schedule record",),
))
# decision.verdict -> "AUTHORIZED"
```

For the other three required paths (SUSPICIOUS → QUARANTINED, AMBIGUOUS
→ REQUIRES_HUMAN_REVIEW, false-positive recovery preserving evidence),
see `taal/tests/test_end_to_end.py` directly — reproducing all four here
would exceed what a packaging doc should carry; the test file already is
the executable demonstration.

## Failure cases

- `evaluate_request()` never defaults an unclear case to `AUTHORIZED` —
  `UNKNOWN != malicious`, but unknown also never silently becomes
  permitted; ambiguous cases route to `REQUIRES_HUMAN_REVIEW`, not a
  guess in either direction.
- Quarantining through `taal/gate/quarantine_mapping.py::taal_quarantine()`
  routes through the real `firewall.quarantine.QuarantineStore` — not a
  second quarantine mechanism. Recovery (`taal_mark_recovered()`) does
  not delete the original quarantine record; the append-only history
  stays intact.
- A caller who tries to make symbolic/archetype language influence a
  technical verdict will find it structurally can't — `metaphor_status`
  is checked, not merely documented as a convention.

## Threat model

- **In scope:** narrative capture via mythologized threat framing
  (the `SYMBOLIC_ONLY` constraint exists specifically to prevent this),
  false positives (recovery path preserves evidence, doesn't erase the
  original finding).
- **Out of scope, named open judgment calls:** `root_gate.py`'s two most
  consequential calls — unevidenced-authority-claim →
  `REQUIRES_HUMAN_REVIEW` rather than `REFUSED`; contradictory evidence →
  `REQUIRES_HUMAN_REVIEW` rather than `AUTHORIZED_WITH_CONSTRAINTS` —
  worth reviewing against your actual risk tolerance
  (`HUMAN_DECISIONS.md` item 5).

## Limitations

No persistence layer beyond what `QuarantineStore` already provides
in-process. No cryptographic signing. No network calls.

## Changelog

- 2026-08-25: initial build, 4 parallel agents (resumed mid-build after
  hitting a session usage limit — first time in this build series, all
  four picked up cleanly from saved progress).
- `taal/`'s own suite: 203 tests as of 2026-08-26.

## Fork guide

`taal/gate/root_gate.py` and `taal/integrator/integrator.py` are the
core pair; `taal/gate/quarantine_mapping.py` additionally depends on
`firewall.quarantine`. Run `python3 -m unittest discover -s taal -p
"test_*.py"` to confirm the fork is intact (203 tests as of 2026-08-26).

## Integration interfaces

`RawSignal`, `NormalizedSecurityEvent`, `GateInput`, `GateDecision` are
the public data shapes. `evaluate_request(GateInput) -> GateDecision`
is the sole gate entry point — no other function in this subsystem
should be treated as authoritative for a verdict.

## Contribution path

None yet — see `firewall/ADOPT.md`'s note; same repository-wide state.
`.github/workflows/tests.yml` runs this subsystem's suite on every push/
PR to `kyle4814/titanos`.

## Machine-readable manifest

```yaml
subsystem: taal
public_modules:
  - taal.integrator.integrator
  - taal.gate.root_gate
  - taal.gate.quarantine_mapping
  - taal.schema.threat_archetype
  - taal.schema.permission_request
  - taal.schema.normalized_security_event
  - taal.schema.verdict
runtime_dependencies: [PyYAML]
depends_on_subsystem: [firewall]
test_command: python3 -m unittest discover -s taal -p "test_*.py"
test_count: 203
known_limitation: two named open policy calls in root_gate.py (HUMAN_DECISIONS.md item 5)
provenance: taal/BUILD_REPORT.md
```

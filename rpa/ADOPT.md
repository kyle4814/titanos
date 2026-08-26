# Adopting `rpa/`

External-facing packaging doc — FRONTIER-008's fifth instance, same
template as the four before it. Distinct from `rpa/BUILD_REPORT.md`
(internal audit trail).

## Thesis

RPA-Ω, "Legacy Upgrade Library": 8 schemas modelling the real-world path
from a legacy system map through bottleneck identification, automation
candidacy, pilot simulation, human authorization, and measured rollback
— plus the one genuinely security-critical piece, `rpa/gates/
human_jurisdiction.py`, which this session found and closed two real
gaps in (a forged-history exploit, and a content-validation bypass).
Reuses `magl/`'s validator pattern and `kpm/promotion/
state_machine.py`'s state machine rather than building parallel ones.

## Quickstart — the security-critical gate

This is the part worth understanding deeply; the other 7 schemas are
straightforward YAML validators following the same `schema/validator.py`
pattern documented in `schema/ADOPT.md`.

```python
from kpm.promotion.state_machine import PromotionStore
from rpa.gates.human_jurisdiction import (
    SourceRegistry, authorize_pilot, confirm_pilot_authorized,
)

registry = SourceRegistry(archive_dir="/tmp/example_archive", registry_path=None)
candidate_text = open("rpa/fixtures/automation_candidate.yaml").read()
source = registry.ingest_source(candidate_text.encode(), source_type="yaml",
                                 source_location="example", author_or_origin="alice")

store = PromotionStore()
store.register("candidate-1", created_by="alice")
for state in ("DISTILLED", "PROVISIONAL", "TESTED"):
    store.promote("candidate-1", to_state=state, reason="advancing")

# Queue for review -- NOT authorization. Self-queueing is legitimate here.
# source_registry/source_hashes are REQUIRED: authorize_pilot() recovers
# the exact bytes and runs validate_automation_candidate() fresh before
# queueing anything -- a candidate_id with no real validated content
# behind it is refused (NoValidatedSource), not silently accepted.
authorize_pilot(store, "candidate-1", reviewed_by="alice",
                created_by="alice", reason="ready for review",
                source_registry=registry, source_hashes=(source.content_hash,))

confirm_pilot_authorized(store, "candidate-1")   # -> False: still HUMAN_REVIEW,
                                                  # not yet promoted to STABLE

# The actual authorization -- a SEPARATE call, by someone other than the creator
store.promote("candidate-1", to_state="STABLE", reason="approved",
               reviewed_by="bob")

confirm_pilot_authorized(store, "candidate-1")   # -> True, genuinely re-derived
```

## Failure cases

- `authorize_pilot()` reaching `HUMAN_REVIEW` is **not** authorization —
  it means "ready for a human to look at." A caller that treats
  `authorize_pilot()`'s return value as permission to run the pilot is
  making the exact mistake this module's docstring warns against.
- `authorize_pilot()` raises `NoValidatedSource` if none of the declared
  `source_hashes` recover to content that passes
  `validate_automation_candidate()` — closing a real gap this session's
  own adversarial recon found: previously, any `candidate_id` string
  could be queued for review with zero connection to real, structurally
  validated candidate content. Raises `AmbiguousValidatedSource` if more
  than one declared hash independently validates — this gate refuses to
  guess which one is the real subject.
- `confirm_pilot_authorized()` never raises — returns `False` for any
  record that's missing, not `STABLE`, or whose `history` doesn't show a
  genuine `HUMAN_REVIEW → STABLE` transition reviewed by someone other
  than `created_by`. It does **not** trust `record.state == "STABLE"`
  at face value — it re-derives the guarantee from history every call,
  specifically so a record whose `state` field merely says `STABLE`
  (e.g. reached via the also-legal `TESTED → STABLE` edge, which this
  gate deliberately does not accept as sufficient) cannot fool it.
- `PromotionRecord.history` is a frozen tuple (fixed 2026-08-25,
  `EPISTEMIC_INTEGRITY_002`) — a caller cannot forge a `HUMAN_REVIEW →
  STABLE` entry via `.append()` to fake authorization. This was a real,
  live, reproduced exploit closed this session; `confirm_pilot_
  authorized()`'s re-derivation is exactly the check that exploit
  bypassed before the fix.

## Threat model

- **In scope:** forged authorization history (closed — see above),
  self-authorization (refused — `SelfPromotionForbidden` on the
  `HUMAN_REVIEW → STABLE` edge), state-label spoofing (defended against
  by re-deriving from history, not trusting `.state`), **content-
  validation bypass** (closed 2026-08-26 — a `candidate_id` with no real
  validated automation-candidate content behind it can no longer be
  queued for review; validation is recomputed fresh at authorization
  time via `SourceRegistry`'s content-addressed recovery, never trusted
  from a stale stored result).
- **Out of scope:** the other 7 schemas (`legacy_system_map`,
  `institutional_bottleneck`, `value_flow`, `automation_candidate`,
  `pilot_simulation`, `before_after_measurement`, `rollback_contract`)
  are structural validators only — same scope boundary as `schema/
  ADOPT.md`'s validator (conformance, not truth/safety).

## Limitations

`value_flow`'s `reviewable: false` severity is `WARNING`, not fatal, by
design — a named open human-judgment call (`HUMAN_DECISIONS.md` item 6),
worth reconsidering for an actual financial-audit deployment context.
No cross-session persistence for `PromotionStore`/`ContradictionRegistry`
(in-memory only) — `SourceRegistry` itself does persist to disk by
default (see `kpm/ADOPT.md`'s own correction). No cryptographic signing.

## Changelog

- 2026-08-25: initial build, 4-agent parallel construction, all 8
  schemas + gate + end-to-end demonstration.
- 2026-08-25: `PromotionRecord.history` frozen — closed the live
  exploit `confirm_pilot_authorized()` exists specifically to defend
  against.
- 2026-08-26: `authorize_pilot()` now requires `source_registry`/
  `source_hashes` and revalidates fresh before queueing — closing a real
  gap a multi-turn adversarial recon found: pilot authorization could
  previously be granted with zero connection to real, structurally
  validated candidate content. Existing tests updated (explicit break,
  not a silent compatibility shim) plus new tests proving the exact
  constructed bypass is now refused.
- `rpa/`'s own suite: 213 tests as of 2026-08-26.

## Fork guide

`rpa/gates/human_jurisdiction.py` depends on `kpm.promotion.
state_machine`; the 8 schema/validator pairs follow `schema/`'s pattern
independently. See `rpa/tests/test_end_to_end.py` for the full
LEGACY → MAP → BOTTLENECK → CANDIDATE → SIMULATION → AUTHORIZATION →
PILOT → MEASURE loop threaded through one coherent scenario — the
fastest way to see all 8 schemas actually connect. Run
`python3 -m unittest discover -s rpa -p "test_*.py"` to confirm the fork
is intact (207 tests as of 2026-08-26).

## Integration interfaces

Each schema module exports a `validate_*()` function following
`schema/validator.py`'s `Issue`/`ValidationResult` shape. `rpa/gates/
human_jurisdiction.py` exports exactly two functions:
`authorize_pilot()` (queue for review) and `confirm_pilot_authorized()`
(the only trustworthy authorization check — never trust `record.state`
directly for this purpose).

## Contribution path

None yet — see `firewall/ADOPT.md`'s note; same repository-wide state.
`.github/workflows/tests.yml` runs this subsystem's suite on every push/
PR to `kyle4814/titanos`.

## Machine-readable manifest

```yaml
subsystem: rpa
public_modules:
  - rpa.gates.human_jurisdiction
  - rpa.schema.legacy_system_map / rpa.validators.validate_legacy_system_map
  - rpa.schema.institutional_bottleneck / rpa.validators.validate_bottleneck
  - rpa.schema.value_flow / rpa.validators.validate_value_flow
  - rpa.schema.automation_candidate / rpa.validators.validate_automation_candidate
  - rpa.schema.pilot_simulation / rpa.validators.validate_pilot_simulation
  - rpa.schema.before_after_measurement / rpa.validators.validate_before_after_measurement
  - rpa.schema.rollback_contract / rpa.validators.validate_rollback_contract
runtime_dependencies: [PyYAML]
depends_on_subsystem: [kpm, magl]
test_command: python3 -m unittest discover -s rpa -p "test_*.py"
test_count: 207
known_limitation: value_flow's reviewable:false is WARNING not fatal (open human decision)
provenance: rpa/BUILD_REPORT.md
```

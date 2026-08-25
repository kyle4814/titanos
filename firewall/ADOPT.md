# Adopting `firewall/`

External-facing packaging doc — FRONTIER-008's first proof, distinct
from `BUILD_REPORT.md` (this subsystem's internal audit trail). This
file answers "how do I use, fork, or remove this," not "what was
decided and why."

## Thesis

Governs what may acquire runtime authority — narrower than "is this
claim true." Three parts: a rejection engine (`evaluate()`), a
quarantine state machine for contamination handling, and a dissent
register so disagreement never gets silently relabelled as
contamination. Zero runtime dependencies beyond the Python standard
library; no network, no external service.

## Quickstart

```python
from firewall.gate import Artifact, evaluate

artifact = Artifact(...)                    # see firewall/gate.py for fields
decision = evaluate(artifact, corroborating=())
# decision.to_dict() -> inspectable verdict; the artifact itself is
# never mutated or deleted, whatever the verdict is.
```

```python
from firewall.quarantine import QuarantineStore

store = QuarantineStore()
record = store.quarantine(artifact_id="a1", content="...", reason="...")
store.transition(artifact_id="a1", to_state=..., reviewed_by="human_name")
store.pending_review()   # never store.delete() -- no delete surface exists
```

```python
from firewall.dissent import DissentRegister

register = DissentRegister()
register.record(dispute_id="d1", subject="...", position=...)
register.resolve(dispute_id="d1", status=..., ...)
register.minority_positions()   # preserved, never discarded on resolution
```

## Failure cases

- `evaluate()` refusing an artifact does **not** delete or hide it —
  refused artifacts stay readable and archived, they simply cannot
  govern runtime policy. If your integration expects rejection to mean
  "gone," it will be surprised.
- `QuarantineStore.transition()` raises `IllegalTransition` for any
  edge not in `can_transition()`'s table — the table has no "delete"
  or "purge" target, by design (see `SIGIL_LEXICON.md`'s
  `SIGIL.NO_DELETE_SURFACE`).
- `DissentRegister.resolve()` does not erase `minority_positions()` —
  a resolved dispute still exposes the losing position on request.

## Threat model

- **In scope:** contamination masquerading as legitimate content,
  disagreement being mislabelled as contamination (the mirror-image
  failure `dissent.py` exists specifically to prevent), forged
  transition history (closed this session — `QuarantineRecord.history`
  is a frozen tuple, not a mutable list; see
  `foundation/tests/test_epistemic_state_immutability.py`).
- **Out of scope, known limitation:** single-reviewer authority —
  `reviewed_by` is a plain string, not cryptographically authenticated,
  and no four-eyes/N-of-M requirement exists yet. Repository-wide open
  item, tracked in `HUMAN_DECISIONS.md` item 4, not specific to this
  subsystem. Do not deploy this module as a security boundary against
  an adversary who can forge a `reviewed_by` value.

## Limitations

No cryptographic signing. No network calls. No async/concurrency
guarantees beyond what Python's GIL gives a single process — this store
is in-memory per instance, not a shared service; two processes each
holding their own `QuarantineStore()` do not see each other's state.

## Changelog

- 2026-08-25: `history` field frozen (tuple, not list) on
  `QuarantineRecord` — closed a live forged-entry exploit vector
  shared across five record types in this repository.
- Pre-existing: `gate.py`/`quarantine.py`/`dissent.py` built and tested
  (36 tests, `firewall/BUILD_REPORT.md`).

## Fork guide

This module has no dependency on any other subsystem in this
repository — `import firewall.gate`, `import firewall.quarantine`,
`import firewall.dissent` work standalone. To fork just this piece:
copy the `firewall/` directory and its `tests/`, drop the
`SIGIL_LEXICON.md` cross-references in the module docstrings (they are
provenance notes, not imports), run
`python3 -m unittest discover -s firewall -p "test_*.py"` to confirm
the fork is intact.

## Integration interfaces

`Artifact`, `Decision`, `QuarantineRecord`, `DisputeRecord`, `Position`
are the only public data shapes — all plain dataclasses, `to_dict()`
provided on each for serialization. No class in this subsystem expects
to be subclassed.

## Contribution path

None yet — this repository has no CONTRIBUTING.md or issue-triage
process. `.github/workflows/tests.yml` runs this subsystem's suite on
every push/PR to `kyle4814/titanos`; a passing run is the only current
bar. See `HUMAN_DECISIONS.md` for what remains a human judgment call.

## Machine-readable manifest

```yaml
subsystem: firewall
public_modules: [firewall.gate, firewall.quarantine, firewall.dissent]
runtime_dependencies: []
test_command: python3 -m unittest discover -s firewall -p "test_*.py"
test_count: 36
known_limitation: single-reviewer authority, no cryptographic signing
provenance: firewall/BUILD_REPORT.md
```

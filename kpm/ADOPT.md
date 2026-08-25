# Adopting `kpm/`

External-facing packaging doc — FRONTIER-008's third instance, same
template as `firewall/ADOPT.md`/`schema/ADOPT.md`. Distinct from
`kpm/BUILD_REPORT.md` (internal audit trail) and `kpm/constitution/
CONSTITUTION.yaml` (this subsystem's own doctrine).

## Thesis

Knowledge Production Machine — a bounded recursive pipeline for turning
raw source material into small, versioned, evidence-classified
"blueprint atoms." Distinct from `firewall/`'s job (gating artifacts
already in canonical shape): KPM is upstream of that, producing the
shape in the first place. Reuses `schema/`/`firewall/`'s house style
throughout (append-only no-delete stores, absence-of-edge transition
tables, fail-closed exceptions) rather than inventing a second one.
Zero runtime dependency beyond PyYAML.

## Quickstart

```python
import sys
sys.path.insert(0, "kpm/source-vault")   # hyphenated dir, not a valid
                                          # package path -- see Failure cases
from registry import SourceRegistry

registry = SourceRegistry()
record = registry.ingest_source(
    b"raw content", source_type="text",
    source_location="...", author_or_origin="...",
)   # hashed, archived, provenance_status="UNVERIFIED" by default
```

```python
from kpm.schemas.epistemic_types import classify_claim, reclassify

claim = classify_claim("C1", "some text", "SPECULATIVE_HYPOTHESIS",
                        classified_by="you", confidence="LOW")
reclassify(claim, "EVIDENCE_SUPPORTED_MODEL", "new evidence", "you",
           evidence_refs=("...",))
# mutates claim in place and returns the same object -- there is no
# separate "new" claim to reassign
```

```python
from kpm.promotion.state_machine import PromotionStore

store = PromotionStore()
rec = store.register("BP-1", created_by="you")
for state in ("DISTILLED", "PROVISIONAL", "TESTED"):
    store.promote("BP-1", to_state=state, reason="advancing")
store.promote("BP-1", to_state="STABLE", reason="reviewed",
               reviewed_by="reviewer")
# reviewed_by must differ from created_by, checked by value -- self-review
# is refused even if you just pass your own name. RAW -> TESTED directly
# is illegal -- there is no shortcut edge, only the full chain above.
```

```python
from kpm.contradictions.registry import ContradictionRegistry
# evidence-gated, minority-position-preserving -- see firewall/dissent.py
# for the sibling pattern this mirrors
```

## Failure cases

- `kpm/source-vault/` is a **hyphenated directory name** — not a legal
  Python package identifier. `import kpm.source_vault...` will not work;
  use the `sys.path.insert` workaround shown above (same one this
  subsystem's own tests use).
- `classify_claim(..., confidence="HIGH")` raises `ConfidenceNotEarned`
  for classifications whose entire epistemic identity is "not yet
  evidenced enough" (`SPECULATIVE_HYPOTHESIS`, `CREATIVE_CONCEPT`,
  `SYMBOLIC_DOCTRINE`, `UNKNOWN`) — this is enforced, not advisory.
- `PromotionStore.promote()` raises on any transition not in the
  explicit table — there is no STABLE edge from RAW, DISTILLED,
  PROVISIONAL, CONTESTED, or QUARANTINED; only TESTED and HUMAN_REVIEW
  have one. Self-review (`reviewed_by` == `created_by`) is refused.
- `Claim.history` and `PromotionRecord.history` are frozen tuples, not
  mutable lists (fixed 2026-08-25, `EPISTEMIC_INTEGRITY_002`) — calling
  `.append()` on either raises `AttributeError`. A caller that mutated
  history directly to forge provenance before that fix no longer can.

## Threat model

- **In scope:** forged classification/promotion history (closed this
  session — see Failure cases above), self-review bypass (refused),
  unevidenced claims entering high-confidence/evidentiary classes
  (blocked by `_require_confidence_earned`/`_REQUIRES_EVIDENCE_TO_ENTER`).
- **Out of scope, known limitation:** single-reviewer authority —
  `reviewed_by`/`classified_by` are plain strings, not cryptographically
  authenticated; no four-eyes/N-of-M requirement. Repository-wide open
  item, `HUMAN_DECISIONS.md` item 4.

## Limitations

**Correction, verified 2026-08-26:** `SourceRegistry` is NOT in-memory
only — by default it persists real, content-addressed data to disk
(`kpm/source-vault/registry.jsonl` + `kpm/source-vault/archive/*.blob`),
reloading on construction. This was found and corrected after this
session's own `FIRST_PING.md` ingestion calls actually wrote real files
into the tracked repository, contradicting an earlier draft of this
doc's blanket "no persistence layer" claim. `PromotionStore` and
`ContradictionRegistry` genuinely are in-memory per process instance —
nothing they hold survives a restart. No cryptographic signing on any
store. No network calls anywhere in this subsystem.

## Changelog

- 2026-08-25: `Claim.history`/`PromotionRecord.history` frozen (tuple,
  not list) — closed a live forged-entry authorization-bypass exploit
  reachable through `rpa/gates/human_jurisdiction.py`.
- 2026-08-25: initial build, 4-agent parallel construction, 228 tests
  passing at integration time (including pre-existing `schema/`/
  `firewall/`/`legacy/` regression); `kpm/`'s own suite is 102 tests as
  of 2026-08-26.

## Fork guide

`kpm/source-vault/registry.py`, `kpm/schemas/epistemic_types.py`,
`kpm/promotion/state_machine.py`, `kpm/contradictions/registry.py` are
independently importable (mind the hyphenated-directory workaround for
the first). To fork just this piece: copy `kpm/` and its `tests/`
subdirectories, run `python3 -m unittest discover -s kpm -p "test_*.py"`
to confirm the fork is intact (102 tests as of 2026-08-26).

## Integration interfaces

`SourceRecord`, `Claim`, `PromotionRecord` are the public data shapes
(dataclasses, `to_dict()` provided). `kpm/constitution/CONSTITUTION.yaml`
documents the doctrine two of its claims are cross-verified against real
code (`forbidden_promotion_transitions` matches
`state_machine.py::TRANSITIONS` exactly) — read it before assuming a
constitutional claim is aspirational rather than enforced.

## Contribution path

None yet — see `firewall/ADOPT.md`'s note; same repository-wide state.
`.github/workflows/tests.yml` runs this subsystem's suite on every push/
PR to `kyle4814/titanos`.

## Machine-readable manifest

```yaml
subsystem: kpm
public_modules:
  - kpm.source_vault.registry   # via sys.path workaround, see above
  - kpm.schemas.epistemic_types
  - kpm.schemas.blueprint_atom
  - kpm.promotion.state_machine
  - kpm.contradictions.registry
runtime_dependencies: [PyYAML]
test_command: python3 -m unittest discover -s kpm -p "test_*.py"
test_count: 102
known_limitation: SourceRegistry persists to disk by default (kpm/source-vault/), PromotionStore/ContradictionRegistry do not; single-reviewer authority only
provenance: kpm/BUILD_REPORT.md, kpm/constitution/CONSTITUTION.yaml
```

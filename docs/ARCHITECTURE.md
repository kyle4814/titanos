# TitanOS Epistemic Integrity Library — Architecture

## The four layers, and the question each one answers

| Layer | File | Question it answers |
|---|---|---|
| Parser/Validator | `schema/validator.py` | Can this be structurally understood, and does it conform to the declared schema? |
| Provenance | `provenance/` (separate package: `titanos-provenance`) | Where did this come from, and has its integrity been preserved? |
| Contamination gate | `firewall/gate.py` | Does this violate a known architectural constraint? May it influence runtime? |
| Quarantine / Dissent | `firewall/quarantine.py`, `firewall/dissent.py` | If held or disputed, is it preserved, reviewable, and recoverable? |

**IMPLEMENTATION**: these are four separate modules with no shared mutable
state. None calls into another to make its own decision — `validator.py`
never asks the gate anything, `gate.py` never re-parses YAML. Composition
happens at the call site, not inside any one layer, so no layer can quietly
absorb another's responsibility.

**SPECIFICATION**: none of the four layers ever answers "is this true."
That question is out of scope for all of them, by design (see
`THREAT_MODEL.md`).

## Data flow (as implemented today)

```
raw YAML text
   -> schema/validator.py::validate_artifact()   -> ValidationResult (VALID/INVALID)
   -> [not yet wired] provenance verification     -> VALID/INVALID/UNKNOWN/PROVENANCE_FAILURE
   -> firewall/gate.py::evaluate()                -> AUTHORIZED/REFUSED/QUARANTINED/REQUIRES_HUMAN_REVIEW
   -> firewall/quarantine.py (if QUARANTINED)      -> held, preserved, human-reviewable
   -> firewall/dissent.py (if disputed)            -> DISPUTED, never silently resolved
```

**ASSUMPTION, stated plainly**: this pipeline is not wired end-to-end
anywhere in this repository. Each stage is independently built and tested;
no ingest path calls all four in sequence yet. Wiring it is explicitly
withheld pending the human decision in `legacy/DECISION_PACKET.md`.

## What is NOT sovereign (the absolute invariant, restated as architecture)

No module in this tree grants itself the authority to move an artifact to
AUTHORIZED. `evaluate()` computes a verdict from declared, checkable facts;
`QuarantineStore.transition()` requires `reviewed_by` to leave QUARANTINED;
`DissentRegister.resolve()` requires evidence, never a vote count. Every one
of these is a refusal to let the machine be the final word — **VERIFIED
PROPERTY**, confirmed by `firewall/tests/` (36/36) and
`schema/tests/test_meta_attack.py` (13/13).

## Repository layout

```
schema/       artifact_schema.py, validator.py, tests/
firewall/     gate.py, quarantine.py, dissent.py, tests/
legacy/       classify.py, DECISION_PACKET.md, manifests/, tests/
doctrine/     doctrine-001.yaml, doctrine-002.yaml, POLE_REVERSAL_DOCTRINE.yaml
compiler/     coverage.py (doctrine <-> code <-> test consistency checker)
provenance/   seal.py (this library's own release manifest — not the
              cryptographic provenance package, which lives in the
              separate titanos-provenance repository)
failures/     FAILURE_ARCHIVE.md — every defect found, real or false-positive
docs/         this file and its siblings
```

## UNRESOLVED QUESTIONS

- Whether the four layers should be composed into a single `ingest()`
  entry point, or remain separately callable so a caller can use only the
  layers it needs. No decision has been made; composing them is easy once
  decided, so the delay costs little.
- Whether provenance verification (the `titanos-provenance` package) should
  become a dependency of this repository or stay separate. Currently
  separate (§Zero-Dependency Principle — no dependency added before it's
  decided necessary).

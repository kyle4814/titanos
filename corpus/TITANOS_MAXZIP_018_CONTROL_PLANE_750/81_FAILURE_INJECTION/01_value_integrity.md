# TITANOS — 81_FAILURE_INJECTION / value_integrity

## Mission
Define a production-grade contract for `value_integrity` within `81_FAILURE_INJECTION`.

## Mandatory order
RECON → SEARCH → REUSE → IMPLEMENT → TEST → BLUE TEAM → CALIBRATE → RECEIPT → VALUE → PARETO.

## Invariants
- one canonical source of truth
- explicit inputs and outputs
- explicit failure states
- provenance for external observations
- durable receipts
- modelled / observed / realized value separation
- configuration switches enforced at execution boundaries
- no silent fallback
- no unsupported commercial claims

## Acceptance
Implementation is not complete until the relevant tests and durable receipt exist.

# TITANOS — 40_DEPENDENCY_GRAPH / deadline

## Purpose
Define a bounded, auditable implementation surface for `deadline`.

## Required sequence
RECON → SEARCH → REUSE → VERIFY → IMPLEMENT → TEST → DEMONBLADE → RECEIPT → PARETO.

## Valuation doctrine
A numerical value is a **modelled estimate unless supported by realized financial evidence**.
Never represent modelled value as revenue, profit, cash, investment return, or customer value.

## Required fields
- evidence_id
- source
- timestamp
- state
- confidence
- assumptions
- cost_basis
- value_basis
- reuse_basis
- risk_basis
- verification_status

## Acceptance
No silent assumptions. No duplicate source of truth. No canonical state in temporary storage.

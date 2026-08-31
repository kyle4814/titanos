# TITANOS — REJECT

DOMAIN: 06_DEMONBLADE_SECURITY
PACKAGE: MAX NUKE 010
STATUS: DRAFT ENGINEERING FEEDSTOCK
VERSION: MAGL-V12

## PURPOSE
Define a bounded, testable responsibility for `reject`.

## INPUTS
- canonical state
- explicit task scope
- authorised dependencies
- versioned configuration
- relevant evidence

## OUTPUTS
- result
- status
- evidence references
- errors / blockers
- receipt metadata
- next action

## ENGINEERING RULES
1. Inspect existing implementation before creating new implementation.
2. Preserve provenance and lineage.
3. Distinguish proposed, implemented, tested, verified and validated states.
4. Never invent missing facts.
5. Bound side effects and permissions.
6. Make failure behaviour explicit.
7. Add tests before promotion.

## PARETO
Prefer the smallest change that unlocks the greatest verified downstream capability.

## DEMONBLADE
Attack assumptions, duplicated responsibility, stale state, missing evidence,
unsafe permissions and hidden coupling before promotion.

## GERMAN ENGINEER
TRACEABLE → REPRODUCIBLE → TESTED → SIMPLE → SECURE → MEASURABLE.

NICHT MEHR. NICHT WENIGER.

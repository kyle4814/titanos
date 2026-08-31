# TITANOS — AGENT TESTS

PACKAGE: MAX NUKE 013
DOMAIN: 03_AGENT_FLEET
STATUS: DRAFT STACK SPECIFICATION

## PURPOSE
Define a bounded responsibility for `agent_tests` within the TitanOS stack.

## STACK CONTRACT
RECON → CONTRACT → IMPLEMENT/REUSE → TEST → ATTACK → VERIFY → RECEIPT → PROMOTE

## RULES
- inspect the repository before changing it
- reuse existing capability before creating a duplicate
- preserve provenance and versioning
- keep interfaces explicit
- bound side effects
- define failure and recovery
- test consequential behaviour
- distinguish observed facts from proposals and forecasts

## PARETO
Prefer the smallest verified delta that unlocks the most downstream capability.

## DONE
Implementation or verified reuse + tests + evidence + receipt + state update.

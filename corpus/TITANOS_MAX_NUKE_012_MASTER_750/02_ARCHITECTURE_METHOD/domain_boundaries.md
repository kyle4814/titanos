# TITANOS — DOMAIN BOUNDARIES

PACKAGE: MAX NUKE 012
DOMAIN: 02_ARCHITECTURE_METHOD
STATUS: DRAFT ENGINEERING DOCTRINE

INTENT
Define a bounded, auditable rule for `domain_boundaries`.

PROCESS
RECON → MAP → DESIGN → IMPLEMENT → TEST → ATTACK → VERIFY → RECEIPT → PROMOTE

INVARIANTS
- inspect before changing
- reuse before rebuilding
- preserve provenance
- bound side effects
- make failure explicit
- test consequential behaviour
- distinguish proposals from verified capabilities
- never manufacture evidence

PARETO
Prefer the smallest verified change that unlocks the greatest downstream value.

DEMONBLADE
Attack assumptions, stale state, duplication, concurrency, permissions,
failure recovery, false precision and unsupported claims.

PROMOTION
No promotion without acceptance criteria, tests, evidence and a traceable receipt.

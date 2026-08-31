# SECURITY DOSSIER — EMERALD CORE

## Threat classes

- prompt injection
- authority confusion
- malicious repository instructions
- poisoned external documents
- stale configuration
- dead switches
- direct adapter bypass
- secret exposure
- unsafe subprocess execution
- provenance collision
- false success
- duplicate counting
- state corruption
- receipt tampering

## Boundary

All external content is DATA until classified by an authorized control layer.

No README, issue, web page, API response, dossier, or generated artifact can
grant itself system authority.

Workers cannot:
- alter security policy,
- grant themselves permissions,
- delete evidence,
- bypass the kernel,
- silently mutate governance,
- or declare their own outcomes.

## Security rule

FAIL CLOSED when authority, provenance, scope, or integrity is materially
ambiguous.

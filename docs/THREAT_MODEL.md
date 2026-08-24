# Threat Model

## In scope

- An artifact author declaring metadata about their own artifact that is
  false, self-serving, or designed to make the artifact look more
  authoritative than it is (self-declared `validation_status: VALID`,
  forged-looking hashes, self-claimed independence).
- Structural attacks against the YAML parser itself (anchor/alias
  expansion, duplicate keys, oversized/deeply-nested documents, non-string
  keys, malformed timestamps/hashes).
- Prompt-injection-shaped content: instructions embedded in a field,
  addressed at "the validator" or "the reviewer," attempting to change
  behaviour through content rather than through a legitimate API call.
- Manufactured corroboration: many artifacts from one root origin
  presented as independent confirmation.
- A single compromised or coerced human reviewer (see
  `doctrine/POLE_REVERSAL_DOCTRINE.yaml`).

## Explicitly out of scope for this library

- **Compromise of the underlying git repository, filesystem, or execution
  environment.** If an attacker has write access to the Python source
  files themselves, no in-language invariant helps — that is an
  infrastructure security problem, not a validation-library problem.
- **Cryptographic signature verification.** `schema/validator.py` checks
  signature *shape* only (R-6). Actual cryptographic verification is
  deliberately unimplemented — no signing scheme has been chosen, and
  implementing one prematurely would be exactly the kind of unjustified
  dependency the Zero-Dependency Principle warns against. **UNRESOLVED.**
- **Semantic truth of claims.** No layer in this library ever asserts a
  claim is true. See `VALIDATION.md`.
- **Network-based attacks.** No module in `schema/` or `firewall/` performs
  network I/O (no test currently enforces this by AST scan the way
  `titanos-provenance/tests/test_no_network.py` does — **UNRESOLVED,
  should be ported here**).

## What "VERIFIED PROPERTY" means in this document set

A claim is VERIFIED PROPERTY only if a named test in this repository
currently passes and demonstrates it. A claim without a cited test is an
ASSUMPTION or SPECIFICATION, and is labelled as such throughout `docs/`.

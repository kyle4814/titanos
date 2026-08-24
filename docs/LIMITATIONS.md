# Limitations

Stated plainly, not buried in prose elsewhere.

1. **Single-reviewer authority.** One `reviewed_by` string releases a
   quarantined artifact or resolves a dispute. No independent second
   reviewer is required. See `doctrine/POLE_REVERSAL_DOCTRINE.yaml`,
   PR-I-04.
2. **`reviewed_by` is unauthenticated.** Free text, not a cryptographically
   bound identity. PR-I-05.
3. **No end-to-end wiring.** `schema/validator.py`, `firewall/gate.py`,
   `firewall/quarantine.py`, `firewall/dissent.py`, and the provenance
   package are each independently tested but not composed into a single
   ingest pipeline anywhere in this repository.
4. **No cryptographic signature verification.** `signature` is shape
   checked only (R-6).
5. **False-negative coverage on the legacy corpus is unmeasured.** 2,952
   files parse as YAML but don't conform to the TitanOS schema; none were
   evaluated for semantic contamination, because the schema has no
   mechanism to detect that in a file that doesn't declare TitanOS fields
   at all. See `legacy/DECISION_PACKET.md`.
6. **Doctrine amendment provenance relies on git history**, which this
   library does not model as an attack surface (see F-007,
   `failures/FAILURE_ARCHIVE.md`, for a concrete case in a different repo).
7a. **Quarantine reason is checked for non-emptiness, not for substance.**
   `s.quarantine(reason="x")` passes the same check as a genuine
   explanation — found during the §Phase 12 second adversarial pass. Not
   fixed: a "reason must be substantive" check would need a definition of
   substantive this library has no principled way to enforce (a length
   minimum is trivially gamed), so this is recorded as an open limitation
   rather than papered over with a check that only looks like a fix.
7. **Metadata-only classification.** `firewall/gate.py` classifies
   *declared* fields. A hostile author who forges provenance and mislabels
   NARRATIVE as EVIDENCE defeats the metadata layer; only independent
   corroboration (also gameable if ancestry is faked well enough) and
   human review catch that. Stated in `gate.py`'s own docstring.

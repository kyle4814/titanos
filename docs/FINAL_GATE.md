# §Phase 15 — Final Gate

Each answer cites the test that backs it. "No" backed by a test is a
stronger claim than "no" backed by confidence.

**1. Can malformed YAML bypass validation?**
No, for the classes tested. `schema/tests/test_false_negatives.py` and
`test_meta_attack.py` (37 tests) throw duplicate keys, alias fan-out, deep
nesting, oversized documents, non-string keys, and type confusion at it;
all resolve to `INVALID`, none to `VALID`, none crash uncaught. Two real
bypasses were found and closed during this work (RecursionError on deep
alias chains; TypeError on non-string keys against the real corpus) — both
are now regression tests. **Not a claim of exhaustive coverage.**

**2. Can an artifact redefine its own validation rules?**
No. Fields like `transitions`, `override_rules`, `bypass_validation` are a
fixed forbidden-key list (R-11) checked structurally; no code path reads
artifact content as configuration. `TestChangeTheTransitionTable` asserts
the module-level `TRANSITIONS` dict is byte-identical before and after an
artifact claims to demand a change.

**3. Can an artifact self-authorize?**
No. `AUTHORIZED_RUNTIME_CLASSES` excludes self-referential classes;
`generated_by_agent` without `independently_confirmed_by` routes to
`REQUIRES_HUMAN_REVIEW`, never `AUTHORIZED`
(`TestSelfMythology::test_agent_cannot_self_authorize`). A field literally
named `validation_status: VERIFIED` is flagged (R-10), not honoured.

**4. Can quarantine be bypassed?**
Partially open, honestly. No code path skips quarantine when
`contamination_state` is terminal-blocking. But nothing *forces* an
artifact's `contamination_state` to be set accurately in the first place —
that depends on whatever computed it upstream, which is outside this
library's scope. **This gate cannot answer for input it never receives.**

**5. Can quarantine be silently erased?**
No. No delete/purge/clear/remove/drop method exists on `QuarantineStore`.
Verified by `hasattr()` in two independent test files.

**6. Can disagreement disappear?**
No. `resolve()` never removes a `Position`; minority positions are
queryable after resolution via `minority_positions()`.

**7. Can common provenance masquerade as independence?**
No, when `root_origin` is honestly declared — `collapse_ancestry()` counts
distinct origins, not artifacts. **Yes, if `root_origin` itself is forged**
— schema validation checks shape, not truth (documented explicitly in
`PROVENANCE.md`, not a silent gap).

**8. Can valid cryptography masquerade as truth?**
Structurally, no — R-6 checks signature *shape*, and no code anywhere
treats a well-formed signature as a truth claim; `TestStaleAndValidSignatureOverInvalidSemantics`
tests this directly. **No cryptographic verification is implemented at
all**, so this answer is currently vacuous rather than hard-won — see
`LIMITATIONS.md` item 4.

**9. Can schema evolution create an authorization bypass?**
No. A declared `schema_version` that doesn't match the implemented version
is `INVALID` (R-9), never assumed forward-compatible.

**10. Can UNKNOWN silently become AUTHORIZED?**
No. `UNKNOWN` is absent from `AUTHORIZED_RUNTIME_CLASSES` by construction;
`TestGateSurface::test_allowlist_excludes_all_interpretive_classes` checks
the allowlist directly, not behaviour that could drift from it.

**11. Can the validator suppress criticism of TitanOS?**
No. `TestNotAnIdeologicalFilter` runs a governance rule that names itself
`titanos-is-wrong-about-scoring` through the gate and gets `AUTHORIZED` on
the same terms as any other rule. This is the single test worth re-running
after any future change to `gate.py`.

**12. Can the validator become an unaccountable authority?**
No single module can — `validate_artifact()` returns a structural verdict
only, `evaluate()` a gate verdict only, and neither can move an artifact to
`AUTHORIZED` by itself; that requires passing through `quarantine.py`'s
`VERIFIED` state with a named `reviewed_by`. **The reviewer itself is
currently unaccountable** in the sense that `reviewed_by` isn't verified —
see #4 in LIMITATIONS.md and PR-I-05 in the pole reversal doctrine. This is
the honest edge of the claim.

**13. Can the 3,058 legacy artifacts be classified without human
judgment?**
No. Every record in both Track A and Track B carries
`review_required: true`. Zero files were auto-promoted past that in this
run.

**14. If not, exactly where must human judgment remain?**
- Whether to spend review budget on the 2,952 `UNRECOGNISED_YAML` files at
  all (`legacy/DECISION_PACKET.md`, question 2).
- Whether to re-scan the 106 permission-denied files with elevated access
  (question 1).
- Who is authorized as `reviewed_by` for quarantine release and dispute
  resolution — currently unenforced (limitation #1/#2).
- Whether/how to wire these four independently-tested layers into an
  actual ingest pipeline (`ARCHITECTURE.md`, unresolved question).

None of these four points were decided by this work. They are named so
they can be decided.

# Quarantine

Source: `firewall/quarantine.py`.

## What quarantine is, and is not

Quarantine is not a verdict of falsehood. It means: this artifact could
not be verified through the required gates, so it is held, preserved, and
routed to a human. Conflating "unverified" with "false" is how a safety
filter becomes a censor — **SPECIFICATION**, stated directly in the
module's own docstring and tested (`firewall/tests/test_firewall.py::TestContaminationStates::test_quarantine_preserves_rather_than_deletes`).

## The transition table

`TRANSITIONS: Mapping[ContaminationState, frozenset[ContaminationState]]`.
Enforcement is the *absence* of an edge, not a runtime check:
`CONTAMINATED` and `QUARANTINED` have no path to `AUTHORIZED` in the table
itself. **VERIFIED PROPERTY**
(`firewall/tests/test_quarantine_dissent.py::TestNoPathToExecution`,
re-verified from the attacker's side in
`schema/tests/test_meta_attack.py::TestChangeTheTransitionTable`).

Release from `QUARANTINED` requires a non-empty `reviewed_by` — automated
release would reduce quarantine to a timer. **VERIFIED PROPERTY**
(`test_release_requires_a_human`).

## No delete surface

`QuarantineStore` has no `delete`, `purge`, `clear`, `remove`, or `drop`
method — not refused at runtime, absent from the class. **VERIFIED
PROPERTY**, checked via `hasattr()` in two independent test files
(`firewall/tests/test_quarantine_dissent.py`,
`schema/tests/test_meta_attack.py::TestDeleteQuarantineRecordAttempt`).

## Known limitation (see also POLE_REVERSAL_DOCTRINE.yaml, PR-I-04/05)

A single `reviewed_by` string is sufficient today to release a quarantined
artifact. No independent second-reviewer requirement exists, and
`reviewed_by` is an unverified free-text field, not a cryptographically
bound identity. **NOT_ENFORCED, stated as an open gap, not glossed over.**

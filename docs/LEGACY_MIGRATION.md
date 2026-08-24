# Legacy Migration

Source: `legacy/classify.py`, `legacy/DECISION_PACKET.md`.

## What exists

A read-only scanner (`scan_corpus()`) that found **3,058 real YAML files**
across `/home/tech2` (excluding this repository, `.git`, `node_modules`)
at scan time 2026-08-25 — matching the figure independently reported by
the earlier `titanos-public-staging/audit/PUBLICATION_READINESS_REPORT.md`
audit, cross-checked live rather than assumed still accurate.

Two classification tracks were run against the real corpus (not a
simulation): `classify_track_a()` (100% default UNKNOWN) and
`classify_track_b()` (validator-assisted, still defaulting to UNKNOWN or
`REVIEW_REQUIRED`/`UNRECOGNISED_YAML`, never past it). Results:
`legacy/manifests/track_a.json`, `legacy/manifests/track_b.json`.

## What was found (VERIFIED, from the actual scan)

- 0 files structurally conform to the TitanOS artifact schema (expected —
  none were authored against it).
- 2,952 files parse as valid YAML but don't conform (`UNRECOGNISED_YAML`).
- 106 files were unreadable (permission denied), concentrated in
  `clawd_backup/moneyprinter/.claude/worktrees/*` and a directory literally
  named `worldmonitor-quarantine`.
- **Every record in both tracks carries `review_required: true`.** No file
  was auto-promoted past that, in either track.

## What was NOT done

- No source file was modified, renamed, or deleted. `legacy/tests/test_classify.py::test_no_source_file_is_modified`
  verifies this directly.
- No file was wired into any ingest path or given runtime authority.
- No recommendation was made on the two open questions in
  `legacy/DECISION_PACKET.md` (re-scan permission-denied files? spend
  review budget on the 2,952-file bucket?). Both are human decisions.

## UNRESOLVED

Whether Track B's `REVIEW_REQUIRED` bucket should ever be nonzero in
practice (it was 0 against this corpus — no legacy file happened to be
schema-conformant) and what review workflow would apply if it were.

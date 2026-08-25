# Legacy Corpus Decision Packet — 3,058 YAML Files

**Status: NO DECISION MADE. This packet exists to inform one, not to make one.**

Generated 2026-08-25 against the real, live corpus at scan time —
`find /home/tech2 -iname '*.yaml' -o -iname '*.yml'`, excluding `.git`,
`node_modules`, and `cosmic-library` itself. **3,058 files**, confirmed
live (this is the same figure the earlier `PUBLICATION_READINESS_REPORT.md`
audit reported independently — cross-checked, not assumed still true).

Raw output: `legacy/manifests/track_a.json`, `legacy/manifests/track_b.json`
(regenerate locally via `python3 legacy/classify.py` — **not tracked in
git**, added 2026-08-25 as part of pre-publication review: the manifests
contain full filesystem paths from outside this repository, and inspecting
them showed they reveal the names and directory structure of unrelated
private projects on the scanning machine — e.g. project codenames under
`clawd_backup/`. That's a real, if modest, information-disclosure risk
for a public repository, unrelated to anything this packet is actually
about. Excluded from tracking rather than redacted-in-place, since the
raw paths were never load-bearing for any test — only the aggregate
statistics below are. This exclusion is itself logged, not silent, per
the standing rule against hiding what was found.)

---

## WHAT IS KNOWN

- 3,058 real `.yaml`/`.yml` files exist across `/home/tech2` outside this
  library's own tree.
- **0 of 3,058** structurally conform to the TitanOS artifact schema
  (`schema/artifact_schema.py`). This is the expected result, not a
  finding of contamination — the schema is new; nothing in the legacy
  corpus was ever authored against it.
- **106 files (3.5%)** could not be read at all (permission denied — every
  single one, no exceptions found; the actual list is in
  `legacy/manifests/track_b.json`). These are concentrated in
  `clawd_backup/moneyprinter/.claude/worktrees/*` and
  `clawd_backup/worldmonitor-quarantine/*` — files under restrictive
  permissions, several already sitting in a directory literally named
  `quarantine`.
- **2,952 files (96.5%)** parsed as valid YAML but failed TitanOS schema
  validation. Issue counts cluster at 7 (2,180 files) and 8 (580 files) —
  consistent with most legacy files being missing the same handful of
  TitanOS-specific required fields (`content_hash`, `contamination_state`,
  `classification`, etc.) that no legacy format would have used, rather
  than 2,952 independent, unrelated problems.
- File sizes range 0 – 1.8MB, mean ~64KB. No file exceeded the validator's
  structural ceilings during this scan.
- Content hashes (sha256) were computed for every readable file and are
  recorded in the manifest — the corpus's current state is now
  content-addressed even though nothing about it has been classified as
  trustworthy.

## WHAT IS UNKNOWN

- Whether any of the 2,952 "doesn't conform" files are individually
  contaminated, malicious, or merely legitimately pre-TitanOS. Schema
  non-conformance answers a structural question, not that one.
- What the 106 permission-denied files contain. Their names (backup
  snapshots, worktree state, OpenAPI specs from a repo already named
  "quarantine") are suggestive, not evidence.
- Whether any file among the 3,058 was authored, edited, or influenced by
  an untrusted party. Provenance for this corpus was never tracked at
  authoring time, so there is no chain to verify — schema validation
  cannot manufacture provenance history that was never recorded.

## WHAT THE VALIDATOR CAN PROVE

- That a given file's YAML is well-formed or not (deterministically,
  reproducibly, by anyone re-running `schema/validator.py`).
- That a given file does or does not declare the fields, types, enums, and
  provenance shape the TitanOS artifact schema requires.
- That a file does not contain a structural self-authorization attempt
  (R-10/R-11 rules — declaring `validation_status: VALID` about itself,
  redefining transition rules, etc.). None of the 3,058 files triggered
  R-10/R-11 in this scan; if any had, it would be visible in the manifest.

## WHAT IT CANNOT PROVE

- That a schema-non-conformant file is safe, false, or unimportant.
- That a schema-conformant file (hypothetically, in a future scan) is
  actually true, actually intended as a TitanOS artifact, or actually
  authored by whoever it claims.
- Anything about the 106 unreadable files — a scan that cannot read a file
  has no basis for any classification stronger than UNKNOWN.

## THE TWO TRACKS, COMPARED

| | Track A (all default) | Track B (validator-assisted) |
|---|---|---|
| UNKNOWN | 3,058 (100%) | 106 (3.5%) |
| UNRECOGNISED_YAML (parses, non-conformant) | 0 | 2,952 (96.5%) |
| REVIEW_REQUIRED (schema-VALID, still gated) | 0 | 0 |
| Human review needed before any status change | 3,058 | 3,058 |

**Every single record in both tracks carries `review_required: true`.**
Track B narrows *what a human needs to look at first* (106 unreadable
files, then 2,952 categorized-by-missing-field files) — it does not narrow
*who gets to decide their status*. That decision stays human in both
tracks, by construction (§Phase 9: "each file must initially receive
UNKNOWN unless objective machine-verifiable criteria establish another
classification" — and no file in this corpus met that bar).

## FALSE-POSITIVE / FALSE-NEGATIVE RISK

- **False-positive risk (legitimate file wrongly flagged as suspicious):**
  LOW for the 2,952 UNRECOGNISED_YAML files — non-conformance to a schema
  invented after they were written is not a suspicion signal, and the
  packet says so explicitly rather than implying otherwise.
- **False-negative risk (contaminated file wrongly passed through):**
  UNMEASURED. Schema validation was never capable of catching semantic
  contamination in files that don't even declare TitanOS fields — this is
  a coverage gap, not a clean bill of health. A file could contain
  arbitrary malicious YAML content and still land in the same
  UNRECOGNISED_YAML bucket as an innocuous legacy config.

## SCHEMA / PROVENANCE COVERAGE

- Schema coverage of the corpus: 0% (no file was authored against this
  schema; expected).
- Provenance coverage: 0% verifiable (no file in this corpus carries a
  `root_origin`/`content_hash`/`signature` triplet that could be checked
  against an actual origin — schema-level shape checks aside, there is no
  provenance CHAIN to walk for pre-existing files).
- Unknown-field frequency: dominated by the *absence* of TitanOS-specific
  fields rather than presence of unrecognised ones — these files simply
  predate the vocabulary, they don't contradict it.

## WHAT WOULD BE LOST BY AUTOMATIC CLASSIFICATION

Any automatic promotion of "parses as YAML" or "resembles other files in
this corpus" to a trusted state would silently discard the one fact this
scan actually established: **none of these files have ever been checked
against anything**. Automating past that erases the exact distinction
(structural validity vs. epistemic trust) this whole directive exists to
preserve.

## WHAT WOULD BE GAINED

A one-time human triage pass, informed by this packet, would let scarce
review attention go first to the 106 unreadable files (smallest set,
already the most suspicious by virtue of being inaccessible) rather than
spreading it evenly — and would let the 2,952-file bucket be skimmed in
batches by shared issue signature (7-issue and 8-issue clusters) rather
than file-by-file.

## RISKS

- Doing nothing indefinitely leaves 3,058 files permanently unclassified —
  not dangerous by itself, but it means any future ingest pipeline that
  *does* get built has no pre-existing signal to draw on, and someone will
  eventually be tempted to bulk-approve them under time pressure. This
  packet is the artifact that should be pointed at when that temptation
  shows up.
- Reviewing 2,952 files by hand is a real cost. Nothing in this packet
  recommends spending it — that tradeoff belongs to whoever owns the time
  budget, not to this tool.

## HUMAN DECISION REQUIRED

1. Should the 106 permission-denied files be re-scanned with elevated
   access, or left untouched (they may be intentionally restricted)?
2. Is a one-time human triage of the 2,952 UNRECOGNISED_YAML files worth
   the review cost, given the false-negative gap above — or should this
   corpus remain permanently UNKNOWN/out-of-scope for TitanOS ingest?
3. If triage proceeds: who reviews, and does release from UNKNOWN require
   the same reviewed_by discipline as `firewall/quarantine.py`, or a
   lighter process (this packet does not recommend either)?

No recommendation is given for question 2 or 3. Manufacturing one to avoid
sitting with the uncertainty is exactly what this document exists to
refuse to do.

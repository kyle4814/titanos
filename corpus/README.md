# The Cosmic Library

The raw TITANOS corpus as delivered — 24 archives, 14,215 files, extracted
byte-for-byte with no file edited.

## What this is, and what it is not

**This is input material, not this repository's code.** Nothing in here is
imported, executed, or tested by any suite. It is deliberately excluded
from every production-code scanner (`sentinel`, `sigil`,
`capability_registry`, and the network/README guards) for exactly that
reason — a scan that walks delivered material would report its contents as
this project's own capabilities, which is the confusion this file exists
to prevent.

Publishing it does not promote it. Nothing here has passed a gate.

## What it contains

| | |
|---|---|
| archives | 24 |
| files | 14,215 |
| unique by content hash | 13,225 |
| exact byte duplicates | 990 |
| size | ~60 MB |

By type: 7,158 YAML · 5,304 Markdown · 924 Python · 825 JSON · 4 other.

`MANIFEST.json` carries per-archive file counts, byte totals and a
deterministic tree hash for each, so any archive can be checked against
what was delivered.

## An honest note on duplication

990 files are exact byte duplicates — one file appears 48 times across
archives (`SIGILS.yaml`, `METRICS.yaml`). The campaign's own triage
instrument (`foundation/corpus_triage.py`, whose `structural_key()`
strips wording and keeps shape) repeatedly measured these deliveries as
**structural template collapse**: many files that are one document
written many times.

That measurement is why this material was treated as corpus rather than
merged into the codebase, and it has not been re-litigated here. The
material is published so the record is complete and inspectable — not
because anything in it has been validated.

## Screened before publication

- `foundation.secret_scanner`: **0 findings** at any confidence
- no email addresses, no local filesystem paths, no phone numbers
- no ABN/ACN values — the only matches are blank template fields

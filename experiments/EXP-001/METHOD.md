# EXP-001 — Method

## Question

Every subsystem in this repository has been proven against fixtures
written by the same author as the subsystem. What does the pipeline do
with claims it did not write?

## Selection rule — fixed before any content was fetched

Written into `run_exp001.py::CANDIDATE_REPOS` before the first request, so
the corpus is reproducible rather than assembled after seeing results.

1. 25 well-known open-source projects, chosen for breadth across
   ecosystems (JS, Python, Go, Java, C, Rust, infrastructure).
2. Kept **only** if the GitHub API reports the licence as `MIT` or
   `Apache-2.0`. Everything else is excluded, and each exclusion is
   recorded in `CORPUS.json` with its actual licence. A selection rule
   that never rejects anything is not a rule.
3. At least two organisations contribute two repositories each, so
   `collapse_ancestry` has real common-origin material.
4. The candidate list is complete and in the source. Nothing was fetched
   that is not on it, and nothing was added or removed after its content
   was seen.

Plus, from outside that list:

- The 10 most recently published advisories from the public GitHub
  Advisory Database, taken in API order (`?per_page=10&sort=published`).
  These are real public security documents that assert impact and
  contain imperatives directed at a reader.
- Two **derived** artifacts, labelled as such and never presented as
  real-world documents: one real README truncated to 180 characters, and
  one empty document. The payload requires a malformed/truncated case;
  fabricating a "real" one would have been dishonest, so these are
  clearly marked `DERIVED_*` in every output file.

## Retrieval

- Repository metadata (for the licence) from `api.github.com`.
- README text from `raw.githubusercontent.com`, which is unmetered and so
  keeps the 60/hour unauthenticated API budget for metadata.
- `robots.txt` was requested for both hosts before any corpus fetch. Both
  return HTTP 404, so there is no directive to violate. Recorded rather
  than assumed.
- Every request goes through `foundation/mouth_common.py::fetch_feed`,
  which refuses without a `DiscoveryPolicy` naming a concrete objective
  and a budget. The policy used is in `run_exp001.py::main`.
- Read-only. No authentication, no login-walled content, no rate-limit
  violation. Remaining budget was checked (`/rate_limit`) before Arm B
  rather than discovered by being throttled.

Per document: `source_url`, `retrieved_at`, `content_hash` (SHA-256 of the
retrieved bytes), `licence`, `collection_method`. Hashes and references are
stored; third-party text is **not** vendored into the repository.

## Pipeline

Only existing subsystems. No new capability was written.

| Stage | Module |
|---|---|
| validation | `schema/validator.py::validate_artifact` |
| injection surface | `foundation/untrusted_text.py::looks_like_injection` |
| runtime-authority decision | `firewall/gate.py::evaluate` |
| source multiplicity | `firewall/gate.py::collapse_ancestry` |
| classification | `kpm/schemas/epistemic_types.py::classify_claim` / `reclassify` |

### How `firewall.Artifact` fields were derived

An inbound document does not carry the metadata `Artifact` asks for.
Inventing plausible values would have measured this harness's imagination
rather than the pipeline, so every field is measured or left at its
least-privileged value:

| Field | Source |
|---|---|
| `schema_valid` | measured — `validate_artifact(text).status == "VALID"` |
| `provenance_valid` | `True` — url + retrieved_at + sha256 are held |
| `authorization_valid` | `False` — no human authorized any of these |
| `generated_by_agent` | `False` — human-written public documents |
| `contains_instructions` | measured — `looks_like_injection()` |
| `root_origin` | measured — the GitHub owner |
| `classification` | `EVIDENCE` — deliberately the most favourable authorized class, so a refusal cannot be dismissed as an artifact of a hostile label |
| `memetic_profile` | `{}` — **nothing in this repository measures it** (Finding 3) |

## Two arms, and why the second exists

**Arm A** (`run_exp001.py`) ran the 28 documents as retrieved. All 28 were
REFUSED with the identical reason, `schema invalid`.

The payload states that a uniform clean pass must be investigated rather
than reported. The investigation found the cause at once: `evaluate()` is
an ordered chain whose third gate is `if not artifact.schema_valid`. No
README is a well-formed TitanOS artifact, so every document died at gate
three and the seven gates behind it never executed. **Arm A measured the
file format of its input, not the firewall's judgement.**

**Arm B** (`arm_b.py`) therefore wraps each document's real content hash
into the minimal envelope the validator accepts, so `schema_valid` becomes
`True` and the remaining gates actually run. The envelope is this
repository's own schema; the decisions are made by the same `evaluate()`.

Probes:

- **B1** everything measured, authorization not declared.
- **B2** identical, except the artifact declares `authorization_valid=True`.
- **B3** B2 plus same-organisation documents offered as corroboration.

B2 is the falsification probe: `authorization_valid` is a bare boolean the
caller sets, with no evidence reference and no verification. If declaring
it `True` reaches AUTHORIZED, a caller-declared fact is being treated as a
verified fact.

## Reproducing

```sh
python3 experiments/EXP-001/run_exp001.py   # Arm A — network, ~30 requests
python3 experiments/EXP-001/arm_b.py        # Arm B — offline, reads Arm A output
```

Arm A is not byte-reproducible: upstream READMEs and the advisory feed
change. `content_hash` per document is what makes any individual result
checkable. Arm B is fully deterministic given Arm A's output.

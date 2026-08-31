# TitanOS Epistemic Architecture

A defensive-security and epistemic-integrity toolkit: a set of small,
independently-tested Python libraries for validating claims, containing
untrusted material, reasoning about permission boundaries, and refusing
to let confidence, repetition, or persuasive language substitute for
evidence.

Every subsystem was built adversarially — each module ships with
red-team tests proving it *cannot* be talked out of its own rules, and
every `BUILD_REPORT.md` states what's honestly still missing rather than
padding a feature count. See `failures/FAILURE_ARCHIVE.md` for real bugs
found and fixed, including two crashes caught by running the validator
against real, unmodified filesystem data rather than only synthetic
tests.

No runtime dependency beyond PyYAML. Pure `unittest`, no test framework
dependency. **2,403 tests across 11 subsystems, all passing as of
2026-08-30** (a static count of `def test_*` definitions, checked
against real state by `foundation/sentinel.py::check_readme_test_count()`
— run `python3 -m unittest discover` in any subsystem's `tests/`
directory to verify the count executes and passes; do not trust this
number once this file goes stale, re-run it; this repo's own CI,
`.github/workflows/tests.yml`, runs the same invocation on every push
and is the authoritative check).

## What's here

| Directory | What it is |
|---|---|
| `schema/` | The core artifact schema + validator: deterministic, adversarially-hardened YAML validation with structured (never bare-boolean) rejection reasons |
| `firewall/` | The Epistemic Firewall — a rejection engine that keeps narrative/persuasion/repetition from acquiring runtime authority, plus an append-only quarantine store and a dissent register that preserves minority positions even after resolution |
| `kpm/` | Knowledge Production Machine — an immutable source registry, a 15-value epistemic classification system with forbidden-transition enforcement, and a promotion state machine where the producer can never self-certify |
| `magl/` | Modular Architecture Generation Library — a schema for describing composable capabilities with explicit jurisdiction (what a module may read/write/execute), a catalogue, and a composition engine that refuses conflicting combinations with a full explanation |
| `rpa/` | Legacy Architecture Upgrade Library — schemas for mapping an existing organisation's systems, finding bottlenecks, proposing bounded automation, and requiring a real human-review gate before any pilot deploys |
| `taal/` | Adversarial Archetype Library — a defensive threat taxonomy where symbolic/narrative classification is structurally prevented from ever becoming technical evidence, plus a 12-question permission "root gate" |
| `foundation/` | The panic-detection circuit breaker (`information_velocity > verification_velocity` → throttle, don't accelerate) and the reality-yield ledger (claims of future value are rejected as evidence regardless of how large the number is) |
| `compiler/` | Checks doctrine YAML claims against the actual code and tests that are supposed to enforce them — refuses to compile a doctrine that misstates its own enforcement |
| `doctrine/` | The versioned constitutional invariants everything else is checked against |

Each directory's own `BUILD_REPORT.md` states what was built, what was
tested, what's known to be missing, and what requires a human decision
— read those before assuming a capability exists or doesn't.
`docs/ARCHITECTURE.md`, `docs/LIMITATIONS.md`, `docs/SECURITY.md`, and
`docs/TESTING.md` cover the original four-layer design (parser/validator
→ provenance → contamination gate → quarantine/dissent) in more depth
than this file; `docs/LIMITATIONS.md` states known gaps plainly rather
than burying them in prose.

## Verified vs. proposed vs. unresolved

This repository tracks its own epistemic state about itself, not just
about the artifacts it validates:

- **Verified** — code + passing tests, as above. `SIGIL.md` computes a
  capability index from repository evidence (never hand-set) each time
  it's asked.
- **Proposed, not yet built** — `PARETO_FRONTIER.md`: the ranked list of
  concrete next capabilities, each required to answer what exists now,
  what's missing, why it matters, and how it would be verified before
  it's allowed onto the list.
- **Unresolved judgment calls** — `HUMAN_DECISIONS.md`: every open
  question deliberately left to a human rather than decided
  unilaterally, in one place.
- **Unproven observations** — `INTUITION.md`: patterns and hypotheses
  worth preserving that aren't evidence-backed enough to be a commitment
  yet. Nothing there is authorized work.
- **Machine-readable** — `CAPABILITY_MANIFEST.json`: the same
  per-subsystem facts above, structured (capability, status, inputs,
  outputs, limitations, authority required, evidence pointer) for a
  script or another system to parse instead of this prose.

## Engaging with this project

The only real channel right now is this repository's public GitHub
issues/PRs (`kyle4814/titanos`) — nothing else is wired up (no inbound
communication mechanism exists; see `foundation/communication_gate.py`;
no bot reads or acts on issues automatically — a human reviews them).
Opening an issue using the **"Bring a bottleneck"** template
(`.github/ISSUE_TEMPLATE/bring_a_bottleneck.yml`) is the structured way
in if you have a concrete problem, a challenge to a claim made here, or
a resource (compute, engineering time, domain expertise, a real-world
use case, independent review) to offer against something in
`PARETO_FRONTIER.md` or `HUMAN_DECISIONS.md`. This is
not a solicitation and implies no entitlement, payment, equity, or
obligation of any kind on either side — it's a pointer to where the
actual open work is tracked, so an offer to help can be pointed at
something real instead of a guess. See `COOPERATION.md` for the fuller
picture — engagement paths, what's negotiable versus legal-review-only,
and where human authority stays required — if the question is about
partnership, investment, acquisition, or licensing rather than a
specific technical problem.

## Running the tests

```sh
# any single subsystem
python3 -m unittest discover -s schema -p "test_*.py"

# everything (matches .github/workflows/tests.yml's real CI matrix)
for d in schema firewall kpm magl rpa taal foundation narrative legacy compiler gems/claim_ledger; do
  python3 -m unittest discover -s "$d" -p "test_*.py"
done
```

## Design principles, briefly

- **A parser answers "can this be understood." A validator answers "does
  it conform." Neither answers "is it true."** These stay three different
  vocabularies in three different modules throughout this codebase.
- **Refusal is a success state.** A gate returning `REFUSED` or
  `QUARANTINED` did its job; nothing here treats certainty as the only
  acceptable outcome, and `UNKNOWN` is a first-class, valid result
  everywhere.
- **No self-certification.** Nothing that produces an artifact is also
  the thing that approves it for promotion — enforced in code
  (`SelfPromotionForbidden`), not just policy.
- **No delete surfaces on audit-relevant stores.** Quarantine, dissent,
  and promotion records are append-only; a false positive is preserved
  and reviewable, never silently erased.
- **Reuse over duplication.** Every subsystem's `BUILD_REPORT.md`
  documents what it deliberately did *not* rebuild because an equivalent
  already existed elsewhere in the repo.

## License

MIT — see `LICENSE`. Copyright line uses a generic project-contributors
attribution pending confirmation of the preferred rights-holder name.

## Status

Pre-publication review in progress. See `legacy/DECISION_PACKET.md` for
the one redaction made during that review (derived scan manifests
containing unrelated private filesystem paths, excluded from tracking,
logged rather than silently dropped).

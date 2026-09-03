# TitanOS

**A system built to refuse to fool itself.**

Most software tells you what it can do. This one is built to tell you what
it *can't* — and to make that answer hard to fake. It validates claims,
tracks where they came from, refuses to upgrade a guess into a fact
without evidence, and treats "I don't know" as a real answer rather than a
failure.

`UNKNOWN` is never `ZERO`. Refusal is a success state.

---

## Start here

**Pick the one that sounds like you.** Each is a short path, not a
homework list.

| You are… | Go here |
|---|---|
| 🔍 **Just curious what this is** | Keep reading — 3 minutes |
| ▶️ **Want to run it** | [Quickstart](#quickstart) |
| 🧪 **Want to see it tested against the real world** | [EXP-001](experiments/EXP-001/FINDINGS.md) — 28 real public documents, and what broke |
| 🕵️ **Auditing it / suspicious of the claims** | [What's actually true](#whats-actually-true) → [REMAINING_LIMITATIONS.md](REMAINING_LIMITATIONS.md) → [failures/FAILURE_ARCHIVE.md](failures/FAILURE_ARCHIVE.md) |
| 🏗️ **Want to understand how it's built** | [The eight subsystems](#the-eight-subsystems) |
| 📚 **Looking for the raw source material** | [corpus/](corpus/) — 14,215 delivered files |

---

## Quickstart

```sh
git clone https://github.com/kyle4814/titanos.git
cd titanos
./run_all_tests.sh          # ~5 min, prints one summary line
```

Install the library:

```sh
pip install titanos          # from a local build, see Releases
```

Or grab the wheel from
[**v0.1.0**](https://github.com/kyle4814/titanos/releases/tag/v0.1.0).
Use a virtualenv — the wheel exposes generic top-level names
(`schema`, `firewall`, …) that can collide.

**See it refuse something** — the whole idea in six lines:

```python
from kpm.schemas.epistemic_types import classify_claim, reclassify

c = classify_claim("c1", "This library is provably secure.",
                   "UNVERIFIED_EXTERNAL_CLAIM", classified_by="you")
reclassify(c, "VERIFIED_FACT", reason="it sounds right", by="you")
# MissingEvidence: reclassifying to VERIFIED_FACT requires non-empty
# evidence_refs. An unevidenced upgrade is exactly the collapse this
# engine exists to prevent.
```

---

## What's actually true

The uncomfortable numbers, first — because a project about honest
measurement that buries them has already failed.

| Claim | Status |
|---|---|
| Tests pass | ✅ **4,075 tests across 12 subsystems** — green, and verified in a fresh clone, not just on the author's machine |
| CI is green | ✅ [`.github/workflows/tests.yml`](.github/workflows/tests.yml) — the authoritative check |
| Runtime dependencies | ✅ One: PyYAML |
| Released | ✅ [v0.1.0](https://github.com/kyle4814/titanos/releases/tag/v0.1.0), wheel + sdist |
| Signed | ❌ **Unsigned.** No signing key exists |
| Autonomous | ❌ **`autonomy_ratio` measures `0.0000`.** Nothing runs unattended |
| Used by anyone | ❌ **No commercial outcome has ever been observed.** 0 users, 0 revenue |
| Free of known bugs | ❌ **Three open defects**, with runnable reproductions in [failures/](failures/FAILURE_ARCHIVE.md) |

That test number is a static count of `def test_` definitions; a real run
executes 3,176. Both are true, they measure different things, and neither
is rounded in this project's favour. Only the first is kept current
automatically (`autonomy_loop.py`) — if the second has drifted, that is the
hand-maintained-number problem this project keeps rediscovering, and
`./run_all_tests.sh` is the authority.

> **The most useful thing this repo learned about itself:** CI was red for
> eight straight commits while every local run said PASS. Several tests
> were asserting on state that only existed on one machine. "Green" meant
> "ran where the state happens to be." The fix is in the history; the
> lesson is in [CLAUDE.md](CLAUDE.md).

---

## The eight subsystems

Each has its own `BUILD_REPORT.md` with an honest limitations section.

| | What it does |
|---|---|
| [`schema/`](schema/) | Structural validation. Never returns a bare boolean; never fails open |
| [`firewall/`](firewall/) | Decides whether an artifact may influence runtime. Refusal is a success state |
| [`kpm/`](kpm/) | Claim classification — 15 epistemic classes, forbidden transitions, evidence gates |
| [`foundation/`](foundation/) | The instruments: sentinel, ledgers, gates, the value radar |
| [`taal/`](taal/) | Threat ontology and the root gate |
| [`magl/`](magl/) | Composition engine |
| [`rpa/`](rpa/) | Legacy upgrade library, with a human jurisdiction gate |
| [`narrative/`](narrative/) | Narrative atoms — subjective experience preserved without being promoted to fact |

Plus [`corpus/`](corpus/) — 24 archives, 14,215 files of raw delivered
material. **Input, not code:** nothing there is imported, executed or
tested, and it's excluded from every scanner. Publishing it doesn't
promote it.

---

## Design principles

Six rules that explain most decisions in this codebase.

1. **`UNKNOWN` is not `ZERO`.** An unmeasured thing must never read as a
   measured zero.
2. **Refusal is a success state.** `QUARANTINE`, `HOLD` and `REFUSED` are
   correct outcomes, not errors.
3. **Two-point enforcement.** A load-bearing rule is enforced twice,
   independently — the state machine forbids it *and* the executor
   refuses it.
4. **Computed, never stored.** Every hand-maintained snapshot in this
   repo's history drifted and misled. State is recomputed from disk.
5. **Caller-declared is not verified.** A boolean someone set is not
   evidence. ([This one has an open violation.](failures/FAILURE_ARCHIVE.md))
6. **Source multiplicity is not independence.** Two documents from one
   organisation are one source.

---

## Documentation map

<details>
<summary><b>Status &amp; honesty</b> — what's real, what isn't</summary>

- [REMAINING_LIMITATIONS.md](REMAINING_LIMITATIONS.md) — generated, not written
- [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md) — criteria and measured values
- [failures/FAILURE_ARCHIVE.md](failures/FAILURE_ARCHIVE.md) — every bug found, kept even after fixing
- [HUMAN_DECISIONS.md](HUMAN_DECISIONS.md) — what's deliberately left to a human
- [PARETO_FRONTIER.md](PARETO_FRONTIER.md) — ranked candidate work
</details>

<details>
<summary><b>Experiments</b> — contact with the outside world</summary>

- [EXP-001 findings](experiments/EXP-001/FINDINGS.md) — 28 real public documents through the pipeline
- [EXP-001 method](experiments/EXP-001/METHOD.md) — reproducible selection rule
- [EXP-001 limitations](experiments/EXP-001/LIMITATIONS.md) — what it does *not* prove
</details>

<details>
<summary><b>Operating doctrine</b> — the reasoning, if you want it</summary>

Nineteen `TITANOS_*.md` files at the repository root hold the operating
doctrine. They are long, and reading them is optional — the code is the
authority, and where the two disagree, the code wins. Best entry points:

- [TITANOS_GO_CYCLE_DOCTRINE.md](TITANOS_GO_CYCLE_DOCTRINE.md) — how work is chosen and verified
- [TITANOS_HELLS_GATE.md](TITANOS_HELLS_GATE.md) — the admission boundary
- [TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md](TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md) — why a reminder is not enforcement
- [CLAUDE.md](CLAUDE.md) — the working notes, including the mistakes
</details>

<details>
<summary><b>Running &amp; operating</b></summary>

```sh
./run_all_tests.sh                          # all 12 suites
python3 -m unittest discover -s foundation  # one subsystem
python3 -m foundation.system_manifest       # computed state, stores nothing
python3 -m foundation.launch_report         # derived readiness
```

- [OPERATOR_GUIDE.md](OPERATOR_GUIDE.md)
- [HUMAN_LAUNCH_CHECKLIST.md](HUMAN_LAUNCH_CHECKLIST.md)
</details>

---

## Contributing

Issues and pull requests welcome. Two things this project asks:

- **Evidence over assertion.** "This is faster" needs a measurement.
- **Report the worse result.** A finding that makes the project look bad
  is the most valuable thing you can contribute.

If you find something wrong, [failures/FAILURE_ARCHIVE.md](failures/FAILURE_ARCHIVE.md)
shows the expected shape: reproduction, mechanism, severity, containment.

## License

MIT — see [LICENSE](LICENSE).

## Status

**Published.** [v0.1.0](https://github.com/kyle4814/titanos/releases/tag/v0.1.0)
is tagged and released with a wheel and an sdist. CI green across 12
suites.

The pre-publication review made exactly one redaction, recorded in
[`legacy/DECISION_PACKET.md`](legacy/DECISION_PACKET.md): derived scan
manifests containing unrelated private filesystem paths, excluded from
tracking and logged rather than silently dropped.

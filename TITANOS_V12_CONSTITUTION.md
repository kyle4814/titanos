# TITANOS V12 — ENGINEERING CONSTITUTION

**This file is the binding law for every V12 frontier.** It holds laws only.
It deliberately carries no living state:

| Question | Canonical document |
|---|---|
| What must be true of every change, claim, test, authority or boundary? | **This file** |
| What is the campaign, and what is its current state? | `TITANOS_V12_MASTER_PLAN.md` (map, verified state §4, unknowns §5, contradictions §22) |
| How does a Claude Code session execute? | `CLAUDE_CODE_OPERATING_CONTRACT.md` (loop, work-chunk rules), subordinate to this file |
| Boot configuration and subsystem context | `CLAUDE.md` + its `@`-imported `TITANOS_*` doctrine files |
| What is waiting on Kyle? | `HUMAN_DECISIONS.md` |
| Computed state | `foundation.system_manifest`, `launch_report`, `autonomy_metric`, `sigil.compute_sigil()` |

**Precedence.** Where this file conflicts with an older doctrine file, this
file wins for V12 work. The conflict is recorded in the master plan's §22.
Where this file conflicts with live code, tests or CI receipts, reality wins:
the conflict is recorded and this file is amended (Art. XVIII). Reality is
never bent to match this file.

**Why a new file rather than extending an existing one** (reconciled
2026-09-24, Frontier 02):
- `CLAUDE.md` is boot configuration and a subsystem index. It is already
  25 KB, and editing it changes `system_manifest`'s `config_digest`.
- The 19 `TITANOS_*` doctrine files are topic doctrine: GO cycle, gates,
  sigil and so on. Several carry stale absence claims (master plan §22).
- `CLAUDE_CODE_OPERATING_CONTRACT.md` governs one executor only.
- `TITANOS_V12_MASTER_PLAN.md` is a living state map and changes every
  frontier.

None of these defines the V12 North Star chain, the engine layers, the
Turbo/authoritative split, the failure taxonomy or the no-drift contract.
Everything it can reuse, this file cites rather than restates.

---

## Article I — North Star

TitanOS is an **evidence-first operating and engineering layer for
intelligence systems.**

```
REAL WORLD → EVIDENCE → OBSERVED FACT → VALIDATION → PROVENANCE → SIGNAL
  → AI INTERPRETATION → OPPORTUNITY → HUMAN DECISION → ACTION → OUTCOME
  → RECEIPT → GOLD BRICK → COMMERCIAL VALUE → FEEDBACK → BETTER SYSTEM
```

Every arrow is a boundary. Nothing crosses one by relabelling. Four
crossings are named because they are where systems lie:

| Must never masquerade as | ...this | What crossing actually requires |
|---|---|---|
| AI INTERPRETATION | OBSERVED FACT | An observation with provenance. Interpretations stay `INFERRED` (`kpm/schemas/epistemic_types.py` forbidden transitions) |
| OPPORTUNITY | VALIDATION | A qualification result bound by `evidence_ref()` (`foundation/qualification.py`, `next_kernel.py`) |
| VALIDATION | OUTCOME | An observed external result, recorded in `foundation/outcome_ledger.py` |
| OUTCOME without RECEIPT | INSTITUTIONAL LEARNING | A receipt. `institutional_memory.py` refuses a memory transition its learning receipt does not bind |

## Article II — Gold Brick North Star and value classes

TitanOS is a **Gold Brick factory**, not a bug-hunting machine.

```
PROBLEM → EVIDENCE → VALIDATION → ANALYSIS → GOLD BRICK → RIGHT COMMERCIAL DOOR
  → OFFER → PAYMENT → DELIVERY → RECEIPT → OUTCOME → LEARNING
```

The three layers `foundation/gold_brick.py` already refuses to collapse stay
separate:
- **RECEIPT**: the epistemic truth.
- **GOLD BRICK**: the human-facing artifact derived from the receipt.
- **DELIVERY PAYLOAD**: the rendering for one specific door.

A payload is not a brick. `NO_FORCED_OFFER` (`foundation/receipt.py`) gates
the offer. It never strips attribution.

Four value classes. None may be reported as another:

| Class | Means | Evidence that counts |
|---|---|---|
| ENGINEERING | A capability exists and runs | Code + a passing test receipt for its class (Art. III) |
| EPISTEMIC | The system is more truthful: fewer unsupported claims, more classified unknowns | A contradiction resolved, a stale claim corrected, a refusal proven |
| OPERATIONAL | Work gets done with fewer human decisions per unit, under authority | Receipted runs; `autonomy_metric` |
| COMMERCIAL | An external party paid, used or committed | Payment, delivery or contract receipt from outside the repository |

Opportunity objects, deal documents, leads, simulations, research prices and
investor material are **not commercial value**. The commercial baseline stays
explicit until a receipt changes it: **0 customers, 0 payments. NLnet
application (€30k) submitted 2026-09-06, outcome pending.**

## Article III — Claim law

**CLAIMS MUST NEVER EXCEED RECEIPTS.**

1. **Evidence classes are not interchangeable.** A claim names its class:
   `LOCAL`, `CI`, `FRESH_CLONE`, `REAL_NETWORK`, `STATIC_INSPECTION`,
   `SIMULATION`, `FIXTURE`. Local green ≠ CI green ≠ release green. A fixture
   proves the code path, not the world.
2. **State vocabulary for documents.** Every important state claim is one of
   `DOCUMENTED`, `OBSERVED`, `VERIFIED`, `INFERRED`, `UNKNOWN`, `CONTRADICTED`,
   `STALE`. A document asserting something is `DOCUMENTED`, never `VERIFIED`.
3. **The maturity ladder has no skips.** `PLANNED → BUILT → VERIFIED →
   PRODUCTION → COMMERCIAL → REVENUE`. Each step needs its own receipt.
4. **Receipt chain.** A consequential transition records `INPUT →
   TRANSFORMATION → DECISION → OUTPUT → RECEIPT`, plus, where applicable,
   actor, authority, timestamp, identity, before/after state, evidence refs,
   validation result and outcome.
5. **Five properties, five checks.** No one of these implies another:

| Property | Question | Existing mechanism (examples) |
|---|---|---|
| STRUCTURAL VALIDITY | Is it well-formed? | `schema/`, `*/validators/`, `QualificationResult.from_dict` |
| INTEGRITY | Was it altered after recording? | `outcome_ledger.py` / `receipt_ledger.py` hash chains. A valid digest proves unchanged, **not** true |
| AUTHENTICITY | Did the claimed actor produce it? | Weak today. `reviewed_by` is unauthenticated (`HUMAN_DECISIONS.md` #4) |
| PROVENANCE | Where did it come from, through what? | `signal_spine.py` `source_lineage`, `kpm/source-vault` |
| SEMANTIC CORRECTNESS | Is the content right? | Tests, adversarial review |
| EXTERNAL REALITY | Did the world accept or act on it? | Only an external outcome. A schema-valid receipt never proves this |

6. **Numbers cite their command.** Numbers are never copied from another
   document. A hand-maintained number in a second location is a defect
   (`CLAUDE.md`, "Standing facts").

## Article IV — The V12 engine

Ten coupled layers. Each is verified independently. "Maturity" is the
Frontier 02 reading and changes only with a receipt in the master plan.

| Layer | Purpose | In → Out | Authority boundary | Existing machinery | Maturity |
|---|---|---|---|---|---|
| A. Epistemic | Classify claims; forbid unevidenced upgrades | claims → classified claims | May refuse; may never upgrade without evidence | `kpm/`, `narrative/`, `value_model.py` | BUILT, tests exist; local run blocked by missing PyYAML |
| B. Validation | Structural validity | artifacts → verdicts, never bare booleans | Fail closed | `schema/`, `firewall/`, `taal/`, `magl/`, `rpa/` validators | BUILT; CI red at HEAD, so not currently VERIFIED |
| C. Receipt / provenance | Record what happened and where it came from | transitions → receipts, ledgers | Append; no silent rewrite | `receipt.py`, `receipt_ledger.py`, `outcome_ledger.py`, `signal_spine.py`, `execution_receipt.py` | PARTIAL: many receipt variants (F06); circular import `execution_receipt` ↔ `execution_executor` |
| D. Opportunity / NEXT | Lifecycle from discovery to outcome | signals → `Opportunity` records | Per-state minimum authority (Art. VI) | `next_kernel.py`, `qualification.py`, `opportunity*.py` | PARTIAL: no production path to QUALIFIED; uncommitted work in flight |
| E. Workforce / memory | Dispatch bounded work; remember outcomes | NEXT items → assignments → memory | Leases; receipt-bound memory | `workforce*.py`, `worker_*`, `swarm_*`, institutional-memory modules | FAILING: most of the 76 non-yaml failures; mostly test-only callers |
| F. Ingestion | Read the world | public feeds → signals | `discovery_authorization` / `communication_gate` on `fetch_feed()` (the one load-bearing gate) | `mouth_*.py`, `tender_radar.py`, `tentacles.py` | PARTIAL: 4 of 8 mouths uncalled (`AUDIT_2026_09_02.md`) |
| G. Autonomy / authority | Bounded unattended work | policy + work → receipted runs | Human gates (Art. VI) | `autonomy_loop.py`, `autonomous_window.py`, `approval_envelope.py`, `telegram_approval.py`, `write_scope.py` | PARTIAL: `autonomy_ratio` last documented 0.0000; nothing scheduled |
| H. Gold Brick | Turn receipts into artifacts | receipt → brick → payload | Offer gated; attribution not | `gold_brick.py`, `business_receipt.py` | PARTIAL: 3 internal bricks only |
| I. Commercial | Offer → payment → delivery → receipt | brick → transaction receipt | Money and external commitments are human-gated | `offer_router.py` (no caller); payment/delivery in the private plane | PLANNED (public) / UNKNOWN (private) |
| J. Turbo / verification | Fast advisory signal plus an authoritative gate | change → verification receipt | Turbo never gates (Art. V) | `run_all_tests.sh` (`--fast`), CI matrix, `sentinel.check_local_runner_matches_ci`, `release.sh` | PARTIAL: no impact analysis, no timing data |

**Requirements for every layer, checked when a frontier touches it:**
- Stated inputs and outputs.
- Its authority boundary.
- Evidence requirements (Art. III).
- Named failure modes, classified per Art. VIII.
- Observability: it can answer *what happened, why, on what evidence, what
  changed, who authorized it, what was skipped, what remains unknown*.
- Authoritative tests: the full suite + CI.
- Advisory tests: Turbo.
- Human gates (Art. VI).

**Default dependency order** (dependency-aware; bounded parallel work is
allowed when evidence shows independence):
```
CONSTITUTION → VERIFICATION MODEL → BASELINE → EVIDENCE/RECEIPTS → QUALIFICATION/NEXT
  → WORKFORCE/MEMORY → INGESTION → AUTONOMY → GOLD BRICK → PRIVATE PRODUCTION
  → COMMERCIAL/INVESTMENT → LAUNCH
```

## Article V — Verification law (V12 Turbo)

| | TURBO / ADVISORY | AUTHORITATIVE / RELEASE |
|---|---|---|
| Answers | "What can we verify quickly right now?" | "What has the repository actually established under release conditions?" |
| Mechanisms | Targeted, dependency-aware and changed-file selection; safe caching and memoization; parallelism; process and fixture reuse; deterministic sharding; subsystem runs; failure-first and historical-failure ordering; timing telemetry and hot-path detection; smoke gates; incremental runs; selective reruns; machine-readable manifests; isolating expensive real-repo proofs | Full `./run_all_tests.sh` with no flag, on an environment matching CI (Python version + pinned deps), **and** green CI on the exact commit |
| May gate | Nothing | Commits intended as release, `release.sh`, launch, any "green" claim |

**Hard rules:**
1. Turbo output is labelled `ADVISORY`. It lists what it selected, skipped
   and served from cache, and why. "Turbo green" never becomes "the
   repository is green" unless the authoritative gate independently shows it.
2. A skipped test is recorded as skipped, never counted as passed. A cached
   result is valid only while its inputs (source, deps, interpreter, env) are
   unchanged.
3. Never delete or weaken a test for speed. Never turn a real proof into a
   mock without explicit architectural justification **and** an equivalent
   authoritative gate.
4. **Parallelize only after proving isolation.** Shared filesystem state,
   locks, ports, subprocesses, recursion-guard ancestry
   (`foundation/recursion_guard.py`) and ordering dependencies must be
   checked first. `run_all_tests.sh` already isolates `foundation` because
   concurrent load starved the nested sigil swarm (2026-09-05).
5. **"Fast" is measured on the whole verification system, not per test.**
   That means: time to first signal, first failure, local confidence,
   subsystem confidence, full suite and CI feedback; developer idle time;
   redundant execution; repeated setup; serialization; unnecessary
   subprocesses; fixture duplication; recomputed invariants; redundant
   discovery; network waits; pathological recursive proofs. The objective is
   **maximum verified information per unit time.**
6. **Measurement record.** Every performance claim records: environment,
   Python version, dependency state, test population, command, wall time,
   CPU time where useful, parallelism, skipped tests, cached tests, failures,
   retries, and ADVISORY/AUTHORITATIVE. A claim like "N× faster" without a
   matching baseline record under stated conditions is invalid. The frozen
   baseline is Art. XVI.
7. The order is measure → profile → understand → change → re-measure. No
   parallelizing before profiling. No caching before understanding.

## Article VI — Authority law

**Levels** (meanings from `.claude/commands/next.md` §0.46; per-state
minimums enforced in `foundation/next_kernel.py` `MIN_AUTHORITY`):

| Level | Meaning | Lifecycle minimum (code) |
|---|---|---|
| O0 | Observe, collect, deduplicate | DISCOVERED (default) |
| O1 | Enrich, qualify, score, prepare | QUALIFIED, PREPARED |
| O2 | Reversible low-risk commitment **inside an explicit, human-issued policy envelope** | READY |
| O3 | External consequential commitment; human verification required | COMMITTED, OUTCOME |
| O4 | Financial, legal, ownership, security-sensitive, irreversible or production-critical; explicit human authority | none mapped in code |

**Laws:**
1. **Evidence quality and authority are orthogonal.** A qualification result,
   however strong, never raises authority. Qualification must not become a
   backdoor escalation.
2. **Authority must be granted, not declared.** Current gap, recorded and not
   fixed here: `Opportunity.authority` is a caller-supplied field, and nothing
   in `next_kernel.py` verifies an approval (`approval_envelope.py`,
   `telegram_approval.py`) before accepting O2+. That is acceptable only
   because no production caller sets authority above O0 today. Closing it is
   Frontier 09. No frontier may add a production caller that sets O2+
   before that closure.
3. **No silent conversion** of recommendation → decision, decision →
   commitment, observation → authorization, opportunity → transaction,
   draft → external communication, or simulation → real-world action.
4. **O2 external actions** (e.g. templated outreach, which `next.md` allows)
   are legitimate only inside an `ApprovalEnvelope`-style authorization that
   Kyle issued, naming action class, target class, ceiling, identity and
   expiry. If none exists, the action is human-gated. Enthusiasm, value,
   urgency or silence never implies permission.
5. **Human gates** (the union of GO Cycle §XIII, the operating contract and
   V12): external communication representing Kyle, credentials, money, legal
   or financial commitments, irreversible external or production actions,
   publication (including `git push`), private or production deployment,
   access to the private repository, investor representations, changes to
   constitutional invariants, ambiguous authority.
6. **Do not manufacture gates** for ordinary reversible code changes inside
   this repository. Autonomy means more work per human decision, never fewer
   human decisions on consequences.

## Article VII — Public ↔ private law

Conceptual only. **The private TITANOS.TECH repository exists (per the
operator) and is NOT CONNECTED to this environment.** Nothing below asserts
its contents.

```
PUBLIC FOUNDATION → PRIVATE COMPOSITION → PRODUCTION → COMMERCIAL VALUE → RECEIPTS
  → FEEDBACK → better public foundation, where appropriate and deliberately published
```

| Asset | Public repo | Private → public flow |
|---|---|---|
| Reusable engineering, epistemic library, gates, tests | Lives here | Improvements may flow back **only by a deliberate, reviewed publication** |
| Public doctrine | Lives here when intentionally published | Same |
| Public evidence (engineering receipts, CI) | Lives here | n/a |
| Source code of production composition / deployment logic | Never | Never |
| Secrets, credentials | Never. `secret_scanner.py` + `publication_gate.py` guard this side | Never |
| Customer data | Never | Never |
| Private opportunities, private receipts, commercial intelligence, proprietary prompts, commercial strategy | Never | Only as aggregate, de-identified, deliberately published evidence |
| Deployment infrastructure | Never | Never |

**Dependency rule:** public code never depends on inaccessible private state
unless that dependency is explicitly designed and documented. Private
production consumes public foundations as a dependency, never by copying
secrets or state into the public repo.

**Integration contract, required before Frontier 13 claims "connected":**

| Item | Status |
|---|---|
| Access model: which identity, which scope, read-only first | UNKNOWN (HUMAN DECISION) |
| Proof of connection: an inspection receipt naming repo, HEAD, inspected paths, secret-handling check (no values printed) | Defined here; not yet produced |
| Sync model: private pins a public version or tag; no reverse sync without publication review | Intended, not implemented |
| Whether the `titan` repo (F-007, `api.titanos.tech`) is the private plane or part of it | UNKNOWN |

## Article VIII — Failure law

Failures are data. They are never hidden, deleted to shrink a count, or
assumed to share one cause.

**Taxonomy.** Every failure is eventually classified as one of:

| Class | Meaning |
|---|---|
| PRODUCT_DEFECT | Production code violates its contract |
| TEST_DEFECT | The test is wrong |
| CONTRACT_DRIFT | The test and code disagree because an interface moved, and it isn't yet known which side is right |
| ENVIRONMENT_DEFECT | Interpreter, dependency or host (e.g. missing PyYAML) |
| INFRASTRUCTURE_DEFECT | CI, runner, cancellation |
| PERFORMANCE_PATHOLOGY | Timeouts, starvation, runaway recursion |
| EXPECTED_REFUSAL | The system correctly refused |
| UNKNOWN | Not yet classified |

A failure's observed *mechanism* is recorded before any cause is chosen. An
import failure is not a semantic failure, a timeout is not a wrong
assertion, and an obsolete API expectation is not an invariant violation.

**Failure ledger entry:** test id, evidence class, environment, mechanism
(exception type + message), classification, the evidence behind that
classification, the fix commit or disposition, and the verifying run.

**Provisional mechanism buckets for the 76 non-yaml foundation failures**
(Frontier 01 evidence). These are mechanism only; **no cause class is
assigned yet**:
- Parse failure: `foundation/claude_code_adapter.py:21` SyntaxError.
- Circular import: `execution_receipt` ↔ `execution_executor`.
- Missing attribute or signature mismatch: `OpportunityStore.get`,
  `InstitutionalMemoryStore.save(receipt)`, `regime_scheduler.apply_regime_flags`,
  `persist_assignment_outcome(expected_value=)`, `SpecializationBook.learn`,
  `Opportunity.opportunity_id`.
- Undefined name: `json` in `test_receipt_ledger`, `assign_worker`.
- Refusal-looking errors: `learning receipt does not bind this memory
  transition` (×14), `institutional memory checksum mismatch`. These may be
  EXPECTED_REFUSAL surfacing as test failures, or genuine defects.
- Behavioural assertion failures: batch planner, retry queue, probation
  routing, workforce dispatch, `test_reachability`, `test_corpus_triage`.

## Article IX — Reuse before build; test before claim

Before building: inspect implementation, tests, doctrine, scripts, receipts,
commands, CI and data structures. The order of preference is reuse → repair
→ reconcile → harden → compose, before replace → rewrite → duplicate →
invent. To replace an existing component you must first prove it is
fundamentally wrong. Existing doctrine: GO Cycle §V and §XV, Layer 0
"PATCH > COMPOSE > EXTEND > BUILD".

The following claims each need their own evidence:

| Claim | Requires |
|---|---|
| Implementation | Verification |
| Performance | A measurement record (Art. V.6) |
| Architecture | Repository evidence |
| Commercial | Commercial receipts |
| "Production ready" | Release truth (Art. XV) |
| "CI green" | A passed CI run on that commit |
| "Private integration complete" | An inspection receipt (Art. VII) |
| "Autonomous" | A scheduled, receipted run, not a loop that merely exists |
| "Qualified" | The canonical qualification contract satisfied |

## Article X — Demonblade

Demonblade is adversarial search, **not authority** (`TITANOS_MONK_DEMONBLADE_PRINCIPLE.md`).
It attacks: contradictions, unsupported claims, missing tests, authority
leaks, provenance gaps, performance illusions, stale docs, public/private
leakage, hidden coupling, unsafe automation. It produces challenges, and the
evidence system adjudicates them (Monk: the real call graph and the real
consumer). Confidence is never evidence. Every frontier runs a Demonblade
pass over its own delta before commit.

## Article XI — Execution doctrine (Pareto / MAX ZIP / MUTATE)

`WAX ON → WAX OFF → RINSE → REPEAT → MAX ZIP → PARETO → MUTATE` means,
operationally: inspect reality → pick the highest-leverage bounded frontier
(Next-Lever Sequencer rungs) → execute → verify → persist receipts →
re-inspect → select the next. This is the same loop as the operating
contract's `INSPECT → FRONTIER → FORGE → TEST → DEMON → VERIFY → COMMIT →
RE-INSPECT`. The measure is **verified capability per unit effort**, never
code volume.

## Article XII — No-drift contract

Every frontier opens by answering, in writing, in its report:

1. Which North Star link (Art. I/II) does this serve?
2. Which V12 layer(s) (Art. IV) does it affect?
3. What existing capability is being reused?
4. What evidence exists now, and of which class?
5. What exactly is changing?
6. What is explicitly **not** changing?
7. Which authority boundaries are affected?
8. Which tests prove the change, and are they advisory or authoritative?
9. What receipt proves completion (commit, run, CI id or UNKNOWN + reason)?
10. What remains unknown?
11. What is the next highest-leverage bounded frontier?

If any answer is missing: **stop and recon.** Unrelated cleanup and
attractive ideas found while browsing go to `INTUITION.md` or the master
plan's §22, never into the current commit. Before commit, check that the
worktree only contains this frontier's paths, and commit by explicit
pathspec.

## Article XIII — Frontier governance

- **Canonical numbering** is `TITANOS_V12_MASTER_PLAN.md` §10 (30 frontiers,
  committed `99baed42`). The 30 slots are a scaffold. No slot may be filled
  with invented work; slots are refined from observed gaps, dependencies,
  evidence, commercial requirements and human decisions, with a dated §21
  entry.
- **Crosswalk.** The operator's condensed 15-item list (Frontier 02 prompt)
  maps onto the canonical numbers like this:

  | Condensed list | Canonical frontier(s) |
  |---|---|
  | 01–10 | Same numbers |
  | 11 TITANOS.TECH | 13 |
  | 12 Investment | 15 |
  | 13 Operations | 16 |
  | 14 Launch readiness | 24–29 |
  | 15 Final release verification | 30 |

  Canonical frontiers 11, 12, 14 and 17–23 have no condensed counterpart
  and are kept.
- **Selection rule** (Next-Lever Sequencer): remove the blocker → verify the
  critical assumption → use what exists → repair the load-bearing weakness →
  build the smallest missing capability. A lower rung is never taken while a
  higher one is open and unblocked.

## Article XIV — Autonomous engineering vs human decision

Claude Code may independently do bounded, reversible engineering inside this
repository: read, test, edit, and commit to the local branch by explicit
pathspec. It stops for the Art. VI.5 gates. Pushing is publication and needs
Kyle's explicit authorization per occasion unless a standing authorization
is recorded in `HUMAN_DECISIONS.md`. Installing host packages is outside the
repository and needs authorization. Another session's uncommitted work is
never discarded, reverted or bundled into a commit.

## Article XV — Release truth

A V12 release candidate carries **separate** receipts for:
- local focused tests
- the local authoritative suite
- fresh-environment verification
- CI
- real-repository proofs
- security/integrity checks (secret scan)
- public/private boundary checks
- documentation consistency (no `CONTRADICTED`/`STALE` claims in public docs)
- commercial evidence
- deployment verification

Each is exactly one of `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`,
`NOT_APPLICABLE`, `UNKNOWN`. They are **never collapsed into one percentage
or one word.** `foundation/launch_report.py` (`READY` /
`READY_WITH_LIMITATIONS` / `NO_GO`) derives its verdict and does not let
anyone choose it. `release.sh` is the existing gate; both are extended, not
replaced.

## Article XVI — Frozen baseline receipt R-F01 (2026-09-24)

The reference point for every later performance or health claim. It is never
edited; later states are recorded in the master plan's §4.

| Item | Value | Evidence class |
|---|---|---|
| HEAD at inspection | `4f0282c5` | LOCAL |
| Master plan commit | `99baed42` | LOCAL |
| Worktree | 6 uncommitted qualification→NEXT files (not discarded) | LOCAL |
| CI at `4f0282c5` | FAIL (`test (foundation)` ~11.5 min, exit 1). 11 jobs cancelled within ~1 s | CI (run `35963202116`) |
| Last green master CI | `c0a52300`, 2026-09-06 | CI |
| Local env | Python 3.14.4, no pip, no PyYAML | LOCAL |
| CI env | Python 3.12, PyYAML 6.0.3 | STATIC_INSPECTION of workflow |
| Local full run | FAIL. 3,579 tests, 23 m 26 s wall, user 6 m 55 s, sys 2 m 9 s, 11 light suites concurrent + `foundation` isolated, uncommitted work included | LOCAL |
| `foundation` | 3,248 tests, 1,392 s in the full run (~99% of wall). Isolated re-run: 893 s, 17 failures + 123 errors + 1 skip. 64 are PyYAML import errors, **76 are not** | LOCAL |
| Parse failure | `foundation/claude_code_adapter.py:21`, from `898f0c4c` | STATIC_INSPECTION (`ast.parse`) |
| Commercial | 0 customers, 0 payments. NLnet €30k submitted, pending | DOCUMENTED (`README.md`, `NLNET_SUBMISSION_RECEIPT.md`) |
| Private TITANOS.TECH | Exists per operator; NOT CONNECTED | DOCUMENTED (operator) |

## Article XVII — Enforcement map

This article states honestly which parts of this constitution code enforces.

| Law | Enforced by code today? |
|---|---|
| Discovery socket gated (Art. VI) | **Yes**: `fetch_feed()` → `authorize_discovery()`, `test_network_control_plane.py` |
| Per-state minimum authority (Art. VI) | **Yes**: `next_kernel.MIN_AUTHORITY`. Authority *grant* verification: **no** (Art. VI.2) |
| Qualification evidence binding (Art. I) | Partial: committed at `4f0282c5`, extended by uncommitted work |
| Unevidenced epistemic upgrade (Art. I, III) | **Yes**: `kpm` `MissingEvidence` |
| Local suite list = CI matrix (Art. V) | **Yes**: `sentinel.check_local_runner_matches_ci` (cannot run on this host without PyYAML) |
| Turbo labelled ADVISORY; never gates (Art. V) | **No** (no Turbo implementation yet) |
| Release requires full suite (Art. XV) | Partial: `release.sh` gates on `run_all_tests.sh` |
| Separate release receipts (Art. XV) | **No** |
| Failure ledger (Art. VIII) | **No** (process only) |
| No-drift preamble (Art. XII) | **No**: process only, judged each session |
| Secrets never public (Art. VII) | Partial: `secret_scanner.py`, `publication_gate.py` (the gate guards a human action; no in-repo push path) |

Anything marked "No" is `PROCESS_ONLY`. Per the Critical Function
Switch-Gate constitution, those rows are candidates for code enforcement in
their owning frontier. They are not claimed as enforced.

## Article XVIII — Amendment

Amend by a dated entry in the master plan's §21, citing the evidence. You
may amend to match reality. You may never amend to make a report look green.
Weakening Art. III, V, VI or VII requires Kyle's explicit decision, recorded
in `HUMAN_DECISIONS.md`.

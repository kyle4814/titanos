# TITANOS V12 — MASTER CAMPAIGN PLAN

**This file is the strategic north star. It is not the source of truth for
how the system works.** When it disagrees with the live repository, the
repository wins (§3), and this file gets corrected with a dated entry in §21.

Created 2026-09-24, V12 Frontier 01. Operator: Kyle. Primary executor: Claude
Code. Strategic/adversarial control: ChatGPT, via the operator.

Status words used throughout: **VERIFIED** (executed, with a receipt cited
here), **PARTIAL** (some code or proof exists, and the gap is named),
**PLANNED** (no implementation), **UNKNOWN** (not enough evidence),
**BLOCKED** (the named dependency is unmet), **HUMAN DECISION** (Kyle's call).
Moving an item from one state to the next needs evidence. No step skips:
PLANNED → BUILT → VERIFIED → PRODUCTION → COMMERCIAL → REVENUE.

---

## 1. Executive north star

TitanOS is an evidence-first engineering layer for AI systems. It turns
real-world input into evidence, qualified opportunities, human-authorised
action, receipts, and learning, and it refuses to manufacture certainty
anywhere on that path.

```
REAL WORLD → EVIDENCE → OBSERVED FACT → VALIDATION → PROVENANCE → SIGNAL
  → AI INTERPRETATION → OPPORTUNITY → HUMAN DECISION → ACTION → OUTCOME
  → RECEIPT → GOLD BRICK → COMMERCIAL VALUE → FEEDBACK → BETTER SYSTEM
```

**V12 objective:** more verified capability per unit of engineering change.
Architectural closure, evidence integrity, controlled autonomy, commercial
usefulness, repeatable execution. Code volume, agent count, doc volume and
feature count are not the measure.

This file consolidates and does not replace. The existing canonical
documents keep their jobs (§7, §15). This file adds the one thing none of
them has: a phased campaign map tied to the verified current state.

## 2. Epistemic doctrine

These are the V12 campaign rules. Every one of them restates doctrine that
already exists; none adds new doctrine.

| V12 rule | Already enforced / stated in |
|---|---|
| UNKNOWN > invented certainty | `kpm/schemas/epistemic_types.py`; `foundation/value_model.py` ("UNKNOWN is never zero") |
| RECEIPT > CLAIM | `foundation/receipt.py`, `receipt_ledger.py` |
| EXECUTION > STATIC INSPECTION; TEST RESULT > TEST FILE | `CLAUDE.md` "Local green is not evidence. Check CI." |
| LIVE MASTER > MEMORY | `TITANOS_GO_CYCLE_DOCTRINE.md` §V Zero-Trust Reconnaissance |
| CODE > DOCUMENTATION | `TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md` §1, §4 |
| REUSE > REBUILD; ONE CANONICAL PATH | GO Cycle §XV; Next-Lever Sequencer |
| HUMAN AUTHORITY > UNBOUNDED AUTONOMY | GO Cycle §XIII; `CLAUDE_CODE_OPERATING_CONTRACT.md` "Human gates" |
| MEASURE BEFORE OPTIMIZING; VERIFY BEFORE CLAIMING | Operating contract, rules 6 and 8 |

A file existing proves nothing about its contents. The same goes for a test
file (it may not pass), a CI config (CI may not pass), and a documented
capability (it may not run). A local green run does not prove CI green (see
§4, which is a live example).

## 3. Source-of-truth hierarchy

```
LIVE CODE > VERIFIED RUNTIME EXECUTION > TEST RESULTS > PERSISTENT SYSTEM STATE
  > VERIFIED RECEIPTS > THIS MASTER PLAN > ROADMAP / FRONTIER DOCS
  > MEMORY / HISTORICAL CONTEXT > HYPOTHESIS
```

Some state is **computed, not written down**, so no document may carry a
second copy of it:

| Question | Authority |
|---|---|
| HEAD, worktree, test inventory, ledgers, pulse findings | `python3 -m foundation.system_manifest` |
| Launch criteria | `python3 -m foundation.launch_report` (prints only; `write_artifacts()` regenerates `FINAL_SYSTEM_RECEIPT.json`, `CAPABILITY_MATRIX.md`, `REMAINING_LIMITATIONS.md`) |
| Autonomy | `python3 -m foundation.autonomy_metric` |
| Capability tier | `foundation/sigil.py::compute_sigil()` |
| Test result | `./run_all_tests.sh` (local), `.github/workflows/tests.yml` (CI, the authoritative check) |
| README test count | `foundation/autonomy_loop.py` (the only writer allowed) |

Corpus material (`corpus/`, 14k+ files) is **source material and never
executable authority.**

## 4. Current verified state (2026-09-24)

Every row below was observed in this frontier's session. Nothing was copied
from another document.

| Fact | Value | Evidence |
|---|---|---|
| Repository | `kyle4814/titanos`, **public**, default branch `master` | GitHub API `repos/kyle4814/titanos` → `private: false` |
| HEAD at start of frontier | `4f0282c5` ("test: reject noncanonical qualification refs"), level with `origin/master` | `git rev-parse HEAD`; `git rev-list --left-right --count` → `0 0` |
| History | 918 commits, one tag `v0.1.0` | `git log`, `git tag` |
| Worktree | **dirty**: 6 modified files, uncommitted qualification→NEXT work (see §6) | `git status --short` |
| **CI at HEAD** | **FAILED.** `test (foundation)` failed after ~11.5 min. The other 11 matrix jobs show `cancelled` within ~1 s of starting (cause UNKNOWN) | GitHub Actions run `35963202116`, check-run annotations: "Process completed with exit code 1" |
| **Last green CI on master** | `c0a52300`, 2026-09-06 ("[autonomy-loop] README.md: correct test-count drift"). The last 40 master runs all concluded `cancelled` at run level | GitHub Actions API, `status=success` query |
| README claim "CI is green" | **Contradicted by CI.** README:75-76 is stale | above two rows |
| This host's Python | 3.14.4, **no pip, no PyYAML** | `python3 -c "import yaml"` → `ModuleNotFoundError` |
| CI's Python | 3.12 with PyYAML 6.0.3 installed from `requirements.txt` | `.github/workflows/tests.yml` |
| Consequence | Any module importing `yaml` fails on this host, including `foundation.system_manifest` (via `sentinel`), so computed state is **not obtainable here** until the environment is provisioned | `python3 -m foundation.system_manifest` → traceback |
| Local full-suite run (not CI-equivalent) | **FAIL**: 3,579 tests ran, 23m26s wall. 3 suites OK (`firewall`, `gems/claim_ledger`, `provenance`). 8 light suites fail **only** on `ModuleNotFoundError: yaml` (every error is that import). `foundation`: 3,248 tests, FAIL, 1,392 s. Isolated re-run: 893 s, **17 failures + 123 errors, 1 skip**. Of those 140, **64 are the missing `yaml` and 76 are not** (see next row) | `./run_all_tests.sh` and per-suite `unittest`, this session, including the uncommitted §6 work |
| **Foundation defects independent of yaml** | 76 failing tests across ~40 modules, concentrated in the workforce / swarm / institutional-memory / retry / worker layer. Observed causes: **`foundation/claude_code_adapter.py` has a SyntaxError at line 21** (committed in `898f0c4c`; it is the only tracked non-corpus `.py` that fails to parse); circular imports (`execution_receipt` ↔ `execution_executor`); API drift (`OpportunityStore.get` missing, `InstitutionalMemoryStore.save()` signature, `regime_scheduler.apply_regime_flags` missing, `persist_assignment_outcome(expected_value=)`); `NameError: json` in `test_receipt_ledger`; behavioural assertion failures (batch planner, retry queue, probation routing, `test_reachability`). Whether any of the 76 comes from the uncommitted §6 work is **UNKNOWN**. CI at HEAD (without that work) also fails `foundation` | `unittest discover -s foundation` stderr, `ast.parse` over `git ls-files '*.py'` |
| Scheduling | None configured: no `schedule:` in CI, no cron/systemd/launchd files, `crontab` not installed on this host | repo search; `NEXT_MOVE.md`; `autonomy_ratio` last documented `0.0000` (not recomputed here, blocked by missing yaml) |
| Durable ledgers on this host | None present (`foundation/*.jsonl`, `~/.titanos/` absent); `income_watch_state.jsonl` (65 lines) is the only JSONL at root | `ls` |
| Commercial outcome | 0 customers, 0 revenue, 0 contracts, per the repo's own statement | `README.md:81`, `CAPABILITY_MATRIX.md`, `FINAL_LAUNCH_REPORT.md` |
| Only real external submission | NLnet application `2026-11-076`, €30,000, submitted 2026-09-06, outcome PENDING | `NLNET_SUBMISSION_RECEIPT.md` |

## 5. Current unknowns

| Unknown | Why it is unknown | What resolves it |
|---|---|---|
| Exactly which failures CI `foundation` hits at HEAD | Job logs need authenticated download; no `gh` on this host. The local non-yaml defects (§4) are the probable cause, especially the SyntaxError, but not confirmed against the CI log | `gh` auth, or reproduce on Python 3.12 + PyYAML |
| Whether the uncommitted §6 work adds failures | Not isolated (would need a stash-and-rerun, which touches the in-progress work) | Run the foundation suite on a clean checkout of HEAD |
| Why the other 11 CI jobs cancel within ~1 s | Same | Same; check Actions billing/concurrency settings (HUMAN) |
| Whether CI would pass on 3.12 today, minus the foundation failure | Not executed | Provisioned env + `run_all_tests.sh` |
| Current `system_manifest` / `launch_report` / `autonomy_metric` / `compute_sigil` values | Cannot import on this host (no yaml) | Provision PyYAML (HUMAN: host package install) |
| Private TITANOS.TECH repository contents | **PRIVATE REPOSITORY ACCESS = NOT YET CONNECTED** | Kyle grants access in a later frontier |
| Relationship of the separate `titan` repo (F-007) to TITANOS.TECH | `failures/FAILURE_ARCHIVE.md` F-007 records a rotated secret for `api.titanos.tech/internal/orders` in the `titan` repo's history. That suggests, but does not prove, that `titan` is (part of) the private plane | Access (F13) |
| NLnet outcome | External, pending | NLnet response |
| Real-world yield of any mouth/radar output | No outcome ledger on this host | Outcome recorded via `outcome_ledger.py` |

## 6. Current active engineering work

**Uncommitted at frontier start. Frontier 01 does not touch it.** It is the
live front of Frontier 04.

- `foundation/qualification.py`: `QualificationFactor`/`QualificationResult`
  type checks; `to_dict()`/`from_dict()` that re-validate persisted results;
  `evidence_ref()` = `"qualification:" + sha256(canonical to_dict)`.
- `foundation/next_kernel.py`: `Opportunity` now carries a full
  `qualification_result`. QUALIFIED requires that result to be persisted with
  band QUALIFIED, a matching publication id, and its `evidence_ref()` retained
  in `evidence_refs`, at O1 authority. Evidence can't be replaced once the
  lifecycle has moved past DISCOVERED.
- Tests: `foundation/test_next_kernel.py`, `foundation/tests/test_qualification.py`,
  `test_next_queue_integration.py`, `test_opportunity_cycle.py`.
- Recent history (8 commits, `4916f697`..`4f0282c5`) is the same line of work:
  gate qualification at O1 → require evidence → canonical evidence identity.

**Verified gap:** outside tests, no non-test code sets `qualification_result=`
or any authority above O0, so **nothing in production can reach QUALIFIED
today**. `opportunity_cycle.py` writes `state_dir/next_opportunities.json` at
O0/DISCOVERED. `operator_cli next-state` reads `~/.titanos/next_opportunities.json`
by default, which is a different path (a split-brain risk).

## 7. Architecture map

| Layer | Where | State |
|---|---|---|
| Epistemic library | `schema/`, `firewall/`, `kpm/`, `magl/`, `taal/`, `rpa/`, `narrative/`, plus `compiler/`, `legacy/`, `gems/claim_ledger`, `provenance/` | Each has `BUILD_REPORT.md`. 12 test suites (§9) |
| Instruments | `foundation/sentinel.py`, `sigil.py`, `system_manifest.py`, `launch_report.py`, `autonomy_metric.py` | Code + tests; blocked on this host (yaml) |
| Gates | `communication_gate.py` + `discovery_authorization.py` (**the only gate on a real action**: `mouth_common.fetch_feed()`), `publication_gate.py` (guards a human `git push`), others with no production caller (`hells_gate`, `contribution_gate`, `switch_hardener`, `taal/gate/root_gate`, `rpa/gates/human_jurisdiction`, `firewall/gate`) | Per `CLAUDE.md` "Gates" audit, 2026-09-01 |
| Sockets | `mouth_common.fetch_feed()` (GET/POST, gated READ), `telegram_notify.py` (NOTIFY_OPERATOR) | `test_network_control_plane.py` |
| Ingestion / radar | `mouth_*.py`, `tender_radar.py`, `tender_sources.py`, `signal_spine.py`, `tentacles.py` | Code + tests. `AUDIT_2026_09_02.md`: 4 of 8 mouths have no production caller |
| Qualification / NEXT | `qualification.py`, `eligibility.py`, `next_kernel.py` (16 states, O0–O4 authority, atomic JSON store) | PARTIAL (§6) |
| Workforce / swarm / institutional memory | `workforce.py`, `next_leases`, `next_acquire`, `worker_*`, `swarm_*`, `coordination_*`, `dispatcher_recovery`, institutional-memory modules | Mostly reachable **only from tests**, and **the main site of the 76 non-yaml test failures** (§4). `claude_code_adapter.py` does not parse |
| Execution / receipts | `execution_dispatcher`, `executor`, `receipt*.py`, `reconciliation*`, `business_receipt.py`, `learning_receipt.py` | Code + tests |
| Outcome / learning | `outcome_ledger.py`, `opportunity_pipeline.py`, `opportunity_cycle.py`, `opportunity_feedback.py`, `learning_store.py` | Code + tests; calibration tests thin |
| Gold Brick / offer | `gold_brick.py` (`GoldBrick`, `DeliveryRecord`), `offer_router.py` | Code + tests. `route_offer` **has no caller**; all 3 bricks are internal |
| Autonomy | `autonomy_loop.py` (README drift only), `autonomous_window.py`, `checkpoint.py`, `write_scope.py` | Unscheduled by design (`NEXT_MOVE.md`) |
| Operator surface | `foundation/operator_cli.py`, `scheduled_brief.py`, `.claude/commands/{boot,go,next}.md` | Code; cron recipes documented, not installed |

## 8. Public / private boundary

```
PUBLIC TITANOS  (kyle4814/titanos — verified public)
   │  controlled, documented interface  ← NOT YET DEFINED IN CODE
   ▼
PRIVATE TITANOS.TECH  (exists per operator; ACCESS = NOT YET CONNECTED)
   ├── production infrastructure         UNKNOWN
   ├── private data                      UNKNOWN
   ├── credentials / secrets             UNKNOWN (one historical: F-007)
   ├── commercial systems                UNKNOWN (Stripe per .claude/commands/next.md §0.47)
   ├── customer workflows                UNKNOWN
   ├── payment infrastructure            UNKNOWN
   └── controlled external actions       UNKNOWN
```

What the public repo shows about the private side (references only, none verified):
- `.claude/commands/next.md` §0.47 says: treat the private commercial
  infrastructure as an already-built execution plane, and do not rebuild
  Stripe, payment links, delivery, or customer workflow.
- `failures/FAILURE_ARCHIVE.md` F-007: `api.titanos.tech/internal/orders`
  existed and had a secret committed in the `titan` repo. That secret was
  rotated, but the history was not cleaned (HUMAN DECISION #2 in `HUMAN_DECISIONS.md`).
- `titanos.tech` appears as a contact/brand string in `gold_brick.py:89`,
  `contribution_gate.py:221`, `opp_drop.py`, `operator_cli.py` and
  `NLNET_SUBMISSION_RECEIPT.md`.

Rules that stand now: no secrets are printed or committed; public docs make
no claims about private state; the interface is derived from both
repositories once F13 connects, and is not designed ahead of that.
`publication_gate.py` and `secret_scanner.py` are the existing enforcement
for the public side.

## 9. V12 Turbo strategy (Frontier 01)

Two verification tiers, never merged:

| Tier | Purpose | May use | Authority |
|---|---|---|---|
| **TURBO** (development) | Fast feedback on a change | Changed-file impact selection, parallelism, deterministic caching, fixture reuse, failure-first reruns, `--fast` | Advisory only. **Never gates a commit or release** |
| **AUTHORITATIVE** (release) | Truth | Full `./run_all_tests.sh` (no flag) **and** green CI on the exact commit | The only gate. `release.sh` already gates on it |

**What exists today (reuse, don't rebuild):**
- `run_all_tests.sh`: 12 suites. The 11 light suites run concurrently, then
  `foundation` runs in isolation (a nested sigil swarm starved under shared
  load, diagnosed 2026-09-05). `--fast` sets `TITAN_SKIP_REALREPO_SIGIL=1`
  and skips the real-repo sigil class.
- `sentinel.check_local_runner_matches_ci` keeps the runner's suite list and
  the CI matrix in agreement.
- CI: 12-job matrix, `cancel-in-progress` concurrency, 15-min per-job cap.

**Measured shape (2026-09-24, this host):**

| Suite | test files |
|---|---|
| foundation | 245 (of 289 total) |
| rpa / taal | 10 / 11 |
| all other 9 suites | 1–8 each |

- 9 foundation test files spawn subprocesses. Three touch the real-repo
  sigil / authority pulse (`test_sigil.py`, `test_sentinel.py`,
  `test_authority_pulse.py`).
- No changed-file impact analysis exists anywhere in the repo.

**Baseline, this host, 2026-09-24 (not comparable to CI until provisioned):**

| Measure | Value |
|---|---|
| Full `./run_all_tests.sh` wall time | 23 m 26 s (user 6 m 55 s, sys 2 m 9 s) |
| `foundation` alone (serial, isolated) | 1,392 s, 3,248 tests: **~99% of wall time** |
| 11 light suites (concurrent) | 3–10 s each. Their tests execute in <0.5 s, so the time is interpreter startup and import |
| CI `foundation` job at HEAD | ~11.5 min, then failed |

The low user+sys time against 23 minutes of wall time says `foundation` is
dominated by **waiting**, not computation: subprocess swarms, timeouts or
sleeps. Frontier 01's first measurement target is a per-test-file duration
profile of `foundation`. It is not the light suites, whose total cost is
seconds.

**Divergences between local and CI, found this session (each is a Turbo input):**
1. Python 3.14 locally vs 3.12 in CI.
2. PyYAML is missing locally and installed in CI.
3. Local discovery uses the default pattern `test*.py`; CI passes `-p "test_*.py"`.
   They are **equivalent today**: `find` shows no test file matching
   `test*.py` without the underscore. But nothing enforces that, so a
   future `tests.py`-style file would run locally and not in CI.
4. CI foundation takes ~11.5 min on a single runner and fails; the local
   foundation result is in the baseline above.

**Turbo sequence (measure → optimize → re-measure):**
1. Provision the environment to match CI (3.12 + PyYAML). Until then,
   baselines on this host are not comparable to CI.
2. Record a per-suite and per-test-file timing baseline (unittest
   `--durations` on 3.12+, or per-module timing).
3. Build an impact map from changed files to affected test modules, based
   on the import graph. Advisory, with a conservative fallback: if unsure,
   run the whole suite.
4. Only then optimize the measured top-N costs. Candidates, none assumed:
   the real-repo sigil PROOF swarm, subprocess startup, repeated fixtures.
5. Turbo receipt: every Turbo run prints `ADVISORY — not authoritative`
   plus the selected/skipped set.

Forbidden: deleting or weakening a slow test, mocking a real proof without
an equivalent authoritative gate, letting Turbo output gate a commit.

## 10. 30-frontier campaign map

Frontiers are strategic, and the order is refined by evidence (§11). Each
row gives the frontier's purpose, dependencies, intended outcome, required
evidence and current state.

### Phase I — Engineering truth / speed

| # | Frontier | Purpose / intended outcome | Depends on | Evidence required | Current state |
|---|---|---|---|---|---|
| 01 | V12 Turbo — test infrastructure | Fast advisory verification + untouched authoritative gate | 05 (a trustworthy baseline) | Before/after timing receipts; full suite unchanged | PARTIAL: `--fast`, parallel runner exist; no impact analysis; baseline §9 |
| 02 | North star / execution constitution | One strategic control document tied to live state | — | This file, committed | **This commit** (plan). The constitution itself = `CLAUDE.md` + `CLAUDE_CODE_OPERATING_CONTRACT.md` + 19 doctrine files; consolidation PLANNED |
| 03 | Public ↔ private architecture | Explicit, code-checkable boundary | 13 (access) | Interface spec derived from both repos | BLOCKED: private access NOT YET CONNECTED |
| 04 | Qualification / NEXT closure | QUALIFIED reachable only with persisted, evidence-bound qualification at O1, from a production caller | — | Committed tests + a production caller + split-brain path fixed | PARTIAL: uncommitted work (§6); no production caller; state-path split |
| 05 | Foundation baseline restoration | CI green on master again; local == CI | Env provisioning (HUMAN for host packages) | Green CI run on a named commit | **FAILING**: CI foundation red at HEAD; last green 2026-09-06. Locally, 76 non-yaml failures (§4), including a committed SyntaxError |
| 06 | Evidence / receipts / observability | One coherent receipt model | 05 | Map of the 62 receipt-mentioning modules → canonical set | PARTIAL: `receipt.py`, `receipt_ledger.py` (hash-chained) + many variants |

### Phase II — Intelligence loop

| # | Frontier | Purpose / intended outcome | Depends on | Evidence required | Current state |
|---|---|---|---|---|---|
| 07 | Workforce / institutional memory | Workforce modules reachable from a real entrypoint, or retired | 04, 06 | Production call graph | **FAILING**: modules exist, mostly test-only callers; most of the 76 non-yaml foundation failures are here |
| 08 | Real ingestion → opportunity | Mouths → signal → NEXT with provenance | 04, 12 | Live sweep receipt landing in the canonical NEXT store | PARTIAL: mouths + `opportunity_cycle` write O0 records; 4/8 mouths uncalled (`AUDIT_2026_09_02.md`) |
| 09 | Autonomy / human authority | Authority levels O0–O4 enforced in code, not only in `.claude/commands/next.md` | 04 | Tests on authority escalation | PARTIAL: `next_kernel` MIN_AUTHORITY; meanings only in command prose |
| 10 | Gold Brick factory | Bricks for external problems, not only self-describing | 04, 08 | A brick from a real external signal | PARTIAL: `gold_brick.py`; 3 internal bricks |
| 11 | Outcome → learning → calibration | Recorded outcomes adjust ranking | 08, 10 | Durable `outcome_ledger.jsonl` with real records | PARTIAL: code; no ledger on this host; thin calibration tests |
| 12 | Signal fusion / source registry / provenance | One source registry, freshness | — | Registry covers all live mouths | PARTIAL: `signal_spine.py`, `tender_sources.py`, `kpm/source-vault` |

### Phase III — Product / commercial

| # | Frontier | Purpose / intended outcome | Depends on | Evidence required | Current state |
|---|---|---|---|---|---|
| 13 | TITANOS.TECH private production | Connect and reconcile the existing private repo | **HUMAN: access** | Inspection receipt of the private repo | BLOCKED: NOT YET CONNECTED |
| 14 | Commercial / payment / delivery pipeline | Offer → payment → delivery → receipt across the boundary | 03, 13 | One end-to-end sandbox transaction receipt | PLANNED here; private plane UNKNOWN |
| 15 | Investment / strategy suite | Measurable targets, capital, milestones, risks (§14) | 05, 11, 13 | Every figure labelled OBSERVED/VERIFIED/MODELLED/REALIZED | PARTIAL: `investor/`, `INVESTMENT_OPPORTUNITY_MAP.md`; no numbers |
| 16 | Operations documentation | Canonical executable procedures (§15) | 04, 05 | Each procedure runnable as written on a fresh clone | PARTIAL: 3 overlapping entry docs |
| 17 | Developer / contributor experience | Clear extension path | 05, 16 | Fresh-clone contributor walkthrough | PARTIAL: README quickstart; stale claims |
| 18 | External integrations / controlled actions | Every outbound action gated | 09, 19 | `test_network_control_plane.py`-style attack tests per socket | PARTIAL: 2 gated sockets |

### Phase IV — Deployability / trust

| # | Frontier | Purpose / intended outcome | Depends on | Evidence required | Current state |
|---|---|---|---|---|---|
| 19 | Security / secrets / trust boundaries | Boundaries hold across both repos | 03, 13 | Secret scan both repos; F-007 decision | PARTIAL: `secret_scanner.py`; F-007 = HUMAN DECISION |
| 20 | Telemetry / health / reporting | Health computable anywhere | 05 | `system_manifest` runs clean on CI and host | PARTIAL: tools exist; blocked on host env |
| 21 | Recovery / backup / migration | Restart and restore proven | 06, 11 | Kill/restore drill receipt | PARTIAL: `checkpoint.py`, `dispatcher_recovery`, `swarm_recovery`; six in-memory "ledgers" (`CLAUDE.md` Durability) |
| 22 | Adversarial / chaos campaign | Failure injection against live paths | 05, 21 | Injection receipts | PARTIAL: many adversarial unit tests; no chaos harness |
| 23 | Autonomy windows / scheduling / gates | Scheduled work with bounded authority | 09, 20, **HUMAN** | `autonomy_ratio` > 0 with receipts | **HUMAN DECISION** (`NEXT_MOVE.md`: "do not schedule yet") |
| 24 | Deployment reproducibility | Same result on any host | 05 | Fresh env matches CI | FAILING: this host lacks PyYAML/pip |

### Phase V — Launch

| # | Frontier | Purpose / intended outcome | Depends on | Evidence required | Current state |
|---|---|---|---|---|---|
| 25 | Release / packaging / versioning | Signed, reproducible release | 05, 24 | Release receipt | PARTIAL: `v0.1.0`, `release.sh`, unsigned (no key: HUMAN) |
| 26 | Public docs / positioning | Public claims match computed state | 05, 20 | Zero stale claims (§15 list) | PARTIAL: README CI claim stale |
| 27 | Investor / commercial materials final | Derived from verified reality | 15, 28 | Receipts behind each claim | PLANNED |
| 28 | Gold Brick → customer → payment → delivery proof | First real commercial loop | 10, 13, 14 | Payment + delivery receipt | PLANNED; 0 customers (`README.md:81`) |
| 29 | End-to-end rehearsal | Whole system, one run | 01–28 as applicable | Rehearsal receipt | PLANNED |
| 30 | Final V12 release audit / launch gate | Adversarial go/no-go | 29 | `launch_report` READY + human sign-off | PLANNED; last receipt `READY_WITH_LIMITATIONS` (2026-08-31, stale) |

## 11. Frontier dependencies and evidence-based ordering

```
05 baseline ──► 01 turbo ──► (every later frontier verifies faster)
   │
   ├──► 06 receipts ──► 07 workforce ──► 21 recovery ──► 22 chaos
   └──► 20 telemetry ──► 23 scheduling (HUMAN)
04 qualification/NEXT ──► 08 ingestion ──► 10 gold brick ──► 11 learning
                    └──► 09 authority ──► 18 integrations
13 private access (HUMAN) ──► 03 boundary ──► 14 commerce ──► 28 proof ──► 29 ──► 30
```

**Refinement recorded now (Next-Lever Sequencer, rung 1 "remove the blocker"):**
Turbo (01) stays the campaign's first priority. But Turbo's first step is a
baseline, and a baseline measured against a red CI and an unprovisioned host
isn't comparable to anything. So **01 and 05 execute as one opening move**:
provision → reproduce the CI foundation failure → repair → record the green
baseline → then optimize. The repair starts with the smallest verified
defect: `foundation/claude_code_adapter.py:21` does not parse, and
`sentinel.check_python_syntax` would have reported it if the sentinel could
run here. Separately, the **uncommitted 04 work should be
landed or parked first**, because a dirty tree blocks clean commits and
`autonomy_loop` refuses to run on one.

## 12. Commercial architecture

| Stage | What exists | State |
|---|---|---|
| REAL PROBLEM | `tender_radar.py`, `tender_sources.py`, `mouth_*` feeds; research docs `DEALS_*.md` | PARTIAL (code + tests; research docs unverified) |
| EVIDENCE | `receipt.py`, `opportunity.py` (`SignalEvidence`) | PARTIAL (code + tests) |
| QUALIFICATION | `qualification.py`, `eligibility.py`, `next_kernel.py` | PARTIAL (§6) |
| GOLD BRICK | `gold_brick.py` | PARTIAL: internal bricks only |
| COMMERCIAL DOOR / OFFER | `offer_router.py`, `business_receipt.py` | PARTIAL: `route_offer` has no caller, no registered `OfferCapability` |
| PAYMENT | None in public repo | UNKNOWN (private plane, NOT YET CONNECTED) |
| DELIVERY | `gold_brick.DeliveryRecord` (unconstructed outside tests); SpoofGuard (`SPOOFGUARD.md`, `email_security_report.py`) | PARTIAL / UNKNOWN (private) |
| RECEIPT | `receipt*.py`, `business_receipt.py` | PARTIAL |
| OUTCOME | `outcome_ledger.py`, `opportunity_cycle.py` | PARTIAL: no ledger on this host |
| LEARNING | `opportunity_feedback.py`, `learning_store.py`, `learning_receipt.py` | PARTIAL: thin tests |

**Observed external events:** one grant submission (NLnet, pending). No
payment, customer or paid delivery is evidenced anywhere in the public repo.

## 13. TITANOS.TECH integration plan

**PRIVATE REPOSITORY ACCESS = NOT YET CONNECTED.** Nothing about its contents
is asserted here.

When access is granted (Frontier 13):
1. **Read-only inspection first.** Structure, stack, entrypoints, tests, CI,
   secrets handling. No values are printed.
2. Reconcile it against §8 and §12. Every UNKNOWN there becomes a cited fact
   or stays UNKNOWN.
3. Derive the public↔private interface from what both sides actually call.
   Don't design one ahead of that.
4. Check whether the `titan` repo from F-007 is the private plane or part of
   it, and bring HUMAN DECISION #2 (history remediation) back to Kyle with that context.
5. Only then plan Frontier 14 changes. Per `.claude/commands/next.md` §0.47,
   do not rebuild existing private payment/delivery.

## 14. Investment strategy requirements

Existing material to build on, not replace: `INVESTOR_INDEX.md` (the hub,
OBSERVED→VERIFIED→MODELLED→REALIZED rule), `investor/THESIS.md`,
`investor/INVESTMENT_PLAN.md` (Milestones A–D), `investor/MILESTONES.md`,
`investor/DUE_DILIGENCE.md`, `investor/OPPORTUNITY_MAP.md`,
`INVESTMENT_OPPORTUNITY_MAP.md`, `VISION_MAP.md`.

| Required section | Present? |
|---|---|
| Thesis, problem, product, architecture, technical differentiation | Present (`investor/THESIS.md`, README) |
| Evidence / validation receipts | Partial (engineering receipts only) |
| Traction | Correctly stated as none |
| Market sizing, segment | **Missing** |
| Business model, pricing, unit economics | **Missing** (scattered unvalidated prices in research docs, e.g. `DEALS_PRODUCTS.md`) |
| Go-to-market | Missing (operator cold-calling is noted, not planned) |
| Capital requirement, allocation, timeline | Missing amount/timeline; priorities exist |
| Technical + commercial targets, milestones | Partial (Milestones A–D, commercial "not assumed") |
| Competitors, team | Missing |
| Business risk register, assumptions | Missing (engineering risks only, `FINAL_LAUNCH_REPORT.md`) |
| Future gates | Partial (`launch_report` criteria) |

Every missing figure stays UNKNOWN until evidenced or explicitly labelled
MODELLED. No traction, revenue, customer or market number is written
without a source.

## 15. Operations documentation strategy

**Canonical owners today:**

| Question | Owner |
|---|---|
| Model-session workflow (`/boot`→`/go`) | `OPERATOR_GUIDE.md` |
| Non-developer CLI operation | `HOW_TO_RUN.md` |
| Agent-run opportunity sweep | `RUNBOOK_OPPORTUNITY.md` (`swarm_contract.run_swarm_task()`) |
| Human-only actions | `HUMAN_DECISIONS.md` (the canonical owner). Also duplicated in `HUMAN_LAUNCH_CHECKLIST.md`, `FINAL_LAUNCH_REPORT.md` and `OPS_BOARD.md` "Things only you can do" |
| Next recommendation | `NEXT_MOVE.md` |
| Engineering frontier | `PARETO_FRONTIER.md` |
| Execution loop | `CLAUDE_CODE_OPERATING_CONTRACT.md`, `COMMAND_LEXICON.md` (spec only) |

**Stale or contradictory claims found (a consolidation queue for F16/F26, not fixed here):**
- `README.md:75-76` says tests pass and CI is green, but CI is red at HEAD (§4).
- `TITANOS_LAYER0_RECURSIVE_PARETO_FRONTIER.md` and
  `TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md` still say "no GitHub remote".
- `HUMAN_DECISIONS.md` item 12 and `TITANOS_COMMUNICATION_SWITCH_001.md`'s
  invariant say "zero network". Both are superseded, per `CLAUDE.md`.
- Test counts disagree across at least 7 documents (1,135 to 4,366). Only
  the README count has an authorised writer.
- The cron recipes point at `/home/tech2/cosmic-library`, but the repo
  now lives at `/home/userland/titanos`.
- `HUMAN_DECISIONS.md` header says "Last compiled 2026-08-25" while its
  contents run to 2026-09-04.
- `PARETO_FRONTIER.md` lists FRONTIER-024/025 as CLOSED but still under Active.
- `OPS_BOARD.md` (3,441 lines) mixes a changelog, a sales board and a
  strategy memo.

Approach: consolidate into canonical executable procedures (boot, test,
inspect state, ingest, qualify, NEXT, dispatch, authority, act, receipt,
recover, learn, commercial, boundary, deploy, diagnose, release). Each is
proven runnable on a fresh clone. Historical material is archived, not
deleted.

## 16. Security / authority model

- **Human gates** (union of GO Cycle §XIII and the operating contract):
  credentials, legal commitments, money, irreversible production changes,
  external communication as the founder, ownership, ambiguous authority,
  constitutional changes.
- **Coded enforcement that is load-bearing today:** `discovery_authorization`
  / `communication_gate` on `fetch_feed()`, and `telegram_notify` on
  NOTIFY_OPERATOR.
- **Declared but unwired:** most other gates (§7). Their existence is not
  evidence that anything passes through them.
- **NEXT authority:** O0 observe, O1 qualify, O2 reversible commit, O3/O4
  need Telegram verification. Enforced as a per-state minimum in
  `next_kernel.py`; the meanings are defined only in `.claude/commands/next.md`.
- **Open HUMAN DECISIONS relevant here:** F-007 history, four-eyes release
  review, `root_gate` risk tolerance, scheduling (`HUMAN_DECISIONS.md` #2,
  #4, #5, #13, #14).

## 17. Launch definition

V12 is launched only when **all** of these hold, each with a cited receipt:
1. Green CI on the release commit, plus the local authoritative run on an
   environment matching CI.
2. `launch_report` READY. `READY_WITH_LIMITATIONS` counts only if each
   limitation is explicitly accepted by Kyle.
3. Public docs contain no stale claims against computed state.
4. The public↔private boundary is documented from both repositories and
   secret-scanned.
5. At least one complete Gold Brick → customer → payment → delivery →
   receipt → outcome loop (F28). If that has not happened, launch is
   declared as **engineering-only**, never as commercial.
6. Kyle signs off (`GERMAN_ENGINEERING_SIGNOFF.md` human half).

## 18. Evidence / receipt requirements

- A frontier closes with: commit hash, the tests actually executed (command
  and result), CI run id/conclusion for that commit (or UNKNOWN with the
  reason), and files changed.
- Numbers are cited to the command that computed them. They are never
  copied from another document.
- Turbo results are labelled ADVISORY.
- Anything commercial uses the OBSERVED/VERIFIED/MODELLED/REALIZED labels
  from `INVESTOR_INDEX.md`.

## 19. Drift-control protocol

- **Plan drift** (implementation moves on and this file goes stale): every
  frontier's receipt updates §4, §6, §20 and §21. A frontier isn't closed
  until that update is made.
- **Implementation drift** (this file drifts into fantasy): §4 rows must
  cite evidence gathered in the same session that edits them. A row that
  can't be re-verified reverts to UNKNOWN.
- A conflict between this plan and the repository gets recorded in §21
  with its evidence. The plan is corrected; the repository is never forced
  to match the plan.
- This file must not carry a hand-maintained test count or a current-HEAD
  claim outside the dated §4 snapshot. Current values come from §3's
  computed sources.
- Note: this filename matches `system_manifest.py`'s `TITANOS_*.md` doctrine
  glob, so it counts toward `doctrine_files`. It is deliberately **not**
  `@`-imported into `CLAUDE.md`. Per `TITANOS_MEMORY_IRRELEVANCE_PROTOCOL.md`
  it is Tier 3, retrieved on demand, not loaded at every boot.

## 20. Current frontier state

| Item | State |
|---|---|
| Frontier 01 / 02 (this plan) | Plan committed; Turbo implementation not started |
| Recommended next move | **05+01 opening:** (a) fix the `claude_code_adapter.py` SyntaxError (needs no environment); (b) provision a CI-equivalent env (Python 3.12 + PyYAML; host install = HUMAN DECISION); (c) triage the 76 non-yaml foundation failures by root cause; (d) green baseline + CI receipt; (e) only then Turbo optimization |
| Parallel, independent | Land or park the uncommitted 04 work (Kyle/executor decision: it is in-progress work, not this frontier's) |
| Blocked on Kyle | Private repo access (F13); `gh` auth for CI logs (optional); scheduling (F23); F-007 remediation |

## 21. Change / revision history

| Date | Frontier | Change | Evidence |
|---|---|---|---|
| 2026-09-24 | 01 | Created. Consolidated from live repo inspection plus `CLAUDE.md`, the operating contract, `HUMAN_DECISIONS.md`, `NEXT_MOVE.md`, `PARETO_FRONTIER.md`, investor docs and ops docs. Recorded CI red at HEAD (last green 2026-09-06), host missing PyYAML, 76 non-yaml foundation failures including a committed SyntaxError, full-suite baseline 23m26s, private repo not connected | §4, §9 |

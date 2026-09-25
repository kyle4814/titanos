# EXP-002 — Foundation baseline restoration (V12 Frontier 03)

The machine-readable record is `RESULTS.json`. It lists every failing test
in both runs with its exception signature, cause class, category and
disposition. This file is the human-readable receipt.

**Evidence class: LOCAL, in a CI-parity environment. It is not CI.** No
claim is made here that the repository or CI is green.

## Environment

| | This run | CI (`.github/workflows/tests.yml`) |
|---|---|---|
| Python | 3.12.14 (uv-managed) | 3.12 |
| PyYAML | 6.0.3 from `requirements.txt` | 6.0.3 from `requirements.txt` |
| Arch / host | aarch64, UserLAnd proot on Android | x86_64 `ubuntu-latest` |
| Checkout | git worktree | primary checkout |

The system Python here is 3.14 with no pip and no PyYAML (Frontier 01
baseline R-F01). That setup cannot reproduce CI at all: 8 of 12 suites
failed only on `import yaml`. The 3.12 environment lives in `~/.venvs/`,
outside the repository. No project dependency, workflow or runner file
was changed.

## Results

| | Baseline | After |
|---|---|---|
| Commit | `7b7aad88` (clean) | `7031430f` (clean) |
| Mode | Full (no `--fast`) | **ADVISORY** `--fast` (real-repo sigil class skipped) |
| 11 light suites | all OK | all OK |
| `foundation` tests run | 3,751 | 3,802 (+51 that could not even import before) |
| `foundation` failures + errors | **20 + 63 = 83** | **16 + 31 = 47** |
| New failures | — | **0**: every after-run failure also fails in the baseline |
| `foundation` wall time | 11,115 s (user 2,011 s, sys 1,316 s) | 10,428 s (not comparable: `--fast`, concurrent load) |

The after-run skipped one class (`--fast`), so both sides are compared with
it excluded. Of the 83 baseline entries, 36 no longer fail. The rest are
failures still blocked on the unresolved contracts below; some of them
simply get further before failing now.

## Root causes repaired (one commit each)

| Commit | Cause | Class |
|---|---|---|
| `6d0955c3` | `claude_code_adapter.py:21`: a `"\n"` had become a literal newline, splitting the string | PRODUCT_DEFECT |
| `8cdcae9b` | `execution_receipt` ↔ `execution_executor` import cycle (from `dc68e9e4`); 17 test modules could not load | PRODUCT_DEFECT |
| `9dffdfd7` | Unmasked by the above. A replayed approval **re-ran the adapter** (a real side effect) before the store rejected the duplicate receipt. Now matches `ExecutionDispatcher`'s existing contract: an already-receipted intent returns its receipt. A mutation-checked test pins "adapter runs once" | PRODUCT_DEFECT |
| `04be92ab` | Test patched `authorize_communication` in `execution_approval`; the gate is looked up in `telegram_approval`. With the gate closed, the result is `UNAVAILABLE` (verified) | TEST_DEFECT |
| `c2106c83` | Five production modules and five tests called `OpportunityStore.get()` and `Opportunity.opportunity_id`, neither of which ever existed (`git log -S`). Aligned to the existing `load()[id]` / `.id`. Adding `get()` would have meant editing the then-uncommitted `next_kernel.py` | CONTRACT_DRIFT |
| `8d38f972` | `swarm_recovery` called `recover_expired()` twice; the first call clears the leases, so expired work was never requeued | PRODUCT_DEFECT |
| `2215708c` | Stale test imports (`apply_regime_flags` renamed in `fcc600e4`; missing `import json`) | TEST_DEFECT |
| `2c14aa2e` | Institutional memory could not reload anything it saved: the checksum was recomputed with the stored receipt included, and specialization was serialised as a dict the loader rejects. Both mutation-checked | PRODUCT_DEFECT |
| `7031430f` | Six files of qualification→NEXT work, committed on operator instruction. Tests committed at `4f0282c5` had run ahead of the implementation. 6 failures → 0 | CONTRACT_DRIFT |

## Not repaired: the contract is ambiguous or needs a decision

- **Authority** (2 tests, `authority_result`, `transactional_worker`). A
  worker result tries to move an O0 record to PREPARED. `next_kernel`
  requires O1 (since `2e5aa1ae`), and DISCOVERED→PREPARED is not a legal
  transition. Changing either side changes authority semantics, which is
  a stop condition.
- **Institutional-memory empty state** (~15 tests). Tests disagree on
  whether an absent store is `{}` or the empty-memory payload. Trying
  either convention fixed one set of tests and broke the other, so no
  convention was chosen.
- **Workforce / probation / retry / planner** (~15 tests). These modules
  were created 2026-09-23/24, after the last green CI (2026-09-06), and
  their tests contradict each other: one success releases quarantine
  (`test_retry_isolation`) versus two (`test_worker_probation`).
- **Tests for APIs never built or since removed.** `assign_worker` (never
  existed); a richer `persist_assignment_outcome(...)`;
  `evidence_admission` (module deleted in `605df218` 76 s after its test
  was committed, and the commit does not name what it duplicated).
- **`regime_recovery`.** Does "shift" mean change over time, or a
  persistent miss?
- **`test_reachability`.** New modules lack an intent classification.
  Not investigated.
- **Environment.** The real-repo sigil proof timed out (its nested
  `foundation` run exceeded 600 s on this host). The
  `remote_configured=no` result is a worktree artifact: `sigil.py` reads
  `repo_root/.git/config`, and in a worktree `.git` is a file.

## Where the time goes (V12 Turbo input, baseline run)

- **62 of 3,751 `foundation` tests (1.7%) account for 7,123 s, 97% of
  measured test time.** The other 3,636 tests take 52 s combined.
- By module:

  | Module | Time | Tests |
  |---|---|---|
  | `test_system_manifest` | 2,258 s | 13 |
  | `test_sentinel` | 1,502 s | 280 |
  | `test_launch_report` | 809 s | 19 |
  | `test_capability_registry` | 803 s | 18 |
  | `test_closed_loop_reality` | 779 s | 5 |
  | `test_secret_scanner` | 283 s | 11 |
  | `test_conclusion_gate_integration` | 235 s | 11 |

- About 3,760 s of wall time falls outside any test body: class setup,
  plus the nested real-repo sigil `foundation` run.
- One `compute_manifest()` takes 175 s here. 68% of that is
  `secret_scanner.scan` reading 16,285 files (open 43 s, read 29 s,
  stat 17 s) and 9% is three `git` subprocesses. Test classes repeat it
  per test (e.g. `test_launch_report` calls `assess()` in `setUp`).
- CPU was ~30% of wall time. The cost is filesystem and process I/O,
  amplified by proot. It is not computation.

These are measurements, not an optimisation. Nothing was changed for speed.

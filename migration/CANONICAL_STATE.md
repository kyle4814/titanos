# TITANOS — CANONICAL STATE (migration snapshot)

Snapshot of `/home/userland/titanos_state.txt` (the phone host's "North
Star" file), brought into the repository on 2026-09-25 so the PC starts
from one source of truth. Rank: BELOW the code, tests and git history. If
they disagree with this file, this file is wrong — fix it from evidence.
No secrets here, ever.

Captured: 2026-09-25. Source HEAD before the migration commit:
`100b41b1073b3acf1d95bb823e47e29d291ba59a`.

## SOURCE-OF-TRUTH MAP
- Law: `TITANOS_V12_CONSTITUTION.md` | Map/state: `TITANOS_V12_MASTER_PLAN.md`
- Executor loop: `CLAUDE_CODE_OPERATING_CONTRACT.md` | Human calls: `HUMAN_DECISIONS.md`
- Failures: `failures/FAILURE_ARCHIVE.md` | Baseline: `experiments/EXP-002/`
- Operator style: `migration/operator_memory/` (copy of the phone host's Claude memory)
- This migration: `migration/PC_MIGRATION_MANIFEST.md`

## REPOSITORY STATE
- github.com/kyle4814/titanos (PUBLIC), branch `master`
- remote `origin/master` at capture: `4f0282c5a176ec14f255a92a40801f9cf5303753`
- local was 23 ahead / 0 behind (fast-forward) plus this migration commit
- git identity: none on the phone host; commits are authored
  `kyle4814 <tech2scale@gmail.com>` via `git -c user.name=... -c user.email=...`

## UPDATE 2026-09-26 (PC host) — receipt provenance closed, CI unblocked
- `0a6c6d24` fix: gateway trusts an existing execution receipt only with
  Ring 0 provenance (`ExecutionReceipt.sign/verify`, domain "receipt-v1",
  fail-closed `ReceiptIntegrityError`, same-fingerprint execution serialised
  under `dispatcher._execution_lock`). Local: 24/24 new + 125/125 relevant.
  Frontier 1 below is CLOSED for `execute_permitted`; the legacy unsigned
  paths (`receipt_from_result`, `approved_dry_run_with_receipt`,
  `_execute_approved_with_receipt`, reconciliation receipts) are untouched
  and still have no production caller.
- `8559e537` fix: prevent matrix jobs from self-cancelling. Root cause of
  every cancelled run since `e4c9500b` (2026-09-23): job-level concurrency
  group keyed on workflow+ref only, shared by all 12 matrix jobs,
  `cancel-in-progress: true` -> 11/12 cancelled within 1 s. Group now
  includes `matrix.subsystem`.
- **First full-matrix CI result since 2026-09-06:** run `36188217313`,
  SHA `8559e537`, 12/12 jobs executed, 0 cancelled. 11 suites PASS
  (schema, firewall, kpm, magl, rpa, taal, narrative, legacy, compiler,
  gems/claim_ledger, provenance). **`foundation` FAIL**: 3904 tests,
  16 failures + 30 errors (42 distinct tests), 315 s. All 42 names are in
  the EXP-002 / `failures/FAILURE_ARCHIVE.md` baseline record; none is a
  provenance/gateway/receipt/approval/Ring 0/pause/dispatcher test.
  **CI is RED, not green.** Gate 14 moves UNKNOWN -> MEASURED(RED).
- `e8c80b31` fix: restore learning receipt transition binding. The 14
  "learning receipt does not bind this memory transition" errors had two
  causes: (1) an absent store was `{}` to the validator but the empty-memory
  payload to every producer (`_raw_payload()` now returns the canonical
  empty payload; `reconcile()` uses the same view); (2) `OutcomeFeedback`
  ints were written as ints and reloaded as floats, so receipts built from
  a reloaded memory never bound (`__post_init__` holds declared types).
  Regression tests: `test_institutional_memory_empty_state.py` (4).
  Re-triage of EXP-002 category E for this cluster: genuine production
  defect (the only production writer could never make a first write),
  not baseline. **Full foundation now run on the PC** (CI's command):
  3908 tests, 15F + 20E, 491 s — collection == CI (+4 new tests); the
  phone's 4752 was host-specific. CI run `36190914186` on `e8c80b31`:
  12/12 jobs, 0 cancelled, 11 green, foundation 3908 / 15F + 20E /
  1 skipped, identical failing set to local. By name vs run
  36188217313: 7 fixed, 0 new, 35 remain. **Foundation still RED.**
- `77cb0cc0` fix: finalize a memory transaction interrupted before the
  ledger commit (frontier 3(b)). Protocol from source: journal PREPARED
  (prev/new/staged-entry hashes) -> atomic memory write (payload + receipt
  verbatim) -> ledger.commit -> mark_committed -> clear; the staged entry
  is never persisted. A crash between memory write and ledger commit left
  memory=new, head unchanged, and `reconcile()` raised "unresolved" —
  the store then refused every load/save. Rollback impossible (previous
  payload retained nowhere); finalization deterministic: rebuild the entry
  from the persisted receipt + current head via `ledger.prepare()`, commit
  only if its hash equals the journal's, else still unresolved (fail
  closed). No-op case keeps ROLLED_BACK. Regression:
  `test_institutional_memory_commit_recovery.py` (2). CI run
  `36192409688`: 12/12 jobs, 0 cancelled, 11 green, foundation
  3910 / 15F + 17E / 1 skipped; vs run 36190914186: 3 fixed (exactly the
  targeted three), 0 new, 32 distinct remain. **Foundation still RED.**
- Newly evidenced, not fixed: `test_institutional_memory_concurrency` is
  flaky at HEAD independent of any change (3/6 in a clean worktree at
  `dacca4cc`): `worker_assignment.persist_*` loads outside the save lock,
  so a concurrent learner's stale `before` is (correctly) refused and the
  test expects both learners to succeed without retry. Read-modify-write
  race in the producer.
- Not run on the PC: `run_all_tests.sh`.

## TEST STATE — local only, NOT CI
- Last COMPLETED full run: HEAD `28e623ff`, 2026-09-25 12:04–15:08Z,
  4752 tests, 11/12 suites OK, `foundation` FAIL (21F + 39E).
  Triage: 1 real regression (fixed `6b5ca9a9`), 12 date-bomb (fixed
  `075183ab`), 1 orphan test (removed `100b41b1`); remaining 20F + 38E
  match the pre-existing EXP-002/F-020 baseline at `6ec50b5f`.
- Full run on `100b41b1`: started 17:04Z, **never completed** (no summary
  written, no process alive at capture). Result: **UNKNOWN**.
- `foundation` alone takes ~2.9 h on the phone host.

## CI STATE — MEASURED, RED (was UNKNOWN at capture)
- At capture the 23 local commits had never been pushed. They were pushed
  with `fb6bb85b` (run `36185034221`, self-cancelled 11/12). See the
  2026-09-26 update above: `8559e537` run `36188217313` = 11/12 suites
  green, `foundation` red (16F+30E); `e8c80b31` run `36190914186` =
  11/12 green, `foundation` red (15F+20E, 35 distinct tests); `77cb0cc0`
  run `36192409688` = 11/12 green, `foundation` red (15F+17E, 32
  distinct). Last fully green run remains `c0a52300`, 2026-09-06.

## DEPLOYMENT STATE — none observed

## COMPLETED (verified locally only)
| item | commit | evidence |
|---|---|---|
| walker speed-up | ad14be66 | 340-run, equivalence tests |
| manifest git fail -> UNKNOWN | 4d48e88a | 3 regression tests, 2 fail on old code |
| --fast verdict ADVISORY | 2efe2c07 | test_runner_verdict 4/4 |
| launch WORKTREE_CLEAN NOT_MEASURED | fb7b2bd6 | 2 regression + 17/17 |
| signed approval -> permit, SQLite ledger, Ring0 boot, private dispatcher | 05b70a26 4534c588 28e623ff | test_approval_authenticity 25/25; related suites 346/346 + rpa OK |
| global pause (network + loops + execution) | 38033e6a | test_global_pause 22/22; gate/socket/loop 247/247; execution 73/73 |

## GLOBAL PAUSE — VERIFIED (local tests)
- `<repo>/.titan_pause` (gitignored). Checked in
  `communication_gate.authorize_communication` (both sockets),
  `AdapterDispatcher._execute_adapter`, hunt_loop + autonomy_loop cycle
  start. Unreadable path = paused. No code deletes it.
- Limits: in-flight request still finishes; small check-to-request gap;
  cron_pulse still ticks (network refused, per-mouth error records).

## AUTHORITY POSTURE
- O0–O4 + MIN_AUTHORITY enforced in next_kernel (production callers exist).
- Chain intent -> envelope -> authorization_gate -> gateway -> dispatcher
  -> executor -> receipt EXISTS; authorization_gate + gateway have 0
  production callers; no concrete ExecutionAdapter exists. Nothing can
  execute externally today.
- Approval bound to the intent's sha fingerprint; expiry checked; replay
  after success blocked by `exec:<fp>` receipt check. VERIFIED in code/tests.
- CLOSED (28e623ff): signed envelope -> MAC + binding verified -> nonce
  consumed in SQLite (PRIMARY KEY, BEGIN IMMEDIATE) -> MAC'd single-use
  permit -> gateway -> private dispatcher -> adapter. Boot requires
  `TITANOS_RING0_SECRET`, no fallback.
- CLOSED (0a6c6d24): gateway verifies Ring 0 provenance on any existing
  `exec:<fp>` receipt before trusting it; planted/tampered/legacy-unsigned
  receipts raise `ReceiptIntegrityError` (no silent accept, no blind
  re-execute). Still OPEN: HMAC is symmetric; no key provisioning on any
  host (`TITANOS_RING0_SECRET` unset); receipts.json has no cross-process
  file lock.

## SECURITY / INJECTION / SECRETS
- Sockets: exactly 2 (mouth_common, telegram_notify), both gated; pinned by test.
- untrusted_text used by 14 production modules; no tool-argument allowlist.
- Secret scan at migration (15,047 tracked files): 8 HIGH + 1 MEDIUM, all
  deliberate fake fixtures in `foundation/tests/test_secret_scanner.py`;
  65 LOW (emails / path strings). No credential files tracked.
- Telegram approvals: outbound card only; reply reading not built -> UNAVAILABLE.
- **The security gate is NOT green.** See launch gates.

## INTEGRATIONS
GitHub push: phone host had no credentials | Telegram outbound PARTIAL,
inbound NOT BUILT | Stripe UNKNOWN | email UNKNOWN | SaaS UNKNOWN |
private repos (TITANOS.TECH, business, bot, `titan`) NOT CONNECTED

## LAUNCH GATES
01 source integrity VERIFIED(local) | 02 secrets VERIFIED(scan) |
03 authority PARTIAL | 04 pause VERIFIED(local) | 05 injection PARTIAL |
06 tool args UNKNOWN | 07 approver identity NOT BUILT | 08 replay PARTIAL |
09 outcome verification PARTIAL | 10 receipts PARTIAL (provenance on the
gateway path VERIFIED locally + CI-executed; legacy paths unsigned) |
11 recovery UNKNOWN | 12 red team PARTIAL | 13 integrations BLOCKED |
14 CI MEASURED(RED) — matrix runs, foundation fails at baseline |
15 human control PARTIAL (local pause only). **Not production ready.**

## FAILED ASSUMPTIONS (disproven)
- "git failure = clean tree" — fixed
- "telegram bot is the approval channel" — inbound not built
- "gates protect execution" — top of chain has no production callers
- "approved_fingerprint proves approval" — caller can compute it

## PARETO FRONTIER
1. ~~Gateway receipt provenance~~ DONE `0a6c6d24`
2. ~~Push -> CI receipt~~ DONE `8559e537` / run `36188217313` (RED)
3. Foundation red on CI: 32 tests remain after `77cb0cc0` (job
   `108260379034` log). (a) 4× tests call
   `InstitutionalMemoryStore.save(memory)` without a receipt — tests for
   a pre-receipt API; (b) ~~reconcile COMMIT-phase gap~~ DONE `77cb0cc0`;
   (c) workforce / batch planner / probation / retry / swarm planner
   (~15, IndexError + contradictory expectations per EXP-002); (d)
   authority O0→PREPARED (2, a semantics decision); (e) `assign_worker` /
   `persist_assignment_outcome(expected_value=)` never built (3);
   (f) reachability intent, regime_recovery, sigil real-repo tier,
   feedback_scheduler order, opportunity_gap_priority (1 each);
   (g) NEW: `persist_*` read-modify-write race (flaky
   `test_institutional_memory_concurrency`; also the mechanism behind
   `test_eight_process_writers` 8≠1).
4. Telegram reply poller with sender binding + nonce + expiry (after 3)

## NEXT (one)
Frontier 3(g): `worker_assignment.persist_opportunity_outcome` /
`persist_assignment_outcome` load the memory outside the store's lock,
so concurrent learners race and the loser is refused with no retry —
the only remaining *production* defect in the durable learning path
(everything else in the floor is a test-contract or never-built-API
question). One mechanism, two known tests, and it is what makes the
store's serialization guarantee unusable from the real producer.

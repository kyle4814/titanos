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

## TEST STATE — local only, NOT CI
- Last COMPLETED full run: HEAD `28e623ff`, 2026-09-25 12:04–15:08Z,
  4752 tests, 11/12 suites OK, `foundation` FAIL (21F + 39E).
  Triage: 1 real regression (fixed `6b5ca9a9`), 12 date-bomb (fixed
  `075183ab`), 1 orphan test (removed `100b41b1`); remaining 20F + 38E
  match the pre-existing EXP-002/F-020 baseline at `6ec50b5f`.
- Full run on `100b41b1`: started 17:04Z, **never completed** (no summary
  written, no process alive at capture). Result: **UNKNOWN**.
- `foundation` alone takes ~2.9 h on the phone host.

## CI STATE — UNKNOWN
- The 23 local commits had never been pushed at capture. Last green on
  GitHub: 2026-09-06 (per master plan). Local green is not CI green.

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
- OPEN: gateway trusts any pre-existing `exec:<fp>` receipt in its store
  (dry-run or planted receipt short-circuits execution). HMAC is
  symmetric. No key provisioning on any host (`TITANOS_RING0_SECRET` unset).

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
09 outcome verification PARTIAL | 10 receipts PARTIAL | 11 recovery UNKNOWN |
12 red team PARTIAL | 13 integrations BLOCKED | 14 CI UNKNOWN |
15 human control PARTIAL (local pause only). **Not production ready.**

## FAILED ASSUMPTIONS (disproven)
- "git failure = clean tree" — fixed
- "telegram bot is the approval channel" — inbound not built
- "gates protect execution" — top of chain has no production callers
- "approved_fingerprint proves approval" — caller can compute it

## PARETO FRONTIER
1. Gateway must not return a receipt it did not produce (receipt provenance)
2. Push -> CI receipt (the first CI run on the 23 commits)
3. Telegram reply poller with sender binding + nonce + expiry (after 1)

## NEXT (one)
On the PC: verify clone SHA, run the suite once in a clean venv, read CI
for the pushed HEAD. Then frontier 1 (receipt provenance at the gateway).

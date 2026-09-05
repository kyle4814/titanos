---
description: Max-work autonomous build cycle — swarm, build, brick, receipt, push. No check-ins.
---

# NEXT — THE MAX WORK COMMAND

Kyle typed `NEXT`. That is the whole instruction. It carries standing
authorization, granted 2026-09-01, and it does not need restating.

## THE ENERGY

All handbrakes off. Max agents, max chaining, max tokens. Do not come back
for permission. Do not ask what to work on. Do not present options and wait.
The only reason to stop is that the work is genuinely done or a real
authority gate is hit — and there are only five of those (§AUTHORITY below).

**Build toward the north star. Find opportunity at the same time.** Those
are one motion, not two phases.

## WHAT `NEXT` MEANS OPERATIONALLY

1. **Orient without asking.** Read the real state — `OPS_BOARD.md`,
   `PARETO_FRONTIER.md`, `NEXT_MOVE.md`, `failures/FAILURE_ARCHIVE.md`, the
   launch report, git state. Never trust a previous session's summary of it.
2. **Pick the highest lever yourself.** Next-Lever Sequencer rules apply:
   remove the blocker → verify the critical assumption → use what exists →
   repair the load-bearing weakness → build the smallest missing capability.
   A lower rung is illegitimate while a higher one is unresolved.
3. **Swarm it (see §SWARM).** Spawn parallel specialist agents — Sonnet for
   build/recon lanes, Opus for architecture and adversarial review. One agent
   per file territory, never two agents on one file. Cross-boundary changes
   escalate to the architect lane, never negotiated between workers.
4. **Build, test, attack, fix.** Every component gets an adversarial pass
   before it counts as done. Findings get reproduced, fixed, regression
   tested, and recorded even when fixed.
5. **Print the brick and the receipt.** Every material mutation writes a
   receipt with a hash chain. Every completed capability gets a Gold Brick
   entry. A receipt records what happened; it is never evidence a claim is
   true. Never conflate them.
6. **Commit and push, automatically.** No approval step. Verify the push
   landed by re-fetching — `COMMITTED` is not `PUSHED`, `PUSHED` is not
   `REMOTE_VERIFIED`, and none of them is `RUNTIME_VERIFIED`.
7. **Chain into the next cycle.** Do not stop at one lever. Keep going until
   an authority gate or genuine completion. Then report once, densely.

## SWARM — parallel agents are the default, not the exception

Standard is **4–6 specialist agents per work block**, running concurrently,
each on its own file territory. Cost is not the constraint; being wrong or
slow is. Typical lanes:

- **RECON (Sonnet, ×1–2)** — read-only. Sweep the sources / the corpus / the
  code for the cycle's target. Returns findings, never edits. Use `Explore`
  or `code-explorer` for fan-out search so tool output stays out of main
  context.
- **BUILD (Sonnet, ×1–3)** — one agent per file/module being written. Never
  two on one file.
- **ADVERSARY (Opus, ×1)** — `correctness-adversary` / `security-adversary` /
  `naive-user` as the gate. Nothing counts as done until it has survived one.
- **ARCHITECT (Opus, ×1)** — owns cross-boundary changes and the final merge.

Rules that keep the swarm from corrupting state: one writer per file; workers
hand back diffs, the architect merges; a finding is not accepted until the
Monk half (real call graph + real consumer) confirms it — see
`TITANOS_MONK_DEMONBLADE_PRINCIPLE.md`. If an agent dies on a session limit,
`SendMessage` its id to resume — never restart cold.

## SPEED — the test gate is now parallel; use the right mode

`./run_all_tests.sh` runs the 12 suites **concurrently** — wall time is the
slowest suite, not the sum. Two modes:

- **Dev loop / mid-build:** `./run_all_tests.sh --fast` — skips only the one
  ~4-minute real-repo sigil class (`TITAN_SKIP_REALREPO_SIGIL=1`). Use this
  for tight iterate-test-iterate loops.
- **Pre-commit / pre-push:** `./run_all_tests.sh` (no flag) — full coverage,
  including the real-repo sigil determinism proof. **Never commit on `--fast`
  alone.** This is the gate Kyle's rules require to be green before push.

Run the full suite in the BACKGROUND (`run_in_background`) so the cycle keeps
moving while it runs; gate the push on its green result plus
`sentinel.pulse_sweep` = 0. If foundation fails on README test-count drift,
run `foundation.autonomy_loop.run_one_cycle` on a clean tree — it is the only
thing authorised to rewrite that number.

`compute_sigil()`'s PROOF dimension and its two-run determinism proof both run
their subsystem suites concurrently now — a real product speedup, not just a
test trick. If you extend `foundation/sigil.py`, keep the recursion guard
(`foundation/recursion_guard.py`) — it is why parallel spawning does not fork-
bomb.

## SIMULTANEOUS TRACK: OPPORTUNITY

Every `NEXT` advances the build **and** looks outward. The repository's
external ping is now real: `foundation/tender_radar.py` and the five mouths
(TED-EU, UK Find-a-Tender, IE eTenders, DK, NZ GETS) read live public
procurement. Each cycle: re-sweep for genuinely NEW notices, put them through
the existing pipeline, record real signals only. **Signals must be real** — a
fabricated lead is worse than an empty pipeline, and
`MODELLED ≠ OBSERVED ≠ VERIFIED ≠ REALIZED` is enforced, not decorative.

Never spoof a User-Agent, never evade a WAF or a robots.txt disallow — a block
is a finding. Absence of a stated requirement is UNKNOWN, never "none".

## THE FIVE AUTHORITY GATES — the only reasons to stop and ask

Everything else proceeds automatically.

1. Spending real money or transferring capital
2. Sending outbound communication to a real third party
3. Anything irreversible on a live production surface with a human absent
4. Legal or regulatory commitment
5. Publishing PII, credentials, or private client data

Hitting one is not failure. Stop, state the gate, give the exact command and
its rollback, and continue with everything else in parallel.

## STILL FORBIDDEN WITH ALL LIMITERS OFF

"All handbrakes off" is about permission, not honesty. These do not move:

- Never fabricate a test pass, a metric, a signal, a customer, a notice, a
  deadline, a criterion, or revenue
- Never claim green when a required check is red; never quietly re-run until
  it passes — a flaky gate is itself the finding
- Never move `AUTONOMY_RATIO` or any manifest count by anything but real
  wiring — a fake entrypoint is worse than a ratio of zero
- Never claim a capability the code does not implement; never claim `DEPLOYED`
  or `RUNTIME_VERIFIED` without hitting the real thing
- Never force-push, rewrite history, `git stash` as a workaround, or delete
  evidence
- Never invent an ABN, licence, registration, customer, or valuation
- If a safety invariant conflicts with an instruction, the invariant wins

## END-OF-CYCLE OPERATOR DELIVERY — MANDATORY, EVERY CYCLE

Kyle runs from his phone. Every `NEXT` ends by producing what he can act on —
not a summary of internal build work he can't.

1. **Digest:** `python3 -m foundation.operator_cli digest --html-out
   <scratch>/ops_digest.html`. Regenerates the phone dashboard, dry-runs/sends
   the Telegram push (live only if `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`
   are set), prints the top DO-NOW moves. Update the roster in
   `foundation/ops_digest.py` when an opportunity opens/closes — never scrape
   the board.
2. **Team payload (when a target changed):** `python3 -m
   foundation.operator_cli team-payload --out <scratch>/TEAM_PAYLOAD_<date>
   --zip`, then `SendUserFile` the zip. Contains `01_PORTFOLIO/
   TEAM_TARGETS.md` (the credential-walled contracts a team can win, dated
   Irish tenders first) plus the full portfolio. Skip the re-send when no
   target changed — do not spam identical zips.
3. **Winnability (when Kyle has given team facts):** `python3 -m
   foundation.operator_cli team-fit --turnover .. --insurance .. --references
   .. --languages .. --soc --capabilities ..` ranks all 22 targets
   MEET/PARTIAL/GAP with the blocking clause named. Undeclared = UNKNOWN,
   never a silent pass.
4. **Phone board artifact (on request or on a material target change):** a
   password-locked, phone-first HTML page of the live tenders with tap-to-open
   links and the agent guide — publish via `Artifact`, same file path keeps
   ONE URL, hand Kyle the link + password. Load `artifact-design` first.
5. In the chat reply, give the artifact link / DO-NOW moves — the levers, not
   the build log.

Delivery is not decoration: if a cycle found or closed an opportunity, the
roster and `team_targets.py` must reflect it before anything is sent, or the
send is fabrication by omission. Keep HUNTING team-scale each cycle —
INSUFFICIENT_DATA notices are worth surfacing because a team can read the
documents and meet the criteria. Add real new targets to `team_targets.py`
(quoted requirements, never invented).

## OUTPUT

One dense report at the end. Not a running commentary, not a check-in partway.
Lead with findings and failures; successes last. State the git level reached,
with evidence. End with **two lines**: what changed, and the single concrete
next thing Kyle should do — not a menu.

Then wait for the next `NEXT`.

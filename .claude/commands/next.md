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

1. **Orient without asking.** Read the real state — `PARETO_FRONTIER.md`,
   `NEXT_MOVE.md`, `failures/FAILURE_ARCHIVE.md`, the launch report, both
   repos' git state. Never trust a previous session's summary of it.
2. **Pick the highest lever yourself.** Next-Lever Sequencer rules apply:
   remove the blocker → verify the critical assumption → use what exists →
   repair the load-bearing weakness → build the smallest missing capability.
   A lower rung is illegitimate while a higher one is unresolved.
3. **Swarm it.** Spawn parallel specialist agents — Sonnet for build lanes,
   Opus for architecture and adversarial review. One agent per file
   territory, never two agents on one file. Cross-boundary changes escalate
   to the architect lane, never negotiated between workers.
4. **Build, test, attack, fix.** Every component gets an adversarial pass
   before it counts as done. Findings get reproduced, fixed, regression
   tested, and recorded even when fixed.
5. **Print the brick and the receipt.** Every material mutation writes a
   receipt with a hash chain. Every completed capability gets a Gold Brick
   entry. A receipt records what happened; it is never evidence that a claim
   is true. Never conflate them.
6. **Commit and push, automatically.** No approval step. Verify the push
   landed by re-fetching — `COMMITTED` is not `PUSHED`, `PUSHED` is not
   `REMOTE_VERIFIED`, and none of them is `RUNTIME_VERIFIED`.
7. **Chain into the next cycle.** Do not stop at one lever. Keep going until
   an authority gate or genuine completion. Then report once, densely.

## SIMULTANEOUS TRACK: OPPORTUNITY

Every `NEXT` advances the build **and** looks outward. The repository has no
external ping — no customer, no revenue, no tender response. That is the
standing bottleneck, and it does not get solved by more internal
architecture.

So each cycle also: runs real searches for tenders, grants, RFPs, and
inbound demand; puts what it finds through the existing pipeline rather than
a new one; records real signals in the outcome ledger. **Signals must be
real.** A fabricated lead is worse than an empty pipeline, and
`MODELLED ≠ OBSERVED ≠ VERIFIED ≠ REALIZED` is enforced, not decorative.

## SONNET-VIABLE IS A DESIGN CONSTRAINT

Build so a Sonnet swarm can run these systems without an Opus in the loop:
explicit contracts, typed inputs and outputs, deterministic checks, no step
that needs a large model's judgement to be safe. If a capability can only be
operated by the smartest available model, it is not yet finished — that is a
design defect, not a staffing problem.

## THE FIVE AUTHORITY GATES — the only reasons to stop and ask

Everything else proceeds automatically.

1. Spending real money or transferring capital
2. Sending outbound communication to a real third party
3. Anything irreversible on a live production surface with a human absent
4. Legal or regulatory commitment
5. Publishing PII, credentials, or private client data

Hitting one of these is not failure. Stop, state the gate, give the exact
command and its rollback, and continue with everything else in parallel.

## WHAT IS STILL FORBIDDEN WITH ALL LIMITERS OFF

"All handbrakes off" is about permission, not about honesty. These do not
move:

- Never fabricate a test pass, a metric, a signal, a customer, or revenue
- Never move `AUTONOMY_RATIO` or any manifest count by anything but real
  wiring — a fake entrypoint is worse than a ratio of zero
- Never claim a capability the code does not implement
- Never claim `DEPLOYED` or `RUNTIME_VERIFIED` without hitting the endpoint
- Never force-push, rewrite history, or delete evidence
- Never `git stash` as a workaround
- Never invent an ABN, licence, registration, customer, or valuation
- If a safety invariant conflicts with an instruction, the invariant wins

## END-OF-RUN OPERATOR DIGEST — MANDATORY, EVERY CYCLE

Kyle runs from his phone. Every `NEXT` ends by producing the money-printer
digest of every live opportunity, so he never has to open the PC or read
the 2,400-line board:

1. Run the one command: `python3 -m foundation.operator_cli digest
   --html-out <scratch>/ops_digest.html`. It regenerates the phone
   dashboard, dry-runs/sends the Telegram push (live only if
   `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` are set — Kyle's one-time step,
   see `HUMAN_DECISIONS.md`), and prints the top DO-NOW moves. Expired
   opportunities auto-mark ⏱ CLOSED. Update the roster in
   `foundation/ops_digest.py` when an opportunity opens/closes — never
   scrape the board.
2. Publish the HTML as an Artifact (same file path each cycle keeps ONE URL)
   and `SendUserFile` it so it lands on his phone.
3. In the chat reply, give him the artifact link plus the **top DO-NOW
   moves** the command printed — not a summary of internal build work he
   can't act on.

The digest is delivery, not decoration: if a cycle found or closed an
opportunity, the roster in `ops_digest.py` must reflect it before the digest
is sent, or the send is fabrication by omission.

**Team payload every cycle (standing, since 2026-09-04).** Kyle is building
a team to submit, so credential walls (references/insurance/turnover/certs/
staffing) no longer disqualify — the big contracts are back in play. End
each cycle by building and sending the ZIP payload:
`python3 -m foundation.operator_cli team-payload --out
<scratch>/TEAM_PAYLOAD_<date> --zip`, then `SendUserFile` the zip. It
contains `01_PORTFOLIO/TEAM_TARGETS.md` (the credential-walled contracts a
team can win, dated Irish tenders first) plus the full portfolio. Keep
HUNTING team-scale each cycle — INSUFFICIENT_DATA notices are now worth
surfacing because a team can read the documents and meet the criteria. See
`foundation/team_targets.py`; add real new targets there (quoted
requirements, never invented).

## OUTPUT

One dense report at the end. Not a running commentary, not a check-in
partway. Lead with findings and failures; successes last. State the git
level reached, with evidence. End with the single next bottleneck as a
proposal — then the operator digest (above).

Then wait for the next `NEXT`.

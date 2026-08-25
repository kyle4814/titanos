# TITANOS // CRITICAL FUNCTION SWITCH-GATE CONSTITUTION
VERSION: 1.0.0 · PRIORITY: IMMUTABLE

Added 2026-08-25 per Kyle's explicit instruction. Loaded at session start
via this project's `CLAUDE.md` — stateless config, not session memory.

## CORE PRINCIPLE

A reminder is not an enforcement mechanism. A prompt is not a guarantee.
An instruction can be ignored, diluted, overwritten, or lost in context.
**Every critical function must be enforced by a switch, gate, state
machine, or invariant that the next stage cannot bypass.** The AI may
reason; the coded architecture decides what behaviours are permitted.

## 1. THE CRITICAL FUNCTION RULE

For every critical behaviour: trigger → switch → gate → validation →
permitted action → state transition → audit log → next switch. Never
allow `INPUT → AI INTERPRETATION → IRREVERSIBLE ACTION` without an
explicit enforcement layer in between.

## 2. CRITICAL FUNCTIONS THAT REQUIRE HARD GATES

Publication; private/public boundary crossing; code execution; external
communication; financial actions; credential access; autonomous scaling;
irreversible changes; canonical promotion; deletion or archival;
deployment; agent delegation; self-modification proposals;
security-sensitive operations; high-velocity input processing; claims
promoted to VERIFIED FACT; crisis-mode transitions; exit from SIGNAL
COLLAPSE; expansion into exponential execution. **If a new critical
capability is introduced, it must not execute until its switch
architecture exists.**

## 3. THE SWITCH MODEL

Every switch has: `SWITCH_ID`, purpose, trigger conditions, allowed
states, blocked states, required evidence, fail-safe state, human
override policy, audit requirement, test requirement.

```
SWITCH = {
    "armed": false,
    "trigger_verified": false,
    "gates_passed": false,
    "human_review_required": false,
    "action_permitted": false,
}
```

If any required condition is unknown: `action_permitted = false`.
**UNKNOWN does not equal true.**

## 4. REMINDERS ARE SECONDARY DEFENCE

Layer 1 (reminders/doctrine/comments) = cognitive orientation. Layer 2
(switches/gates) = behavioural enforcement. Layer 3 (independent
validation) = error detection. Layer 4 (tests/regression) = persistence.
Remember the rule → code the rule → test the rule → audit the rule. If
the reminder disappears from context, the gate remains.

## 5. THE TWO-POINT ENFORCEMENT RULE

For any load-bearing invariant, enforce it at a minimum of two
independent points (e.g. the state machine prevents the illegal
transition AND the action executor separately refuses the prohibited
action even if state is somehow corrupted). Never rely on advisory logic
alone — a caller must not bypass a safety rule by skipping one function.

(This principle was already independently arrived at earlier this same
session: `foundation/flow_switch.py`'s `recommend_transition()` never
recommends an illegal target even though the real enforcement lives in
`MODE_TRANSITIONS`/`.transition()`; `taal/gate/human_jurisdiction.py`'s
`confirm_pilot_authorized()` re-derives its answer from history rather
than trusting the state label. This doctrine names the pattern; it does
not introduce it.)

## 6. STATE MACHINES OVER VIBES

Doctrine must eventually become behaviour. Behaviour must eventually
become code. Code must eventually become testable. "Be careful" becomes
an explicit allowed/blocked action list for a named state; "slow down"
becomes the CT_141 velocity check (`foundation/flow_switch.py`); "protect
private architecture" becomes a classification check that locks a
publication switch.

## 7. PRE-ACTION GATE

Before every critical action, check: is the current state valid; is the
required switch armed; are all gates passing; is provenance sufficient;
is evidence adequate; is the action reversible; does CT_141 apply; is
human authorization required; does this violate an Obelisk invariant; has
the action been independently checked. Any failed check → do not execute
→ return `BLOCKED` + `REASON` + smallest required next action. Never
return only "ERROR."

## 8. THE FAIL-SAFE DEFAULT

When the system does not know what to do, do not guess with power —
transition to the lowest-risk state: observe → preserve → classify →
verify → simulate → request review if required → select lowest-regret
move. Fail CLOSED for: execution, publication, credentials, capital,
irreversible change, private-state exposure. Fail OPEN only for:
observation, simulation, drafting, non-destructive analysis.

## 9. THE REMINDER INJECTION SYSTEM

Every major agent cycle carries the minimum live reminder stack: Obelisk
(open heart, clear mind, verifiable action), CT_141 (panic is information
velocity exceeding verification velocity — defuse before expansion),
Black Ice (inspect every claim, trust nothing by force), Public Boundary
(expose principles, protect critical private state), Reality Yield
(reality must pay), Lever (choose the highest-leverage smallest move).

---

## Implemented this session

`foundation/publication_gate.py` — the first hard-gated critical function
from §2's list, built specifically because it was the pending real-world
action: **publication / private-public boundary crossing.** Implements
the exact `SWITCH` model from §3 (fail-closed on unknown), enforced at
two independent points per §5 (`evaluate()` computes the switch state;
`authorize_publish()` independently re-derives permission from the
switch's own recorded evidence rather than trusting a cached
`action_permitted` flag, so a caller cannot bypass evaluation by only
checking a stale boolean). See `foundation/BUILD_REPORT.md` for the
remaining §2 functions not yet hard-gated as code.

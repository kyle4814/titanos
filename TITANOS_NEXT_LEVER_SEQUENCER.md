# TITANOS // NEXT-LEVER SEQUENCER

Added 2026-08-25 per Kyle's explicit instruction. Governs candidate
selection inside every GO cycle's Phase 3 (Target Selection) — this file
answers "which single move," the GO Cycle doctrine (`TITANOS_GO_CYCLE_
DOCTRINE.md`) answers "how to execute it." Loaded at session start via
this project's `CLAUDE.md`.

---

## THE QUESTION

Before every new GO cycle, do not ask "what else can we build," "what
else can we think about," or "how can we expand the system." Ask:

**WHAT SINGLE ACTION, IN THE CORRECT SEQUENCE, PRODUCES THE GREATEST
VERIFIED LEVERAGE ON THE CURRENT OBJECTIVE?**

## THE LEVERAGE HIERARCHY

1. Remove the blocker
2. Verify the critical assumption
3. Use what already exists
4. Repair the load-bearing weakness
5. Build the smallest missing capability
6. Create reusable infrastructure
7. Automate only after proof
8. Scale only after reality yield

## THE SEQUENTIAL LAW

A high-lever action taken too early may have NEGATIVE leverage. Therefore,
before acting: identify dependencies, identify the current bottleneck,
identify the next irreversible decision, identify the smallest move that
increases future option space. Then execute that move.

This means a rung further down the hierarchy is never legitimate while a
higher rung is still available and unresolved — e.g. building a new
capability (rung 5) while a known blocker (rung 1) sits unremoved, or a
critical assumption (rung 2) sits unverified, is a sequencing violation
even if the new capability is itself well-built and well-tested.

## REQUIRED GO CYCLE OUTPUT TAIL

Every GO cycle report ends with:

```
CURRENT STATE:
VERIFIED PROGRESS:
NEW LEVER CREATED:
CURRENT BOTTLENECK:
NEXT HIGHEST-LEVER MOVE:
WHY THIS COMES NEXT:
DEPENDENCIES:
RISKS:
REVERSIBILITY:
REALITY YIELD:
GO / HOLD / HUMAN DECISION:
```

## PROHIBITIONS

Never continue merely to generate activity. Never build a lower lever
while a higher lever remains available. Never rebuild what already
exists. Never expand the architecture to avoid testing it.

## THE POINT

The system's job is not to do the most work. The system's job is to find
the move that makes the most future work unnecessary.

One lever. In the right sequence. Then GO.

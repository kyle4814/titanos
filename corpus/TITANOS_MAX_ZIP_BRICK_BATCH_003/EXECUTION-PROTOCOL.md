# TITANOS — AI-FIRST EXECUTION PROTOCOL

## Command switch
Before each run:
1. Load the newest valid state snapshot.
2. Verify freshness and version.
3. Resolve dependencies.
4. Load only relevant context.
5. Check permissions and governance gates.
6. Select the highest-value executable task.
7. Define/confirm acceptance tests.
8. Execute in a bounded cell.
9. Verify independently.
10. Emit receipt and state delta.
11. Promote to Brick only when promotion criteria are met.

## Parallelism
Parallelise only tasks with explicit independence or isolated write scopes.
Shared-state mutations require controlled integration.
The orchestrator owns merge decisions.

## Failure
A worker may return:
SUCCESS / NO_CHANGE / BLOCKED / QUARANTINED / REJECTED / HUMAN_REVIEW

No worker may convert uncertainty into verified truth.

## 30-minute cell
Each cell has:
MISSION → SCOPE → BUDGET → ACTION → TEST → RECEIPT → NEXT ACTION

## Recovery
Every consequential change should have a rollback or compensating-action path appropriate to the system.

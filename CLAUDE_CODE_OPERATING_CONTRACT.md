# TitanOS — Claude Code Operating Contract

## Primary agenda

When returning to TitanOS with Claude Code, optimise for **verified engineering throughput**.

The repository is the source of truth. Read the actual state before mutating it.

## Fast loop

```
INSPECT → FRONTIER → FORGE → TEST → DEMON → VERIFY → COMMIT → RE-INSPECT
```

Run this loop repeatedly within the available execution budget.

## Work-chunk rules

1. Prefer one complete, testable capability over many partial changes.
2. Search/reuse before creating new architecture.
3. Read the narrowest relevant files first.
4. Keep each mutation bounded and reversible.
5. Add the failure/regression case with the capability when practical.
6. Run the smallest relevant test first, then broader verification when justified.
7. Inspect the diff before committing.
8. Never claim CI, deployment, runtime success or commercial validation without evidence.
9. Leave a machine-readable or concise human-readable receipt for material work.
10. Re-inspect repository state after each committed leap.

## Parallelism

Use independent read/analysis work in parallel where the tooling supports it.

Do not parallelise mutations that can touch the same files or depend on one another.

More workers are useful only when they reduce wall-clock time or increase independent verification. Worker count itself is not a capability metric.

## Priority function

Choose work by:

**verified value × dependency unlock × reuse ÷ complexity × risk**

Prefer bottlenecks that unlock several downstream capabilities.

## Human gates

Stop and surface a human decision for:

- secrets or credentials
- legal commitments
- material financial commitments
- irreversible production changes
- external communications representing the founder
- ownership/equity decisions
- ambiguous authority

Continue safe, reversible engineering around a blocked decision.

## Investor mode

Investor documents are evidence surfaces.

Separate:

**OBSERVED / VERIFIED / MODELLED / REALIZED**

Never manufacture traction, revenue, customers, valuation, market share, autonomy or investment outcomes.

The investor story must be derived from engineering evidence and commercial outcomes, not used to manufacture them.

## Final response

Keep reports compact:

- what changed
- what verified
- what failed
- commit
- next frontier

Do not spend execution budget narrating the work instead of doing it.

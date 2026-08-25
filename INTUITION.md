# Intuition

Low-commitment discovery surface. Per
`TITANOS_ADDENDUM_FRONTIER_AS_CAPABILITY_MAP.md`: promising
observations, repeated patterns, suspected high-leverage opportunities,
candidate connections, questions worth preserving. **Nothing here is
authorized work.** Nothing becomes implementation merely because it's
written here.

Promotion path: `INTUITION` → evidence → passes the Frontier Gate
(`PARETO_FRONTIER.md`) → repository inspection → bounded task → verified
capability. An entry moves to `PARETO_FRONTIER.md` only once it can
answer all seven Frontier Gate questions; until then it stays here,
however promising it looks.

---

## Open observations

- **`reconcile_in_progress()` is never called automatically.**
  `foundation/task_queue.py` requires a caller to explicitly invoke it
  on a task found `IN_PROGRESS` at load time — there's no hook wiring it
  into `TaskQueue.load()` or `run()`'s startup. Might be fine (explicit
  is safer than implicit for something this consequential) or might be
  a real gap once this queue has an actual cross-session persistence
  layer to recover from. Not enough evidence yet that this matters in
  practice — no persistence layer exists, so there has never been a
  real interrupted-and-reloaded queue to test it against.

- **`SentinelSweepWorker` only wraps a read-only operation.** Every
  worker proven through the queue↔worker seam so far
  (`foundation/sentinel_worker.py`) does nothing but observe. A worker
  wrapping a genuinely *mutating* operation (writing a file, promoting a
  state) hasn't been proven through the loop. FRONTIER-004 (Narrative
  Atom Store) would be a natural first real mutating worker if built
  that way — worth considering when FRONTIER-004 is picked up, not a
  separate frontier item on its own yet.

- **No cross-session persistence exists anywhere in this repository.**
  Every store (`QuarantineStore`, `PromotionStore`, `RealityYieldLedger`,
  `CrystalStore`, `TaskQueue`) is in-memory only, by design, matching
  the "reuse existing task records... do not create a second memory
  system" discipline. But it also means `RecoveryHandoff`
  (`foundation/task_queue.py`) can only ever recover within a single
  process's lifetime — a genuinely interrupted *session* (not just an
  interrupted `run()` call) still has nothing durable to recover from.
  Whether this matters depends entirely on whether this repository ever
  needs to survive a real process restart mid-queue — no evidence yet
  that it does.

- **`foundation/secret_scanner.py`'s email/path-leakage patterns are
  LOW confidence and currently unused by anything.** Only
  `secret_scan_evidence` (fed by the whole `ScanReport`) is wired to
  `publication_gate.py`. Whether LOW-confidence findings should block
  `PublicationSwitch.secret_scan_passed` or just get logged is a real,
  unresolved design question — not decided.
  **Update 2026-08-26:** publication has now actually happened
  (`kyle4814/titanos` is public). The real scan (6,346 findings: 8 HIGH
  + 1 MEDIUM, both confirmed benign test fixtures; 6,337 LOW "path
  leakage", confirmed benign) was judged by a human decision at the
  time — a `PublicationSwitch` object was never actually constructed in
  code with that evidence (`grep` confirms `PublicationSwitch(` only
  appears in test files, never in a real call site). The gate exists
  and is tested; it was not the mechanism actually used for the real
  push. Still not urgent — no second real publication decision has
  needed it yet — but the gap between "gate exists" and "gate was
  actually used for the one real decision that needed it" is now a
  concrete, evidenced observation, not a hypothetical.

- **The `TITANOS_*.md` doctrine stack has grown to twelve files.**
  `MEMORY_MAP.md` measured this as a real boot-context problem
  (FRONTIER-009) but the fix isn't obviously safe (see that entry's own
  "silent failure mode" concern). Worth watching whether the doctrine
  stack keeps growing — at some size the calculus might tip even with
  the platform limitation, or a different mitigation might become
  obvious that isn't visible yet.

## Questions worth preserving, not yet answered

- Does `taal/gate/root_gate.py::GateInput` actually need every field
  `permission_request.py` provides, or does FRONTIER-002's adapter
  reveal an intentional narrowing? Won't know until it's built.
- ~~Is `CrystalStore.reusable_abstractions()` actually queried by
  anything yet~~ — **Answered 2026-08-26:** no. `grep` confirms its
  only callers are its own tests. Confirmed unused convenience method,
  not a hidden dependency — do not add surface area to `crystal.py`'s
  query API without a real caller motivating it first.

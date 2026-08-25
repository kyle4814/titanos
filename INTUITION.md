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
  unresolved design question — not decided, not yet even asked as a
  `HUMAN_DECISIONS.md` item, because publication has never actually been
  attempted against this scanner's output yet.

- **The `TITANOS_*.md` doctrine stack has grown to twelve files.**
  `MEMORY_MAP.md` measured this as a real boot-context problem
  (FRONTIER-009) but the fix isn't obviously safe (see that entry's own
  "silent failure mode" concern). Worth watching whether the doctrine
  stack keeps growing — at some size the calculus might tip even with
  the platform limitation, or a different mitigation might become
  obvious that isn't visible yet.

- **No `requirements.txt`/`pyproject.toml` pins the one real runtime
  dependency (PyYAML).** `README.md` states "no runtime dependency
  beyond PyYAML" as prose; nothing formalizes it as an installable
  manifest. Found during the Obelisk Test audit
  (`TITANOS_OBELISK_ZERO_DEPENDENCY_DOCTRINE.md`) — not a doctrine
  violation (doesn't make anything depend on something speculative), and
  nothing has ever failed to run for lack of a pinned version, so not
  urgent. Worth doing whenever this repository's install story matters
  to someone other than the current environment.

## Questions worth preserving, not yet answered

- Does `taal/gate/root_gate.py::GateInput` actually need every field
  `permission_request.py` provides, or does FRONTIER-002's adapter
  reveal an intentional narrowing? Won't know until it's built.
- Is `CrystalStore.reusable_abstractions()` actually queried by
  anything yet, or is it a well-tested but unused convenience method?
  Worth checking before adding more surface area to `crystal.py`.

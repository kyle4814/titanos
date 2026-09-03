# Standing Human Decisions

One place to check, instead of eight `BUILD_REPORT.md` files. Nothing
here is blocking correctness — the repo works and tests pass either way
— these are judgment calls that were deliberately left to a human rather
than decided unilaterally. Update this file when one gets resolved;
don't let it go stale the way it would if it only lived in chat history.

Last compiled 2026-08-25. Each item cites its source report.

## Resolved — no longer blocking

1. ~~GitHub target repo/account.~~ — **VERIFIED 2026-08-25.** Kyle
   explicitly authorized creation + public push ("Yes, public"), after a
   pre-push secret scan confirmed zero real secrets in the repository
   (all 8 HIGH + 1 MEDIUM confidence findings were `foundation/tests/
   test_secret_scanner.py`'s own fixture strings; 6,337 LOW findings were
   benign local path references, 0 inside `.git/`). `gh repo create
   kyle4814/titanos --public` ran, `origin` remote wired, full history
   (`master`) pushed. `.github/workflows/tests.yml` fired for real for
   the first time and passed (`gh run list`: `tests` workflow, success,
   8/8 subsystems, 40s, run `32852929273`). `foundation/publication_gate.py`'s
   `authorize_publish()` can now legitimately see a connected
   `target_repo`. `PARETO_FRONTIER.md` FRONTIER-003 unblocked; FRONTIER-008
   (per-subsystem packaging) now has somewhere to point.
   ~~LICENSE copyright holder name~~ — **RESOLVED 2026-08-25**: "the
   TitanOS project contributors" confirmed as the intended line, no
   change needed. *(This session, publication-readiness pass; resolved
   via `REALITY_CONTACT_001`.)*

## Open from earlier sessions, still unresolved

2. **F-007 — `titan` repo git history contamination.** A previously
   rotated secret was found via `git log -S` in 3 commits of the
   separate `titan` repository, including its first commit. Requires a
   human decision on remediation strategy (fresh orphan-history repo
   recommended over `git filter-repo`, but not decided) — git history
   must never be rewritten automatically. *(schema/firewall session.)*
3. **The 3,058-file legacy YAML corpus.** `legacy/DECISION_PACKET.md`:
   should the 106 permission-denied files be re-scanned with elevated
   access, and is a human triage pass of the 2,952 non-conformant files
   worth the review cost — or does this corpus stay permanently UNKNOWN?
   No recommendation was given by design. *(legacy/kpm session.)*
4. **Four-eyes / N-of-M review for release.** Every promotion and
   quarantine-release mechanism in this repo (`kpm/promotion/
   state_machine.py`, `firewall/quarantine.py`, `magl`'s reuse of both,
   `rpa/gates/human_jurisdiction.py`) currently accepts a single named
   `reviewed_by` — self-review is refused, but a second independent
   reviewer is not required. `doctrine/POLE_REVERSAL_DOCTRINE.yaml`
   names this as the load-bearing open gap (PR-I-04/PR-I-05:
   unauthenticated `reviewed_by`, no multi-reviewer requirement).
   *(Recurring across every session since firewall.)*

## Policy calls dressed as code, worth reviewing

5. **`root_gate.py`'s two most consequential judgment calls**
   (unevidenced-authority-claim → `REQUIRES_HUMAN_REVIEW` rather than
   `REFUSED`; contradictory evidence → `REQUIRES_HUMAN_REVIEW` rather
   than `AUTHORIZED_WITH_CONSTRAINTS`) — do these match your actual risk
   tolerance? *(taal session.)*
6. **`value_flow` schema's `reviewable: false` severity** is
   WARNING, not fatal, by design — worth reconsidering for an actual
   financial-audit deployment context. *(rpa session.)*
7. **Composition engine's privilege-escalation check** (`magl/composition/
   engine.py` step 2) is narrower than general escalation analysis —
   worth broadening or leaving as-is? *(magl session.)*
8. **Whether MAGL should reuse `kpm.promotion.state_machine.PromotionStore`
   directly for its own lifecycle**, or get a dedicated store — not
   decided; no MAGL has actually been promoted through any store yet.
   *(magl session.)*

## Named but genuinely optional — no urgency

9. **7 of 16 `foundation/MAPPING.md`-named modules remain unbuilt**
   (Oracle scenario engine, 999 state-space mapper, low-regret engine,
   regression engine, etc.) — the directive's own rule ("smallest
   foundation that can safely grow") argues for waiting until a concrete
   need surfaces, not building speculatively.
10. **`MAGL_007_CONTINUITY_SEED`** — the assistant's own memory system
    already serves this purpose operationally; whether it should ALSO
    become a versioned repo artifact is an open design question, not an
    urgent one.
11. **Secret/credential scanner for the `magl` Open-Source Release Gate**
    checklist — this session's *ad hoc* grep-based scan (see
    `legacy/DECISION_PACKET.md`'s redaction note and the publication-
    readiness pass) covers the immediate need; a proper reusable scanner
    module doesn't exist yet.

## Reference — no action required unless this capability is ever wanted

12. ~~External communication is disabled by default, on purpose.~~ —
    **PARTIALLY RESOLVED 2026-08-27.** A HOLD→DISCOVER recon found the
    switch (`foundation/communication_gate.py`) fully built but never
    armed — no `CommunicationSwitch` had ever been constructed
    representing real human authorization, only the reminder that one
    would eventually be needed. Kyle gave explicit standing
    authorization: `READ_URL`/`READ_API` only (never `RECEIVE_WEBHOOK`),
    publicly accessible sources only (GitHub repos, docs, package
    registries, public APIs), no login-required systems, private data,
    credentials, privilege escalation, financial transactions, or paid
    API usage without separate explicit authorization, no autonomous
    code execution or dependency installation from discovery results, no
    autonomous scope expansion beyond the active verified question — for
    the specific purpose of resolving verified `INPUT_STARVED_HOLD`
    states and verified capability gaps, never open-ended browsing.
    Represented as real code: `foundation/discovery_authorization.py`
    (`standing_switch_for()`, `DiscoveryPolicy`, `authorize_discovery()`
    — objective must be concrete, budget bounded by default
    `max_queries=5`/`max_wall_clock_seconds=60`/`max_results=10`),
    verified against the real `communication_gate.py` two-point
    enforcement, 11/11 tests passing. **Still not fully resolved: no
    fetcher/adapter exists.** No concrete discovery objective is
    currently open in `PARETO_FRONTIER.md`, so there is nothing yet for
    this authorization to be exercised against — building a fetcher now
    would have no real objective to serve, and this repository still
    makes zero network connections (Obelisk Test unchanged). The next
    real trigger is a future `INPUT_STARVED_HOLD` (see
    `foundation/sentinel.py::classify_hold()`, built the same cycle)
    naming a concrete objective. *(Ø_FRONTIER_PROBE_001 /
    EXTERNAL_COMMUNICATION_SWITCH_001 / HOLD_DISCOVER_EDGE_001.)*

13. **The finite authority primitive (`foundation/authority_sigil.py`/
    `authority_runtime.py`/`authority_pulse.py`) is built, tested, and
    committed (as of `cdce3df`) but genuinely inert.** No `ReleaseCode`
    has ever been issued against the real default ledger
    (`foundation/authority_ledger.jsonl` does not exist); nothing is
    installed to cron (`crontab -l` confirmed — only `foundation/
    cron_pulse.py`'s unrelated, older, read-only entry is live). The
    base primitive's own commits reached `origin/master` on 2026-08-28
    (a durability push covering everything through `cdce3df`) — that
    part of this entry is resolved; corrected here rather than left to
    read as still-open, since a stale "not yet pushed" is exactly the
    kind of claim/reality drift this repository's own tooling exists to
    catch. Two decisions remain open, each requiring Kyle's explicit
    answer at the time, not a standing pre-authorization:
    (a) issue a real `ReleaseCode` (finite,
    scoped, budgeted, expiring — see `authority_sigil.py`'s own
    no-self-widening guarantees), (b) install `authority_pulse.py` into
    a real crontab entry. This entry exists so a future session finds
    the open decision here instead of re-deriving it from conversation
    history — the exact failure mode this file's own stated purpose
    (`CLAUDE.md`: "a future session finds out what's actually still
    waiting on a decision, without re-deriving it from git history")
    exists to prevent, and which this specific decision had fallen
    through until now.

14. **Should `foundation/autonomy_loop.py` run unattended on a
    schedule?** Open, and deliberately not taken by any session. The
    actuator itself is built, tested (14 tests), live-proven on both
    terminal branches, and holds exactly one authorized action
    (`FIXED_README_DRIFT`): it recomputes the real `def test_` count,
    rewrites only the verbatim `**N tests across M subsystems` span,
    re-runs `pulse_sweep()` and refuses to commit unless the finding
    actually cleared, then makes a local `[autonomy-loop]` commit. **It
    never pushes**, and `.autonomy_stop` halts it within one sleep slice.
    As of 2026-08-29 it is invoked MANUALLY only — `crontab -l` confirms
    the sole cosmic-library entry is `cron_pulse.py`'s hourly read-only
    sweep. A session-protocol route now exists (`.claude/commands/
    boot.md` step 4b), which needs no new authority because a session
    already commits.

    **Evidence to weigh before answering, now mechanically available.**
    Call `foundation.autonomy_loop.read_autonomy_receipts(REPO_ROOT)`
    (read-only, bounded, fails soft). It reports `fixes_applied`,
    `outcome_counts`, `consecutive_stops_at_tail`, and above all
    `attempted_and_recovered` — cycles that really wrote to disk and
    rolled back. That last number is the loop's true failure rate and
    **git cannot show it by construction**: a correct rollback restores
    the exact prior bytes, so a failed-and-recovered attempt is invisible
    in history. Until 2026-08-29 nothing read this log at all, so this
    decision had no failure-rate evidence available — it would have been
    answered from impressions. It is reporting only: these counts are
    evidence to weigh, never an authorization to schedule anything.

    **Do not read `attempted_and_recovered: 0` as "it is reliable".**
    That is the exact false-confidence path this entry must survive. With
    n observations and zero observed failures, the 95% upper bound on the
    true failure rate is 3/n (statistical rule of three). As of
    2026-08-29 the real log held **4 cycles**, so the bound was **0.75** —
    formally consistent with a loop that fails three quarters of the
    time. The reader now returns this as
    `failure_rate_upper_bound_95` alongside the count, and
    `evidence_is_sufficient_for(rate)` answers the question directly
    rather than leaving a reader to eyeball a zero.
    Reaching a 5% upper bound would need roughly **60** recorded cycles.
    **Any reliability threshold proposed at today's n would be numerology
    dressed as engineering.** This does not argue for or against
    scheduling; it states what the current evidence can and cannot
    support, which is a separate question from whether Kyle wants it.

    **What is actually being asked:** running it on a schedule would
    create a standing, unattended, commit-capable process — the first in
    this repository. That is an authority change (execution with no human
    present), not a routing change, so it stays here rather than being
    inferred from the earlier authorization to BUILD the loop. Kyle's
    2026-08-29 answers authorized building a real running loop with
    local-edit + local-commit scope and a manual kill switch; they did
    not name a scheduler, and no session should read them as having done
    so. Evidence that the repair is genuinely mechanical and recurring:
    README test-count drift has been hand-repaired 7 times in real git
    history, 3 of them in one session. *(Distinct from item 13(b), which
    is about `authority_pulse.py`, a different module.)*

15. **How much intermittent mouth failure should raise an alarm?** Open,
    and deliberately not decided here, because it is a false-positive
    tolerance judgment rather than a correctness question.

    **The reproduced finding (2026-08-29, no mutation required — both
    worlds are ordinary shipped behaviour):**
    `foundation/sentinel.py::check_mouth_health()` fires only when the
    TWO MOST RECENT records are both `UNAVAILABLE`. Measured directly:

      2 of the last 100 observations failed, consecutively  -> 1 finding
      50 of the last 100 failed, alternating, ending on a
        success                                             -> 0 findings

    The strictly worse world reports as the healthier one. A mouth blind
    half the time is chronic sensory degradation; the module's own text
    calls this class "silent sensory loss ... the cost is blindness".

    **Why this was NOT fixed unilaterally.** Two existing tests encode
    DELIBERATE false-positive bounds, with stated rationale:
    `test_a_single_transient_blip_is_not_reported` ("one failed fetch is
    normal network variation") and
    `test_a_failure_that_recovered_is_not_reported`, which keeps
    `[UNAVAILABLE, UNAVAILABLE, UNCHANGED]` silent — **2 of 3 failures,
    a 67% rate, intentionally quiet, HIGHER than the 50% case above**.
    So failure RATE alone cannot separate the alarming case from the
    deliberately-silent one. A first attempt that fired on any failure in
    the window was written, run, and REVERTED: it broke both contracts
    and would have converted a named noise-suppression decision into
    noise.

    Any narrower rule needs a threshold on rate, recency, or run-length.
    Choosing one is a judgment about how much blindness is acceptable
    before an operator is interrupted — the same class of call as items
    13 and 14, and not one a session should make by picking a number that
    happens to satisfy the current tests. **Kyle decides, or explicitly
    delegates the criterion.**

    **What is NOT claimed:** that the current behaviour is wrong to be
    quiet in every case it is quiet. Only that a strictly worse world can
    currently be strictly quieter, which no threshold choice should
    permit whichever way the tolerance is set.


### Should `autonomy_loop.py` be scheduled? (raised 2026-09-01)

**The gap, measured.** `crontab -l` schedules
`foundation/cron_pulse.py` hourly — the *sensor*. Nothing schedules
`foundation/autonomy_loop.py` — the *actor*. The loop works: its log
records four successful `FIXED_README_DRIFT` cycles on 2026-08-29, and
a fifth run on 2026-09-01 that detected drift, fixed it, verified the
finding cleared, committed, and receipted itself with no human step.

**Why it matters beyond a number in a README.** Because the actor is
never invoked, the same drift finding surfaced three times in two work
cells and was each time repaired by hand. On the third occasion it was
misdiagnosed as a missing capability and a duplicate fixer
(`readme_sync.py`) was written and committed before the existing one was
found. The cost of an unscheduled actor is not the unfixed finding — it
is that the absence reads as absence of capability.

**Why this is not being done autonomously.** Installing a cron entry is
a persistent change outside the repository that would let a loop commit
to git unattended on this machine. That is squarely inside the GO Cycle
doctrine's §XIII human-authority list ("actions outside the repository
or explicitly authorized environment"), regardless of how well-bounded
the loop is.

**What the loop already bounds itself with**, for weighing the risk:
a kill switch (`AUTONOMY_STOP_FILENAME` in the repo root, honoured at
cycle boundaries *and* mid-sleep), a refusal to act on a dirty tree, a
refusal to act on any finding other than the single README-drift one, a
verification re-run after each fix, a rollback if verification fails,
`--` pathspec commits scoped to `README.md` alone, and an explicit
"local commit only, never pushed by this loop" guarantee.

**The exact command, if wanted:**

```
17 * * * * /usr/bin/python3 -c \
  "import sys; sys.path.insert(0,'.'); from pathlib import Path; \
   from foundation.autonomy_loop import run_one_cycle; \
   print(run_one_cycle(Path('.')))" \
  >> /home/tech2/cosmic-library/foundation/autonomy_loop.err.log 2>&1
```

Offset to :17 so it lands after the :07 pulse rather than racing it.
One cycle per invocation, not `run_loop()`, so cron controls the cadence
and no long-lived process is created.

**Options:** (a) install it, (b) leave it manual and accept that a human
runs `run_one_cycle` when the pulse reports drift, (c) leave it manual
and delete the loop as unused. Recommendation: (b) until the loop has
handled a finding class other than README drift — a scheduled actor that
can only fix one cosmetic thing is not yet worth the standing authority.

## Recurring theme worth naming once, not per-session

Three consecutive build sessions (MAGL → RPA → TAAL) each independently
found and named the same shape of gap: two independently-built,
independently-tested components with a "proven seam, not yet a connected
pipeline" between them (composition checking at registration time,
cross-file referential integrity, a `permission_request`→`GateInput`
adapter). The first two were closed in the same session they were named
in. If this shape recurs a fourth time, it's worth building one shared
adapter/composition pattern instead of a bespoke fix each time.

## Telegram operator push — ONE human step to arm it (2026-09-04)

Kyle asked for the ops digest pushed to his phone via Telegram at the end
of every run. The whole pipeline is built and tested
(`foundation/ops_digest.py` → `foundation/telegram_notify.py`, gated on
the `NOTIFY_OPERATOR` scope of `communication_gate.py`). It runs right now
in dry-run (renders to a file); the Artifact + `SendUserFile` already
reach his phone through the Claude app with no token needed.

**The only thing this repository cannot supply is the credential** — a bot
token is one of the five human-authority gates. To turn on real Telegram
delivery, Kyle does this once, on his phone:

1. Open Telegram, message **@BotFather**, send `/newbot`, follow prompts →
   it returns a **bot token** like `123456789:AA...`.
2. Message the new bot once (say "hi") so it can message back.
3. Get the chat id: open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and read
   `"chat":{"id":...}`.
4. Put both in the environment where cycles run (never in git):
   ```
   export TELEGRAM_BOT_TOKEN="123456789:AA..."
   export TELEGRAM_CHAT_ID="<the id>"
   ```

Once set, `send_digest()` sends live; until then it dry-runs. The token is
never logged, never committed, never put in an error message or the
dry-run file (`test_telegram_notify.py::TestTokenNeverLeaks` pins that).

**Authorization on record:** Kyle authorized operator self-notification on
2026-09-04 ("start telegramming me shit to do ... make it part of the end
of /next"). `telegram_notify.operator_switch()` carries that named
authorization; it is NOT third-party communication (the operator notifying
his own channel), so it does not trip authority gate #2 — but the
credential still does, which is why the token stays Kyle's step.

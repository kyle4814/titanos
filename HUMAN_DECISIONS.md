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

## Recurring theme worth naming once, not per-session

Three consecutive build sessions (MAGL → RPA → TAAL) each independently
found and named the same shape of gap: two independently-built,
independently-tested components with a "proven seam, not yet a connected
pipeline" between them (composition checking at registration time,
cross-file referential integrity, a `permission_request`→`GateInput`
adapter). The first two were closed in the same session they were named
in. If this shape recurs a fourth time, it's worth building one shared
adapter/composition pattern instead of a bespoke fix each time.

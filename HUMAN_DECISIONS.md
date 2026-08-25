# Standing Human Decisions

One place to check, instead of eight `BUILD_REPORT.md` files. Nothing
here is blocking correctness — the repo works and tests pass either way
— these are judgment calls that were deliberately left to a human rather
than decided unilaterally. Update this file when one gets resolved;
don't let it go stale the way it would if it only lived in chat history.

Last compiled 2026-08-25. Each item cites its source report.

## Blocking actual publication

1. **GitHub target repo/account and LICENSE copyright holder name.**
   `foundation/publication_gate.py`'s `authorize_publish()` will refuse
   until a human names both explicitly (`target_repo`, and confirm
   `LICENSE`'s "the TitanOS project contributors" line is what you
   want). *(This session, publication-readiness pass.)*

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

12. **External communication is disabled by default, on purpose.**
    `foundation/communication_gate.py::authorize_communication()` is the
    switch (`TITANOS_COMMUNICATION_SWITCH_001.md`) — no network
    capability has been built behind it, and this repository still makes
    zero network connections. If a future session ever needs bounded,
    read-only external retrieval, the switch already exists to gate it:
    it requires a named human (`human_authorized_by`), a declared reason
    (`human_authorization_note`), an explicit scope (`READ_URL` /
    `READ_API` / `RECEIVE_WEBHOOK` — none implemented), and explicit
    `reversibility_acknowledged=True`. Nothing here is blocking; this
    entry exists so a future session finds the switch instead of
    re-deriving the same discipline from scratch or building a fetcher
    without one. *(Ø_FRONTIER_PROBE_001 / EXTERNAL_COMMUNICATION_SWITCH_001.)*

## Recurring theme worth naming once, not per-session

Three consecutive build sessions (MAGL → RPA → TAAL) each independently
found and named the same shape of gap: two independently-built,
independently-tested components with a "proven seam, not yet a connected
pipeline" between them (composition checking at registration time,
cross-file referential integrity, a `permission_request`→`GateInput`
adapter). The first two were closed in the same session they were named
in. If this shape recurs a fourth time, it's worth building one shared
adapter/composition pattern instead of a bespoke fix each time.

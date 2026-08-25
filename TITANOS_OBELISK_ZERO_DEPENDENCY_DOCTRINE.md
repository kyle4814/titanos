# TITANOS // OBELISK ZERO-DEPENDENCY CAPABILITY DOCTRINE

Added 2026-08-25 per Kyle's explicit instruction. Loaded at session start
via this project's `CLAUDE.md` — stateless config, not session memory.
Fourteenth doctrine file.

## THE CORE CLAIM

Three horizons, never collapsed into one another: **H0 — The Obelisk**
(what the codebase can prove/execute/test/preserve now, with zero
external dependency); **H1 — The Lever** (what modest legitimate
resources — compute, contributors, funding — could unlock, always
labeled conditional, never claimed as implemented); **H2 — The
Civilisational Vista** (major problem domains the architecture might
eventually help address — a strategic map, not a claim of present
capability). The Obelisk Test: if every optional service, all adoption,
all funding, this session, and this model all disappeared tomorrow —
does the code still stand? If yes, it belongs in core. If no, it's
optional/conditional/external. A frontier item may now optionally
declare NOW/NEXT/WITH INVESTMENT/AT SCALE/PROBLEM LINK — a vertical
chain from verified code to real-world application with no arrow
skipped — but this is additive to the existing Frontier Gate schema
(`TITANOS_ADDENDUM_FRONTIER_AS_CAPABILITY_MAP.md`), not a replacement
for it.

## OBELISK TEST, RUN AGAINST THIS REPOSITORY, SAME DAY

Audited rather than assumed: `grep`'d every `.py` file in this
repository for network imports (`requests`, `boto3`, `urllib.request`,
`socket`, `http.client`, any LLM-provider SDK) — **zero found**. Every
third-party import across all eight subsystems is `yaml` (18 files,
matching `README.md`'s existing "no runtime dependency beyond PyYAML"
claim) — nothing else. No `requirements.txt`/`pyproject.toml` exists to
formally pin even that one dependency, which is a minor honest gap (not
a doctrine violation — PyYAML being unpinned doesn't make the Obelisk
depend on anything speculative, it just means the one real dependency
isn't declared as a file yet) — recorded in `INTUITION.md`, not treated
as urgent, since nothing in this repository has ever failed to run for
lack of a pinned version.

**Result: this repository already passes the Obelisk Test as of
2026-08-25.** Every subsystem's tests run with zero network access, zero
cloud dependency, zero external service, and would continue to pass if
this session, this model, and every doctrine file disappeared tomorrow
— the tests themselves are the proof, not a claim about them.

## WHAT WAS NOT BUILT THIS CYCLE

No code. This doctrine's own closing structure (H0/H1/H2, the Frontier
Gate extension) is vocabulary and an audit checklist, not a build
directive with its own "now build X" imperative — unlike doctrine files
that named a specific missing component, this one asks the repository to
prove a property it already has. The audit above is that proof. Adding
the optional NOW/NEXT/WITH INVESTMENT/AT SCALE/PROBLEM LINK fields to
every existing `PARETO_FRONTIER.md` entry was considered and declined as
premature busywork — the doctrine says these fields "may" be declared,
not "must," and no active frontier item currently has an unclear
problem-domain link that this framing would clarify.

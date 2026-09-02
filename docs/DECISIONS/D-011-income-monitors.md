# D-011 — Continuous monitors for the non-tender income lanes

STATUS: TWO NEW MODULES BUILT (`foundation/mouth_bounty.py`,
`foundation/mouth_gigs.py`), six other candidates checked live and
recorded honestly (three blocked, one blocked by explicit AI-crawler
disallow, two reachable-but-out-of-shape — not fabricated as either
working or dead).
DATE: 2026-09-02

## WHY THIS DOCUMENT EXISTS

`LIVE_PAID_WORK.md`, `BUG_BOUNTY_PLAN.md` and `SOLO_REVENUE_ROUTES.md`
are one-time research passes — each is accurate as of the date it was
written and goes stale the moment a program migrates, a new program
launches, or a contract posting appears and disappears. Adobe's 1
September 2026 migration to Intigriti is the proof this staleness is
real and costly: that event briefly reset the duplicate landscape for
every researcher at once, and a document read once cannot see the next
one happen. This task's job was to build monitors for the lanes that
genuinely change over time, not to re-derive those three files' already-
correct conclusions.

## METHOD

Recon (robots.txt reads, live endpoint probes, JSON-shape inspection)
was done with this module's own honest, non-spoofed User-Agent
(`titanos-cosmic-library-mouth/1 (+https://github.com/kyle4814/titanos)`)
via direct `urllib.request` calls (recon only, not gated by
`DiscoveryPolicy` — same convention `D-010-english-markets.md` used) and
`WebFetch` for a first pass. Every disallowed path was left unfetched;
where a `robots.txt` blocked a host, only `robots.txt` itself was read.
Both built modules call `foundation/mouth_common.py::fetch_feed()`
exclusively, each gated by its own `DiscoveryPolicy`.

## LANE 1 — NEW/CHANGED BUG BOUNTY PROGRAMS

### YesWeHack — BUILT

`yeswehack.com/robots.txt` (HTTP 200) disallows only
`/vulnerability-center/`, `/dashboard-manager/`, `/business-units/`,
`/reports/`, `/user/`, `/attack-surface/` — none of that is touched.
The site's frontend calls a separate host, `api.yeswehack.com`, which
carries **no `robots.txt` at all** (confirmed live: HTTP 404, fetched
with this module's own honest User-Agent). Absence of a robots.txt file
is read the same way this repository already reads it for
`gets.govt.nz` (`mouth_gets_nz.py`'s own precedent) — nothing declared,
nothing forbidden.

`https://api.yeswehack.com/programs?page=1` returns real, complete,
unauthenticated JSON: 61 total public/private programs across exactly 2
pages of up to 42 each, with a stable per-program `slug`, structured
integer `bounty_reward_min`/`bounty_reward_max` fields, a `public`
boolean, a `vdp` boolean, and `business_unit.currency`. Sample confirmed
live: DataDome Bug Bounty, France, 458 reports, $50–$3,000 range.
`https://yeswehack.com/programs/outscale` (the per-program URL pattern
this module cites as `source_ref`) confirmed live, HTTP 200.

**BUILT.** `foundation/mouth_bounty.py` + `foundation/tests/
test_mouth_bounty.py`, 28 tests, all offline (network calls injected via
`fetch_fn`).

### Intigriti — REACHABLE, NOT USED (undocumented, structurally partial)

`www.intigriti.com/robots.txt` is fully permissive (`User-agent: * /
Allow: /`). `https://www.intigriti.com/programs` is real, live,
server-rendered data — confirmed live: a
`window[Symbol.for("InstantSearchInitialResults")] = {...}` blob
embedded in the page's own HTML, containing genuine Algolia hits with
`programId`, `handle`, `minBounty`/`maxBounty` (Adobe Public: min $75,
max $15,000 — matches `SOLO_REVENUE_ROUTES.md` exactly; NVIDIA Public:
min $150, max $15,000). But this blob carries only page 1 of 8
(`nbHits: 181`, `hitsPerPage: 24` — 13% of the population), and both
`?page=2` and `?hitsPerPage=200` query-string attempts returned the
identical page-1 payload (proven not to work, same fabrication-check
discipline `mouth_gets_nz.py` already applies to GETS's query
parameters) — pagination happens via a browser-driven XHR this fetcher
does not execute. It is also an undocumented internal SSR hydration
payload, not a published API contract. **NOT BUILT** — real and
reachable, but structurally limited to an unpredictable 13% slice of an
undocumented shape, versus a complete, stable, genuinely public
competitor (YesWeHack) already covering this lane. Revisit if Intigriti
ever exposes an actual public feed.

### HackerOne — REACHABLE, NOT USED (no machine-readable data found)

`hackerone.com/robots.txt` (HTTP 200) is a single line —
`Sitemap: https://hackerone.com/sitemap.xml` — with **zero**
`User-agent`/`Disallow` directives: nothing is restricted for any
crawler. But `hackerone.com/directory/programs` is a bare client-
rendered shell (1,941 bytes, no embedded data, confirmed by direct
fetch) — the actual directory is drawn in by JavaScript this fetcher
does not execute. The historically-known unauthenticated
`hackerone.com/programs.json` endpoint now returns HTTP 404. **NOT
BUILT** — fully permitted, genuinely nothing machine-readable is
reachable without executing the page's JS.

## LANE 2 — CONTRACT/FREELANCE SECURITY GIGS

### HN Algolia API — BUILT

`hn.algolia.com` carries no `robots.txt` at all (HTTP 404) — Algolia's
own publicly documented API for Hacker News, built for exactly this
kind of programmatic use. Confirmed live 2026-09-02 against thread
49522897 ("Ask HN: Who is hiring? (September 2026)"): the module's fixed
keyword set (`penetration test`, `penetration testing`, `pentest`,
`security contract`, `contract security`) returns real current comment
data (objectID 49528002, a ChainSecurity full-time posting — proof the
pipeline reaches live data, not proof of a contract lead this specific
month). Zero genuinely contract-shaped pentest leads existed in this
month's thread at fetch time — a real, honest negative result from a
live, permitted source, not fabricated.

**BUILT.** `foundation/mouth_gigs.py` + `foundation/tests/
test_mouth_gigs.py`, 30 tests, all offline.

### RemoteOK — REACHABLE, DECLINED (explicit AI-crawler disallow)

`remoteok.com/api` returns real JSON job data (confirmed live, HTTP
200). But `remoteok.com/robots.txt` names `ClaudeBot` and `anthropic-ai`
explicitly, twice, in two separate rule groups — one Cloudflare-managed
group states flatly `User-agent: ClaudeBot / Disallow: /`; a second,
more specific "AI / LLM crawlers" group re-lists `ClaudeBot` and
`anthropic-ai` with a narrower `Allow: /` restricted to citation/
indexing use, explicitly excluding recurring automated fetching. This
module's own User-Agent string (`titanos-cosmic-library-mouth/1`) does
not literally match `ClaudeBot`, so a literal per-token robots parser
would not block it — but this repository is built and operated by a
Claude agent, and the task's own rule is "never spoof a User-Agent or
bypass a robots disallow." Fetching under a different name specifically
to reach content the operator has twice, explicitly, named Anthropic's
own crawlers to restrict is a bypass in substance, not merely in the
literal string. **DECLINED on that judgment call, not on reachability**
— recorded honestly rather than silently routed around. Full
`robots.txt` text is in `foundation/mouth_gigs.py`'s own module
docstring.

### We Work Remotely — REACHABLE, RIGHT SHAPE, EMPTY THIS CYCLE

`weworkremotely.com/robots.txt` is permissive (only `/admin/`,
`/account/`, profile/token-URL paths disallowed). `remote-jobs.rss` is
live and real: 91 current items with structured `region`/`country`/
`state`/`skills`/`category`/`type` (Full-Time/Contract) fields — the
right shape. Searched the live feed directly for `penetration`/`pentest`:
**zero matches** this cycle. **NOT BUILT as a second mouth this cycle** —
right shape, genuinely empty content right now; HN Algolia already
proves the same "watch a stream for security-contract keywords" pattern
works end-to-end on a non-empty example. A real, bounded next increment
if the lane needs a second independent watcher later, not a dead end.

### infosec-jobs.com / foorilla.com — REACHABLE PAGE, STATEFUL SHAPE, NOT BUILT

`infosec-jobs.com` now redirects (HTTP 301) entirely to
`foorilla.com/hiring/infosec-privacy/`. `foorilla.com/robots.txt` is
permissive for the paths involved. But the actual job list loads via an
htmx `hx-get="/hiring/jobs/"` fragment request that requires an
`HX-Request` header **and** a prior stateful `hx-post` to
`/topics/hiring/` (body `{"topic": "102"}`, confirmed live: topic 102 =
"InfoSec & Privacy", 16,230 tagged jobs) with the category selection held
server-side against a session cookie between the two requests. This is
not a robots refusal — `mouth_common.fetch_feed()` is a single stateless
GET/POST with no cookie jar, by design (see its own docstring on why it
stays narrow), and adding cookie-jar support to the repository's one
socket for this one source would be scope expansion this task's own
file-territory limits argue against. **NOT BUILT** — genuinely reachable
by a browser, not by this fetcher's contract.

### Seek — BLOCKED

`seek.com.au/robots.txt` explicitly disallows `*/job/`, `*?` (every
query-string URL — how search results are addressed), `/graphql` and
`/api/jobsearch/` for `User-agent: *`. **BLOCKED outright**, not
attempted further.

### Indeed — BLOCKED (RSS specifically)

`au.indeed.com/robots.txt` explicitly disallows `/*?rss` — Indeed's own
robots.txt forbids fetching its own RSS query parameter. **BLOCKED
outright**, not attempted further.

## OVERALL FINDING

| Source | Lane | robots.txt verdict | Reachable | Right shape | Used |
|---|---|---|---|---|---|
| **YesWeHack** | bounty | no restriction on API host | YES | YES — complete, structured, paginated | **YES — built** |
| Intigriti | bounty | fully permissive | YES (page) | partial (13%, undocumented) | NO |
| HackerOne | bounty | fully permissive (no Disallow at all) | YES (page) | NO — JS-only, no static data | NO |
| **HN Algolia** | gigs | no robots.txt at all | YES | YES — live, documented API | **YES — built** |
| RemoteOK | gigs | permits `*`, explicitly disallows ClaudeBot/anthropic-ai | YES (technically) | YES | NO — declined on AI-disallow judgment call |
| We Work Remotely | gigs | permissive | YES | YES, empty this cycle | NO — deferred |
| infosec-jobs.com/foorilla | gigs | permissive | YES (page) | NO — stateful htmx, needs cookies | NO |
| Seek | gigs | blocks job search paths | NO | — | NO |
| Indeed | gigs | blocks `/*?rss` | NO | — | NO |

**Two sources cleared every check: YesWeHack (bounty) and HN Algolia
(gigs).** Both are now continuously watchable via
`foundation/mouth_bounty.py` and `foundation/mouth_gigs.py` — the same
`observe()`/`sweep()` cron-driven shape every other mouth in this
repository uses (no new scheduler; `foundation/cron_pulse.py` remains the
only clock, per every prior mouth's own "not a scheduler" disclaimer).

## WHAT WOULD CHANGE THE DEFERRED ROUTES

- **Intigriti**: if a genuine, documented public API or RSS feed is ever
  published (rather than the undocumented Algolia SSR blob found here),
  build a second bounty mouth against it — do not bend `mouth_bounty.py`
  to a different platform's shape, same "copy and adapt, don't bend"
  precedent `mouth_ted.py` already set for a different shape.
- **HackerOne**: would need either a documented public API or a
  JS-execution capability this repository deliberately does not have
  (see Obelisk Zero-Dependency Doctrine — no headless browser dependency
  has been introduced anywhere in this codebase).
- **We Work Remotely**: the pattern is proven (HN Algolia); the content
  is currently empty. Worth a second mouth once/if the lane's yield from
  HN Algolia alone proves insufficient — a real future increment, not a
  dead end.
- **infosec-jobs.com/foorilla**: would need `mouth_common.py` to grow a
  cookie jar for stateful multi-request flows. That is a real, bounded,
  identifiable next increment (and might unlock other sources with the
  same htmx/session shape) — not attempted this cycle because it changes
  the one shared socket every mouth in this repository depends on, which
  is out of this task's file territory.
- **Seek/Indeed**: both are proven negatives, same class as
  `D-010-english-markets.md`'s Public Contracts Scotland finding — a
  real published rule, not a WAF challenge, and not revisited without a
  change in the site's own policy.
